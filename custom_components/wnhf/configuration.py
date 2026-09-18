"""Safe, installation-owned registry configuration support for Red Queen."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

import yaml

from .registry import WNHFRegistryError, load_house


CONFIGURATION_API_VERSION = "1.0"
CONFIGURATOR_MANIFEST_FILE = "configurator.yaml"
CONFIGURATOR_MODE_MANAGED = "managed"
CONFIGURATOR_MODE_MANUAL = "manual"
CONFIGURATOR_MODE_UNINITIALIZED = "uninitialized"

REQUIRED_REGISTRY_FILES: dict[str, str] = {
    "rooms.yaml": "rooms",
    "lights.yaml": "lights",
    "covers.yaml": "covers",
    "openings.yaml": "openings",
}
OPTIONAL_REGISTRY_FILES: dict[str, str] = {
    "plants.yaml": "plants",
    "notification_targets.yaml": "notification_targets",
}

# Files eligible for controlled ownership transfer.
MANAGED_REGISTRY_FILES: tuple[str, ...] = tuple(
    sorted((*REQUIRED_REGISTRY_FILES, "plants.yaml"))
)

# Configurator-owned semantic object collections. These are deliberately limited
# to the house registry files that the managed commissioning flow owns.
_MANAGED_OBJECT_SPECS: dict[str, tuple[str, str]] = {
    "rooms": ("rooms.yaml", "rooms"),
    "lights": ("lights.yaml", "lights"),
    "covers": ("covers.yaml", "covers"),
    "openings": ("openings.yaml", "openings"),
    "plants": ("plants.yaml", "plants"),
}
_MANAGED_OBJECT_ACTION_NAMES: dict[str, str] = {
    "rooms": "room",
    "lights": "light",
    "covers": "cover",
    "openings": "opening",
    "plants": "plant",
}

_MANAGED_HEADER = (
    "# Managed by the Red Queen configurator.\n"
    "# Use the Red Queen configuration flow instead of editing this file manually.\n"
)
_MANAGED_OWNER = "red_queen_configurator"


class WNHFConfigurationError(Exception):
    """Raised when a safe configuration operation cannot be completed."""


@dataclass(frozen=True, slots=True)
class ConfigurationApplyResult:
    """Describe one successfully applied configuration transaction."""

    action: str
    changed_files: tuple[str, ...]
    backup_path: str | None
    validation: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable result."""
        return {
            "action": self.action,
            "changed_files": list(self.changed_files),
            "backup_path": self.backup_path,
            "validation": self.validation,
        }


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _timestamp(value: datetime | None = None) -> str:
    return (value or _utc_now()).strftime("%Y%m%dT%H%M%S_%fZ")


