"""Read-only migration and repair preview for Red Queen RC14."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, floor_registry as fr

from .configuration import (
    CONFIGURATOR_MODE_MANAGED,
    CONFIGURATOR_MODE_MANUAL,
    REQUIRED_REGISTRY_FILES,
    RegistryConfigurationManager,
)
from .configuration_diagnostics import async_diagnose_configured_entities
from .registry import WNHFRegistryError, load_house


MIGRATION_REPAIR_PREVIEW_CONTRACT_VERSION = "1.0"

_OBJECT_FILES: dict[str, tuple[str, str, bool]] = {
    "rooms": ("rooms.yaml", "rooms", True),
    "lights": ("lights.yaml", "lights", True),
    "covers": ("covers.yaml", "covers", True),
    "openings": ("openings.yaml", "openings", True),
    "plants": ("plants.yaml", "plants", False),
}

_BLOCKING_ENTITY_STATUSES = {"missing", "disabled"}


@dataclass(frozen=True, slots=True)
class MigrationRepairFinding:
    """One read-only migration/repair preview finding."""

    severity: str
    code: str
    object_type: str | None = None
    object_id: str | None = None
    field: str | None = None
    value: str | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "field": self.field,
            "value": self.value,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class _RawPreview:
    source_sha256: str
    total_objects: int
    proposed_managed_files: tuple[str, ...]
    rooms: tuple[dict[str, Any], ...]
    findings: tuple[MigrationRepairFinding, ...]


@dataclass(frozen=True, slots=True)
class MigrationRepairPreview:
    """Complete read-only preview result."""

    contract_version: str
    mode: str
    source_valid: bool
    migration_candidate: bool
    migration_eligible: bool
    write_performed: bool
    source_sha256: str
    total_objects: int
    proposed_managed_files: tuple[str, ...]
    entity_references_total: int
    entity_references_ready: int
    findings: tuple[MigrationRepairFinding, ...]

    @property
    def blocker_count(self) -> int:
        return sum(item.severity == "blocker" for item in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(item.severity == "warning" for item in self.findings)

    @property
    def info_count(self) -> int:
        return sum(item.severity == "info" for item in self.findings)

    @property
    def repair_needed(self) -> bool:
        return bool(self.findings)

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "mode": self.mode,
            "source_valid": self.source_valid,
            "migration_candidate": self.migration_candidate,
            "migration_eligible": self.migration_eligible,
            "write_performed": self.write_performed,
            "source_sha256": self.source_sha256,
            "total_objects": self.total_objects,
            "proposed_managed_files": list(self.proposed_managed_files),
            "entity_references_total": self.entity_references_total,
            "entity_references_ready": self.entity_references_ready,
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "repair_needed": self.repair_needed,
            "findings": [item.as_dict() for item in self.findings],
        }


def _finding(
    severity: str,
    code: str,
    *,
    object_type: str | None = None,
    object_id: str | None = None,
    field: str | None = None,
    value: Any = None,
    detail: str | None = None,
) -> MigrationRepairFinding:
    return MigrationRepairFinding(
        severity=severity,
        code=code,
        object_type=object_type,
        object_id=object_id,
        field=field,
        value=None if value is None else str(value),
        detail=detail,
    )


def _bundle_sha256(registry_dir: Path, filenames: list[str]) -> str:
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


def _nested_entity_id(item: dict[str, Any], *path: str) -> str | None:
    node: Any = item
    for part in path:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node if isinstance(node, str) and node else None


def _has_feedback_entity(item: dict[str, Any]) -> bool:
    state = item.get("state")
    if isinstance(state, dict):
        entity_id = state.get("entity_id")
        if isinstance(entity_id, str) and entity_id:
            return True
    states = item.get("states")
    if isinstance(states, list):
        return any(
            isinstance(entry, dict)
            and isinstance(entry.get("entity_id"), str)
            and bool(entry.get("entity_id"))
            for entry in states
        )
    return False


def _check_required_text(findings, object_type, object_id, item, field) -> None:
    value = item.get(field)
    if not isinstance(value, str) or not value:
        findings.append(
            _finding(
                "blocker",
                "incomplete_object",
                object_type=object_type,
                object_id=object_id,
                field=field,
            )
        )


def _inspect_object_shape(object_type, object_id, item, findings) -> None:
    _check_required_text(findings, object_type, object_id, item, "name")

    if object_type == "rooms":
        _check_required_text(findings, object_type, object_id, item, "floor")
        return

    _check_required_text(findings, object_type, object_id, item, "room")

    if object_type == "lights":
        control_mode = item.get("control_mode", "monitor_only")
        if control_mode == "toggle":
            if _nested_entity_id(item, "command", "entity_id") is None:
                findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="command.entity_id"))
            if not _has_feedback_entity(item):
                findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="state/entity feedback"))
        elif control_mode in {"monitor_only", "reserved"}:
            findings.append(_finding("warning", "managed_maintenance_limited", object_type=object_type, object_id=object_id, field="control_mode", value=control_mode))
        else:
            findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="control_mode", value=control_mode))
        return

    if object_type == "covers":
        if item.get("type") != "venetian_blind":
            findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="type", value=item.get("type")))
        for field in ("open_entity_id", "close_entity_id"):
            if _nested_entity_id(item, "commands", field) is None:
                findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field=f"commands.{field}"))
        for field in ("open_entity_id", "closed_entity_id", "opening_entity_id", "closing_entity_id"):
            if _nested_entity_id(item, "feedback", field) is None:
                findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field=f"feedback.{field}"))
        capabilities = item.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="capabilities"))
        return

    if object_type == "openings":
        opening_type = item.get("type")
        if opening_type not in {"window", "door", "sliding_door", "garage_door"}:
            findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="type", value=opening_type))
            return
        if opening_type == "garage_door":
            for field in ("open_entity_id", "closed_entity_id"):
                if _nested_entity_id(item, "garage", "feedback", field) is None:
                    findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field=f"garage.feedback.{field}"))
            if _nested_entity_id(item, "garage", "command", "toggle_entity_id") is None:
                findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="garage.command.toggle_entity_id"))
        else:
            if _nested_entity_id(item, "state", "entity_id") is None:
                findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="state.entity_id"))
            state = item.get("state")
            open_states = state.get("open_states") if isinstance(state, dict) else None
            if not isinstance(open_states, list) or not open_states or not all(isinstance(value, str) and value for value in open_states):
                findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="state.open_states"))
        if opening_type == "door":
            lock = item.get("lock")
            if isinstance(lock, dict) and lock.get("enabled", True):
                for path in (("feedback", "entity_id"), ("commands", "lock_entity_id"), ("commands", "unlock_entity_id")):
                    if _nested_entity_id(item, "lock", *path) is None:
                        findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="lock." + ".".join(path)))
            opener = item.get("door_opener")
            if isinstance(opener, dict) and opener.get("enabled", True):
                if _nested_entity_id(item, "door_opener", "command", "entity_id") is None:
                    findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="door_opener.command.entity_id"))
        return

    if object_type == "plants":
        for field in ("species", "location"):
            _check_required_text(findings, object_type, object_id, item, field)
        interval = item.get("watering_interval_days")
        if not isinstance(interval, int) or isinstance(interval, bool) or interval < 1:
            findings.append(_finding("blocker", "incomplete_object", object_type=object_type, object_id=object_id, field="watering_interval_days", value=interval))


def _load_raw_preview(registry_dir: Path) -> _RawPreview:
    findings: list[MigrationRepairFinding] = []
    objects_by_type: dict[str, list[dict[str, Any]]] = {}
    present_files: list[str] = []

    for object_type, (filename, root_key, required) in _OBJECT_FILES.items():
        path = registry_dir / filename
        if not path.is_file():
            if required:
                findings.append(_finding("blocker", "missing_registry_file", object_type=object_type, value=filename))
            continue
        present_files.append(filename)
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as err:
            findings.append(_finding("blocker", "invalid_registry_document", object_type=object_type, value=filename, detail=str(err)))
            continue
        if not isinstance(raw, dict):
            findings.append(_finding("blocker", "invalid_registry_document", object_type=object_type, value=filename, detail="root element is not a dictionary"))
            continue
        entries = raw.get(root_key)
        if not isinstance(entries, list):
            findings.append(_finding("blocker", "invalid_root_list", object_type=object_type, field=root_key, value=filename))
            continue

        objects = []
        seen_local: set[str] = set()
        for index, item in enumerate(entries):
            if not isinstance(item, dict):
                findings.append(_finding("blocker", "invalid_object_entry", object_type=object_type, field=str(index), value=filename))
                continue
            object_id = item.get("id")
            if not isinstance(object_id, str) or not object_id:
                findings.append(_finding("blocker", "missing_object_id", object_type=object_type, field=str(index), value=filename))
                object_id = f"<{object_type}:{index}>"
            elif object_id in seen_local:
                findings.append(_finding("blocker", "duplicate_semantic_id", object_type=object_type, object_id=object_id))
            else:
                seen_local.add(object_id)
            objects.append(item)
            _inspect_object_shape(object_type, object_id, item, findings)
        objects_by_type[object_type] = objects

    room_ids = {
        str(item.get("id"))
        for item in objects_by_type.get("rooms", [])
        if isinstance(item.get("id"), str) and item.get("id")
    }

    seen_global: dict[str, str] = {}
    for object_type in ("rooms", "lights", "covers", "openings", "plants"):
        for item in objects_by_type.get(object_type, []):
            object_id = item.get("id")
            if not isinstance(object_id, str) or not object_id:
                continue
            previous = seen_global.get(object_id)
            if previous is not None and previous != object_type:
                findings.append(_finding("blocker", "duplicate_semantic_id", object_type=object_type, object_id=object_id, detail=f"also used by {previous}"))
            else:
                seen_global[object_id] = object_type
            if object_type != "rooms":
                room_id = item.get("room")
                if isinstance(room_id, str) and room_id and room_id not in room_ids:
                    findings.append(_finding("blocker", "orphan_room_reference", object_type=object_type, object_id=object_id, field="room", value=room_id))

    if all((registry_dir / filename).is_file() for filename in REQUIRED_REGISTRY_FILES):
        try:
            load_house(registry_dir)
        except (OSError, WNHFRegistryError) as err:
            findings.append(_finding("blocker", "registry_validation_error", detail=str(err)))

    proposed_managed_files = sorted({*REQUIRED_REGISTRY_FILES, "plants.yaml"})
    total_objects = sum(len(items) for items in objects_by_type.values())
    rooms = tuple(objects_by_type.get("rooms", []))
    source_hash = _bundle_sha256(registry_dir, present_files)

    findings.sort(
        key=lambda item: (
            {"blocker": 0, "warning": 1, "info": 2}.get(item.severity, 9),
            item.code,
            item.object_type or "",
            item.object_id or "",
            item.field or "",
            item.value or "",
        )
    )
    return _RawPreview(source_hash, total_objects, tuple(proposed_managed_files), rooms, tuple(findings))


def _ha_room_findings(hass: HomeAssistant, rooms: tuple[dict[str, Any], ...]) -> list[MigrationRepairFinding]:
    areas = ar.async_get(hass)
    floors = fr.async_get(hass)
    findings: list[MigrationRepairFinding] = []

    for item in rooms:
        object_id = str(item.get("id") or "<unknown>")
        area_id = item.get("ha_area_id")
        floor_id = item.get("ha_floor_id")
        area = None

        if area_id is not None:
            if not isinstance(area_id, str) or not area_id:
                findings.append(_finding("warning", "invalid_ha_area", object_type="rooms", object_id=object_id, field="ha_area_id", value=area_id))
            else:
                area = areas.async_get_area(area_id)
                if area is None:
                    findings.append(_finding("warning", "invalid_ha_area", object_type="rooms", object_id=object_id, field="ha_area_id", value=area_id))

        if floor_id is not None:
            if not isinstance(floor_id, str) or not floor_id:
                findings.append(_finding("warning", "invalid_ha_floor", object_type="rooms", object_id=object_id, field="ha_floor_id", value=floor_id))
            elif floors.async_get_floor(floor_id) is None:
                findings.append(_finding("warning", "invalid_ha_floor", object_type="rooms", object_id=object_id, field="ha_floor_id", value=floor_id))

        if area is not None and floor_id is not None and area.floor_id is not None and area.floor_id != floor_id:
            findings.append(_finding("warning", "area_floor_mismatch", object_type="rooms", object_id=object_id, field="ha_floor_id", value=f"{floor_id} != {area.floor_id}"))

    return findings


async def async_build_migration_repair_preview(hass: HomeAssistant, registry_dir: Path) -> MigrationRepairPreview:
    """Build a deterministic migration/repair preview without writing anything."""
    manager = RegistryConfigurationManager(registry_dir)
    snapshot = await hass.async_add_executor_job(manager.snapshot)
    raw = await hass.async_add_executor_job(_load_raw_preview, registry_dir)
    diagnostics = await async_diagnose_configured_entities(hass, registry_dir)

    findings = list(raw.findings)
    findings.extend(_ha_room_findings(hass, raw.rooms))

    for issue in diagnostics.issues:
        severity = "blocker" if issue.status in _BLOCKING_ENTITY_STATUSES else "warning"
        findings.append(
            _finding(
                severity,
                f"entity_{issue.status}",
                object_type=issue.object_type,
                object_id=issue.object_id,
                field=issue.role,
                value=issue.entity_id,
                detail=issue.platform,
            )
        )

    mode = str(snapshot["mode"])
    source_valid = bool(snapshot["validation"].get("valid"))
    if not source_valid and snapshot["validation"].get("error"):
        error = str(snapshot["validation"]["error"])
        if not any(item.code == "registry_validation_error" and item.detail == error for item in findings):
            findings.append(_finding("blocker", "registry_validation_error", detail=error))

    if mode == CONFIGURATOR_MODE_MANAGED:
        findings.append(_finding("info", "already_managed", detail="Migration is not required; preview acts as repair analysis."))

    findings.sort(
        key=lambda item: (
            {"blocker": 0, "warning": 1, "info": 2}.get(item.severity, 9),
            item.code,
            item.object_type or "",
            item.object_id or "",
            item.field or "",
            item.value or "",
        )
    )

    migration_candidate = mode == CONFIGURATOR_MODE_MANUAL
    blocker_count = sum(item.severity == "blocker" for item in findings)
    migration_eligible = migration_candidate and source_valid and blocker_count == 0

    return MigrationRepairPreview(
        contract_version=MIGRATION_REPAIR_PREVIEW_CONTRACT_VERSION,
        mode=mode,
        source_valid=source_valid,
        migration_candidate=migration_candidate,
        migration_eligible=migration_eligible,
        write_performed=False,
        source_sha256=raw.source_sha256,
        total_objects=raw.total_objects,
        proposed_managed_files=raw.proposed_managed_files,
        entity_references_total=diagnostics.total_references,
        entity_references_ready=diagnostics.ready_references,
        findings=tuple(findings),
    )