def _read_yaml_document(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as err:
        raise WNHFConfigurationError(f"Could not read {path}: {err}") from err

    if not isinstance(raw, dict):
        raise WNHFConfigurationError(
            f"Root element in {path} must be a dictionary"
        )
    return raw


def _render_yaml(document: dict[str, Any], *, managed: bool) -> str:
    rendered = yaml.safe_dump(
        document,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return f"{_MANAGED_HEADER}{rendered}" if managed else rendered


def _write_fsync(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def registry_bundle_sha256(registry_dir: Path, filenames: list[str]) -> str:
    digest = sha256()
    for filename in sorted(filenames):
        path = registry_dir / filename
        if not path.is_file():
            continue
        digest.update(filename.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
        digest.update(b"\0")
    return digest.hexdigest()


class RegistryConfigurationManager:
    """Inspect and safely update one installation-owned registry bundle."""

    def __init__(self, registry_dir: Path) -> None:
        self.registry_dir = registry_dir
        self.manifest_path = registry_dir / CONFIGURATOR_MANIFEST_FILE
        self.backup_root = registry_dir.parent / "configuration_backups"

    def snapshot(self) -> dict[str, Any]:
        """Return file, ownership and load-validation state without mutation."""
        generated_at = _utc_now()
        known_files = {**REQUIRED_REGISTRY_FILES, **OPTIONAL_REGISTRY_FILES}
        file_results: list[dict[str, Any]] = []

        for filename, root_key in known_files.items():
            path = self.registry_dir / filename
            item: dict[str, Any] = {
                "file": filename,
                "required": filename in REQUIRED_REGISTRY_FILES,
                "exists": path.is_file(),
                "root_key": root_key,
                "count": None,
                "sha256": None,
                "valid_yaml": None,
                "error": None,
            }
            if path.is_file():
                try:
                    source = path.read_bytes()
                    item["sha256"] = sha256(
                        source.replace(b"\r\n", b"\n")
                    ).hexdigest()
                    document = _read_yaml_document(path)
                    values = document.get(root_key)
                    item["valid_yaml"] = isinstance(values, list)
                    item["count"] = len(values) if isinstance(values, list) else None
                    if not isinstance(values, list):
                        item["error"] = (
                            f"Root key '{root_key}' must contain a list."
                        )
                except (OSError, WNHFConfigurationError) as err:
                    item["valid_yaml"] = False
                    item["error"] = str(err)
            file_results.append(item)

        manifest: dict[str, Any] = {}
        manifest_error: str | None = None
        if self.manifest_path.is_file():
            try:
                manifest = _read_yaml_document(self.manifest_path)
            except WNHFConfigurationError as err:
                manifest_error = str(err)

        any_registry_file = any(
            item["exists"] for item in file_results
        )
        manifest_managed_files = manifest.get("managed_files")
        valid_managed_manifest = (
            manifest.get("api_version") == CONFIGURATION_API_VERSION
            and manifest.get("mode") == CONFIGURATOR_MODE_MANAGED
            and manifest.get("owner") == _MANAGED_OWNER
            and isinstance(manifest_managed_files, list)
            and all(
                isinstance(filename, str)
                and filename in {*REQUIRED_REGISTRY_FILES, *OPTIONAL_REGISTRY_FILES}
                for filename in manifest_managed_files
            )
            and set(REQUIRED_REGISTRY_FILES).issubset(manifest_managed_files)
        )
        mode = manifest.get("mode")
        if not valid_managed_manifest:
            mode = (
                CONFIGURATOR_MODE_MANUAL
                if any_registry_file
                else CONFIGURATOR_MODE_UNINITIALIZED
            )

        missing_required = [
            filename
            for filename in REQUIRED_REGISTRY_FILES
            if not (self.registry_dir / filename).is_file()
        ]
        validation: dict[str, Any] = {
            "valid": False,
            "error": None,
            "warnings": [],
            "counts": None,
        }
        if missing_required:
            validation["error"] = (
                "Missing required registry files: "
                + ", ".join(missing_required)
            )
        else:
            try:
                house, warnings = load_house(self.registry_dir)
                validation.update(
                    {
                        "valid": True,
                        "warnings": list(warnings),
                        "counts": {
                            "rooms": len(house.rooms),
                            "lights": len(house.lights),
                            "covers": len(house.covers),
                            "openings": len(house.openings),
                            "plants": len(house.plants),
                        },
                    }
                )
            except (OSError, WNHFRegistryError) as err:
                validation["error"] = str(err)

        return {
            "api_version": CONFIGURATION_API_VERSION,
            "generated_at": generated_at.isoformat(),
            "registry_path": str(self.registry_dir),
            "mode": mode,
            "managed": mode == CONFIGURATOR_MODE_MANAGED,
            "write_enabled": mode in {
                CONFIGURATOR_MODE_MANAGED,
                CONFIGURATOR_MODE_UNINITIALIZED,
            },
            "manifest": manifest or None,
            "manifest_error": manifest_error or (
                None
                if not self.manifest_path.is_file() or valid_managed_manifest
                else "Configurator manifest is not a valid managed-ownership marker."
            ),
            "missing_required_files": missing_required,
            "files": file_results,
            "validation": validation,
        }

    def room_options(self) -> list[dict[str, str]]:
        """Return configured room IDs and names for flow selectors."""
        path = self.registry_dir / "rooms.yaml"
        if not path.is_file():
            return []
        document = _read_yaml_document(path)
        rooms = document.get("rooms")
        if not isinstance(rooms, list):
            raise WNHFConfigurationError("rooms.yaml has no valid rooms list")
        return [
            {"value": str(item["id"]), "label": str(item["name"])}
            for item in rooms
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and isinstance(item.get("name"), str)
        ]


    def _require_managed(self) -> None:
        """Reject every mutation unless Red Queen owns the registry bundle."""
        snapshot = self.snapshot()
        if not snapshot["managed"]:
            raise WNHFConfigurationError(
                "This registry is manually owned and remains read-only. "
                "Configurator writes are allowed only for a managed installation."
            )

    @staticmethod
    def _object_spec(object_type: str) -> tuple[str, str]:
        """Resolve one supported managed object collection."""
        try:
            return _MANAGED_OBJECT_SPECS[object_type]
        except KeyError as err:
            raise WNHFConfigurationError(
                f"Unsupported managed object type: {object_type}"
            ) from err

    def _object_document(
        self,
        object_type: str,
    ) -> tuple[str, str, dict[str, Any], list[Any]]:
        """Load one managed object collection after ownership validation."""
        self._require_managed()
        filename, root_key = self._object_spec(object_type)
        path = self.registry_dir / filename
        if not path.is_file():
            raise WNHFConfigurationError(
                f"Managed registry file does not exist: {filename}"
            )
        document = _read_yaml_document(path)
        entries = document.get(root_key)
        if not isinstance(entries, list):
            raise WNHFConfigurationError(
                f"{filename} has no valid '{root_key}' list."
            )
        return filename, root_key, document, entries

    def object_options(self, object_type: str) -> list[dict[str, str]]:
        """Return stable IDs and readable labels for maintenance selectors."""
        _filename, _root_key, _document, entries = self._object_document(
            object_type
        )
        options = [
            {
                "value": str(item["id"]),
                "label": f"{item.get('name') or item['id']} ({item['id']})",
            }
            for item in entries
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item.get("id")
        ]
        return sorted(
            options,
            key=lambda item: (item["label"].casefold(), item["value"]),
        )

    def get_object(self, object_type: str, object_id: str) -> dict[str, Any]:
        """Return one managed raw registry object without mutable state leakage."""
        _filename, _root_key, _document, entries = self._object_document(
            object_type
        )
        for item in entries:
            if isinstance(item, dict) and item.get("id") == object_id:
                return deepcopy(item)
        raise WNHFConfigurationError(
            f"Managed object not found: {object_type}/{object_id}"
        )

    def update_object(
        self,
        object_type: str,
        object_id: str,
        replacement: dict[str, Any],
    ) -> ConfigurationApplyResult:
        """Replace one managed object while its semantic identity stays stable."""
        filename, root_key, document, entries = self._object_document(
            object_type
        )
        if not isinstance(replacement, dict):
            raise WNHFConfigurationError(
                "Managed object replacement must be a dictionary."
            )
        if replacement.get("id") != object_id:
            raise WNHFConfigurationError(
                "A stable semantic object ID cannot be changed during maintenance."
            )

        index = next(
            (
                index
                for index, item in enumerate(entries)
                if isinstance(item, dict) and item.get("id") == object_id
            ),
            None,
        )
        if index is None:
            raise WNHFConfigurationError(
                f"Managed object not found: {object_type}/{object_id}"
            )

        candidate = deepcopy(document)
        candidate[root_key][index] = deepcopy(replacement)
        validation = self._validate_documents({filename: candidate})

        manifest = _read_yaml_document(self.manifest_path)
        manifest["updated_at"] = _utc_now().isoformat()
        changed = {
            filename: candidate,
            CONFIGURATOR_MANIFEST_FILE: manifest,
        }
        backup = self._write_transaction(changed, managed=True)
        action_name = _MANAGED_OBJECT_ACTION_NAMES[object_type]
        return ConfigurationApplyResult(
            action=f"update_{action_name}",
            changed_files=tuple(sorted(changed)),
            backup_path=backup,
            validation=validation,
        )

    def set_object_enabled(
        self,
        object_type: str,
        object_id: str,
        enabled: bool,
    ) -> ConfigurationApplyResult:
        """Enable or disable one managed semantic object transactionally."""
        replacement = self.get_object(object_type, object_id)
        replacement["enabled"] = bool(enabled)
        return self.update_object(object_type, object_id, replacement)

    def delete_object(
        self,
        object_type: str,
        object_id: str,
    ) -> ConfigurationApplyResult:
        """Delete one managed object only when the complete house remains valid."""
        filename, root_key, document, entries = self._object_document(
            object_type
        )
        index = next(
            (
                index
                for index, item in enumerate(entries)
                if isinstance(item, dict) and item.get("id") == object_id
            ),
            None,
        )
        if index is None:
            raise WNHFConfigurationError(
                f"Managed object not found: {object_type}/{object_id}"
            )

        if object_type == "rooms":
            if len(entries) <= 1:
                raise WNHFConfigurationError(
                    "At least one managed room must remain configured."
                )
            dependents = self._room_dependents(object_id)
            if dependents:
                raise WNHFConfigurationError(
                    "Room is still referenced and cannot be deleted: "
                    f"{object_id} <- {', '.join(dependents)}"
                )

        candidate = deepcopy(document)
        del candidate[root_key][index]
        validation = self._validate_documents({filename: candidate})

        manifest = _read_yaml_document(self.manifest_path)
        manifest["updated_at"] = _utc_now().isoformat()
        changed = {
            filename: candidate,
            CONFIGURATOR_MANIFEST_FILE: manifest,
        }
        backup = self._write_transaction(changed, managed=True)
        action_name = _MANAGED_OBJECT_ACTION_NAMES[object_type]
        return ConfigurationApplyResult(
            action=f"delete_{action_name}",
            changed_files=tuple(sorted(changed)),
            backup_path=backup,
            validation=validation,
        )

    def _room_dependents(self, room_id: str) -> list[str]:
        """Return semantic objects that still reference one managed room."""
        dependents: list[str] = []
        for object_type in ("lights", "covers", "openings", "plants"):
            filename, root_key = _MANAGED_OBJECT_SPECS[object_type]
            path = self.registry_dir / filename
            if not path.is_file():
                continue
            document = _read_yaml_document(path)
            entries = document.get(root_key)
            if not isinstance(entries, list):
                continue
            for item in entries:
                if not isinstance(item, dict) or item.get("room") != room_id:
                    continue
                object_id = str(item.get("id") or "<unknown>")
                dependents.append(f"{object_type}:{object_id}")
        return sorted(dependents)

    def create_managed_base(
        self,
        *,
        building_id: str,
        building_name: str,
        rooms: list[dict[str, Any]],
    ) -> ConfigurationApplyResult:
        """Create a complete empty managed bundle for a new installation."""
        snapshot = self.snapshot()
        if snapshot["mode"] != CONFIGURATOR_MODE_UNINITIALIZED:
            raise WNHFConfigurationError(
                "Registry files already exist. Existing manual registries are "
                "never overwritten by the configurator."
            )
        if not building_id or not building_id.startswith("house"):
            raise WNHFConfigurationError(
                "Building ID must be a stable semantic ID beginning with 'house'."
            )
        if not building_name.strip():
            raise WNHFConfigurationError("Building name must not be empty.")
        if not rooms:
            raise WNHFConfigurationError("Select at least one Home Assistant area.")

        room_ids = [item.get("id") for item in rooms]
        if any(not isinstance(value, str) or not value for value in room_ids):
            raise WNHFConfigurationError("Every generated room requires an ID.")
        if len(room_ids) != len(set(room_ids)):
            raise WNHFConfigurationError("Generated semantic room IDs are not unique.")

        documents: dict[str, dict[str, Any]] = {
            "rooms.yaml": {
                "building": {
                    "id": building_id,
                    "name": building_name.strip(),
                },
                "rooms": rooms,
            },
            "lights.yaml": {"lights": []},
            "covers.yaml": {"covers": []},
            "openings.yaml": {"openings": []},
            "plants.yaml": {"plants": []},
        }
        validation = self._validate_documents(documents)
        now = _utc_now()
        manifest = {
            "api_version": CONFIGURATION_API_VERSION,
            "mode": CONFIGURATOR_MODE_MANAGED,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "owner": _MANAGED_OWNER,
            "managed_files": sorted(documents),
        }
        changed = {**documents, CONFIGURATOR_MANIFEST_FILE: manifest}
        backup = self._write_transaction(changed, managed=True)
        return ConfigurationApplyResult(
            action="create_managed_base",
            changed_files=tuple(sorted(changed)),
            backup_path=backup,
            validation=validation,
        )

    def adopt_manual_registry(
        self,
        *,
        expected_source_sha256: str,
    ) -> ConfigurationApplyResult:
        snapshot = self.snapshot()
        if snapshot["mode"] != CONFIGURATOR_MODE_MANUAL:
            raise WNHFConfigurationError(
                "Manual registry adoption requires registry mode 'manual'."
            )
        if self.manifest_path.is_file():
            raise WNHFConfigurationError(
                "Manual registry has an existing configurator ownership marker; refusing to overwrite it."
            )
        if not snapshot["validation"].get("valid"):
            raise WNHFConfigurationError(
                "Manual registry is not valid and cannot be adopted."
            )
        if not expected_source_sha256:
            raise WNHFConfigurationError(
                "Expected manual source SHA-256 is required."
            )

        source_files = [
            filename
            for filename in MANAGED_REGISTRY_FILES
            if (self.registry_dir / filename).is_file()
        ]
        if registry_bundle_sha256(self.registry_dir, source_files) != expected_source_sha256:
            raise WNHFConfigurationError(
                "Manual registry source changed after preview; migration aborted."
            )

        documents: dict[str, dict[str, Any]] = {}
        for filename in MANAGED_REGISTRY_FILES:
            path = self.registry_dir / filename
            if path.is_file():
                documents[filename] = _read_yaml_document(path)
            elif filename == "plants.yaml":
                documents[filename] = {"plants": []}
            else:
                raise WNHFConfigurationError(
                    f"Manual registry is missing required file: {filename}"
                )

        validation = self._validate_documents(documents)

        if registry_bundle_sha256(self.registry_dir, source_files) != expected_source_sha256:
            raise WNHFConfigurationError(
                "Manual registry source changed after validation; migration aborted."
            )

        now = _utc_now()
        manifest = {
            "api_version": CONFIGURATION_API_VERSION,
            "mode": CONFIGURATOR_MODE_MANAGED,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "owner": _MANAGED_OWNER,
            "managed_files": list(MANAGED_REGISTRY_FILES),
            "migration": {
                "source_mode": CONFIGURATOR_MODE_MANUAL,
                "source_sha256": expected_source_sha256,
                "adopted_at": now.isoformat(),
            },
        }
        changed = {**documents, CONFIGURATOR_MANIFEST_FILE: manifest}
        backup = self._write_transaction(changed, managed=True)
        if backup is None:
            raise WNHFConfigurationError(
                "Manual registry migration did not produce the mandatory backup."
            )

        return ConfigurationApplyResult(
            action="adopt_manual_registry",
            changed_files=tuple(sorted(changed)),
            backup_path=backup,
            validation=validation,
        )

    def add_room(self, room: dict[str, Any]) -> ConfigurationApplyResult:
        """Append one room to a managed registry and validate the whole bundle."""
        return self._append_managed_entry(
            filename="rooms.yaml",
            root_key="rooms",
            entry=room,
            action="add_room",
        )

    def add_light(self, light: dict[str, Any]) -> ConfigurationApplyResult:
        """Append one light to a managed registry and validate the whole bundle."""
        return self._append_managed_entry(
            filename="lights.yaml",
            root_key="lights",
            entry=light,
            action="add_light",
        )

    def add_cover(self, cover: dict[str, Any]) -> ConfigurationApplyResult:
        """Append one venetian blind to a managed registry and validate the bundle."""
        return self._append_managed_entry(
            filename="covers.yaml",
            root_key="covers",
            entry=cover,
            action="add_cover",
        )

    def add_opening(self, opening: dict[str, Any]) -> ConfigurationApplyResult:
        """Append one opening to a managed registry and validate the bundle."""
        return self._append_managed_entry(
            filename="openings.yaml",
            root_key="openings",
            entry=opening,
            action="add_opening",
        )

    def add_plant(self, plant: dict[str, Any]) -> ConfigurationApplyResult:
        """Append one Plant Care object to a managed registry and validate the bundle."""
        return self._append_managed_entry(
            filename="plants.yaml",
            root_key="plants",
            entry=plant,
            action="add_plant",
        )

    def _append_managed_entry(
        self,
        *,
        filename: str,
        root_key: str,
        entry: dict[str, Any],
        action: str,
    ) -> ConfigurationApplyResult:
        snapshot = self.snapshot()
        if not snapshot["managed"]:
            raise WNHFConfigurationError(
                "This registry is manually owned and remains read-only. "
                "Configurator writes are allowed only for a managed installation."
            )

        object_id = entry.get("id")
        if not isinstance(object_id, str) or not object_id:
            raise WNHFConfigurationError("A stable semantic object ID is required.")

        path = self.registry_dir / filename
        document = _read_yaml_document(path)
        entries = document.get(root_key)
        if not isinstance(entries, list):
            raise WNHFConfigurationError(
                f"{filename} has no valid '{root_key}' list."
            )
        if any(
            isinstance(item, dict) and item.get("id") == object_id
            for item in entries
        ):
            raise WNHFConfigurationError(
                f"Semantic object ID already exists: {object_id}"
            )

        candidate = deepcopy(document)
        candidate[root_key].append(entry)
        validation = self._validate_documents({filename: candidate})

        manifest = _read_yaml_document(self.manifest_path)
        manifest["updated_at"] = _utc_now().isoformat()
        changed = {
            filename: candidate,
            CONFIGURATOR_MANIFEST_FILE: manifest,
        }
        backup = self._write_transaction(changed, managed=True)
        return ConfigurationApplyResult(
            action=action,
            changed_files=tuple(sorted(changed)),
            backup_path=backup,
            validation=validation,
        )

    def _validate_documents(
        self,
        overrides: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Validate candidate documents as one complete isolated bundle."""
        self.registry_dir.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(
            prefix=".red_queen_configuration_",
            dir=self.registry_dir.parent,
        ) as temporary:
            candidate_dir = Path(temporary)
            for filename in REQUIRED_REGISTRY_FILES:
                document = overrides.get(filename)
                if document is None:
                    source = self.registry_dir / filename
                    if not source.is_file():
                        raise WNHFConfigurationError(
                            f"Missing required candidate file: {filename}"
                        )
                    document = _read_yaml_document(source)
                _write_fsync(
                    candidate_dir / filename,
                    _render_yaml(document, managed=True),
                )

            plants = overrides.get("plants.yaml")
            if plants is None and (self.registry_dir / "plants.yaml").is_file():
                plants = _read_yaml_document(self.registry_dir / "plants.yaml")
            if plants is not None:
                _write_fsync(
                    candidate_dir / "plants.yaml",
                    _render_yaml(plants, managed=True),
                )

            try:
                house, warnings = load_house(candidate_dir)
            except WNHFRegistryError as err:
                raise WNHFConfigurationError(
                    f"Candidate registry validation failed: {err}"
                ) from err

        return {
            "valid": True,
            "warnings": list(warnings),
            "counts": {
                "rooms": len(house.rooms),
                "lights": len(house.lights),
                "covers": len(house.covers),
                "openings": len(house.openings),
                "plants": len(house.plants),
            },
        }

    def _write_transaction(
        self,
        documents: dict[str, dict[str, Any]],
        *,
        managed: bool,
    ) -> str | None:
        """Stage, back up and replace files with rollback on any failure."""
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        existing = [
            filename
            for filename in documents
            if (self.registry_dir / filename).is_file()
        ]
        backup_dir: Path | None = None
        try:
            if existing:
                backup_dir = self.backup_root / f"{_timestamp()}_{uuid4().hex[:8]}"
                backup_dir.mkdir(parents=True, exist_ok=False)
                for filename in existing:
                    shutil.copy2(
                        self.registry_dir / filename,
                        backup_dir / filename,
                    )
        except OSError as err:
            if backup_dir is not None:
                shutil.rmtree(backup_dir, ignore_errors=True)
            raise WNHFConfigurationError(
                f"Configuration backup failed; no files were changed: {err}"
            ) from err

        staged: dict[str, Path] = {}
        replaced: list[str] = []
        try:
            for filename, document in documents.items():
                stage = self.registry_dir / f".{filename}.{uuid4().hex}.tmp"
                _write_fsync(stage, _render_yaml(document, managed=managed))
                staged[filename] = stage

            replace_order = sorted(
                staged,
                key=lambda filename: (
                    filename == CONFIGURATOR_MANIFEST_FILE,
                    filename,
                ),
            )
            for filename in replace_order:
                os.replace(staged[filename], self.registry_dir / filename)
                replaced.append(filename)
        except OSError as err:
            for stage in staged.values():
                stage.unlink(missing_ok=True)
            for filename in replaced:
                target = self.registry_dir / filename
                backup = backup_dir / filename if backup_dir else None
                if backup is not None and backup.is_file():
                    shutil.copy2(backup, target)
                else:
                    target.unlink(missing_ok=True)
            raise WNHFConfigurationError(
                f"Configuration transaction failed and was rolled back: {err}"
            ) from err

        return str(backup_dir) if backup_dir is not None else None
