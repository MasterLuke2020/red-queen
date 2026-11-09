#!/usr/bin/env python3
"""Stage Red Queen 1.2 domain cutover into a NEW directory only.

The original Home Assistant configuration is never changed. This is an
offline staging tool, NOT a production installation or rollback command.
It intentionally preserves all legacy entity IDs, unique IDs, object IDs,
wnhf/ data files and existing Home Assistant Store namespaces.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any
from uuid import uuid4

from rq12_domain_registry_transform import DomainMigrationError, plan_registry_transform

DOMAIN_RE = re.compile(r"(?m)^(?P<indent>)(?P<name>wnhf)(?P<suffix>\s*:)")
NEW_ROOT_RE = re.compile(r"(?m)^red_queen\s*:")

# Preserve the explicit HA logger level for the renamed integration.
LOGGER_KEY_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]+)(?P<quote>['\"]?)"
    r"custom_components\.wnhf(?P=quote)(?P<colon>[ \t]*:)"
)

SERVICE_RE = re.compile(
    r"(?m)^(?P<lead>\s*(?:-\s*)?(?:service|action)\s*:\s*)"
    r"(?P<quote>['\"]?)(?P<service>wnhf\.[a-z][a-z0-9_]*)"
    r"(?P=quote)(?P<tail>\s*(?:#.*)?)$"
)
SERVICE_NAME = re.compile(r"^wnhf\.([a-z][a-z0-9_]*)$")
CORE = ("core.config_entries", "core.entity_registry", "core.device_registry")
YAML_EXTENSIONS = {".yaml", ".yml"}
EXCLUDE_TOP = {"custom_components", "www", "deps", "tts", "media", "backups"}


class StageError(ValueError):
    """Unqualified or ambiguous migration input; refuse to stage."""


def _sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def _all_regular(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            raise StageError("Symlink encountered; refuse to copy linked configuration")
        if not path.is_file() and not path.is_dir():
            raise StageError("Non-regular configuration entry encountered")


def _json_doc(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise StageError("Invalid HA JSON storage: " + path.name) from exc
    if not isinstance(obj, dict):
        raise StageError("HA JSON storage must be object: " + path.name)
    return obj


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def rewrite_yaml_source(
    text: str, *, configuration_root: bool = False,
    allowed_services: set[str] | None = None,
) -> tuple[str, int, int]:
    """Preserve YAML formatting and entity IDs; touch only unambiguous service keys."""
    configs = 0
    if configuration_root:
        matches = list(DOMAIN_RE.finditer(text))
        if len(matches) > 1 or (matches and NEW_ROOT_RE.search(text)):
            raise StageError("Ambiguous simultaneous/multiple HA integration root keys")
        if matches:
            text = DOMAIN_RE.sub("red_queen\\g<suffix>", text)
            configs = 1

    if configuration_root:
        # A different logger namespace otherwise hides the HA start marker.
        text = LOGGER_KEY_RE.sub(
            lambda m: (m.group("indent") + m.group("quote") +
                       "custom_components.red_queen" + m.group("quote") +
                       m.group("colon")),
            text,
        )

    count = [0]
    def replace(match: re.Match[str]) -> str:
        name = match.group("service").split(".", 1)[1]
        if allowed_services is not None and name not in allowed_services:
            raise StageError("Unknown legacy service call: " + name)
        count[0] += 1
        return (match.group("lead") + match.group("quote") +
                "red_queen." + match.group("service").split(".", 1)[1] +
                match.group("quote") + match.group("tail"))
    text = SERVICE_RE.sub(replace, text)
    # Service templates must be audited, not guessed from a string replacement.
    if re.search(r"(?m)^\s*(?:-\s*)?(?:service|action|service_template|domain)\s*:"
                 r".*wnhf\.", text):
        raise StageError("Unresolved or templated legacy service in YAML")
    return text, configs, count[0]


def rewrite_lovelace_json(
    obj: dict[str, Any], *, allowed_services: set[str] | None = None,
) -> tuple[dict[str, Any], int]:
    """Rewrite only action/service property values, never dashboard entity IDs."""
    count = [0]
    def visit(value: Any) -> Any:
        if isinstance(value, list):
            return [visit(v) for v in value]
        if not isinstance(value, dict):
            return value
        new: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"service", "action", "perform_action"} and isinstance(item, str):
                match = SERVICE_NAME.fullmatch(item)
                if match:
                    if allowed_services is not None and match.group(1) not in allowed_services:
                        raise StageError("Unknown Lovelace legacy service call: " + match.group(1))
                    new[key] = "red_queen." + match.group(1)
                    count[0] += 1
                    continue
                if item.startswith("wnhf."):
                    raise StageError("Unrecognized/templated Lovelace service call")
            new[key] = visit(item)
        return new
    return visit(obj), count[0]


def _verify_identity(old: dict[str, dict], new: dict[str, dict]) -> None:
    old_entries = old[CORE[0]]["data"]["entries"]
    new_entries = new[CORE[0]]["data"]["entries"]
    old_ids = [e["entry_id"] for e in old_entries if e.get("domain") == "wnhf"]
    new_ids = [e["entry_id"] for e in new_entries if e.get("domain") == "red_queen"]
    if len(old_ids) != 1 or new_ids != old_ids:
        raise StageError("Config-entry identity not preserved")
    old_entities = old[CORE[1]]["data"]["entities"]
    new_entities = new[CORE[1]]["data"]["entities"]
    if len(old_entities) != len(new_entities):
        raise StageError("Entity count changed")
    for before, after in zip(old_entities, new_entities):
        for field in ("entity_id", "unique_id", "config_entry_id", "id"):
            if before.get(field) != after.get(field):
                raise StageError("Entity identity changed unexpectedly")
    old_devices = old[CORE[2]]["data"]["devices"]
    new_devices = new[CORE[2]]["data"]["devices"]
    if len(old_devices) != len(new_devices):
        raise StageError("Device count changed")
    for before, after in zip(old_devices, new_devices):
        if before.get("id") != after.get("id"):
            raise StageError("Device identity changed unexpectedly")


def _eligible_yaml(root: Path) -> list[Path]:
    paths = []
    for path in root.rglob("*"):
        if path.suffix.lower() not in YAML_EXTENSIONS or not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.parts[0] in EXCLUDE_TOP or ".storage" in rel.parts:
            continue
        paths.append(path)
    return sorted(paths)


def stage(source: Path, target: Path, package: Path) -> dict[str, Any]:
    """Create one isolated stage; never modify or replace an existing target."""
    src, dest, pkg = source.resolve(), target.absolute(), package.resolve()
    if not src.is_dir() or not (src / ".storage").is_dir():
        raise StageError("Source is not a complete Home Assistant config directory")
    if not pkg.is_dir() or not (pkg / "manifest.json").is_file():
        raise StageError("New Red Queen integration package not found")
    if _json_doc(pkg / "manifest.json").get("domain") != "red_queen":
        raise StageError("Wrong integration package domain")
    if dest == src or dest.is_relative_to(src) or src.is_relative_to(dest):
        raise StageError("Source and target must not be nested or equal")
    if dest.exists() or dest.is_symlink():
        raise StageError("Target already exists; never overwrite a stage")
    if not dest.parent.is_dir():
        raise StageError("Target parent directory must already exist")
    _all_regular(src)
    _all_regular(pkg)
    # Only migrate service calls that the new integration actually exposes.
    # Service descriptions are top-level YAML mappings in services.yaml.
    services_file = pkg / "services.yaml"
    if not services_file.is_file():
        raise StageError("Red Queen services.yaml missing")
    allowed_services = set(re.findall(
        r"(?m)^([a-z][a-z0-9_]*):\s*(?:\n|$)",
        services_file.read_text(encoding="utf-8"),
    ))
    if not allowed_services:
        raise StageError("No registered services found in new package")
    originals = {name: _json_doc(src / ".storage" / name) for name in CORE}
    transformed, counts = plan_registry_transform(*(originals[name] for name in CORE))
    if counts["already_migrated"]:
        raise StageError("Source is already migrated; refuse repeat staging")
    _verify_identity(originals, transformed)
    if (src / "custom_components/red_queen").exists():
        raise StageError("New integration directory already present in source")

    temporary = dest.parent / (".rq12-staging-" + uuid4().hex)
    stats = Counter()
    try:
        shutil.copytree(src, temporary, symlinks=False)
        for name in CORE:
            _write_json(temporary / ".storage" / name, transformed[name])
        original_package = temporary / "custom_components" / "wnhf"
        if not original_package.is_dir():
            raise StageError("Legacy package missing; verify input snapshot")
        shutil.rmtree(original_package)
        shutil.copytree(pkg, temporary / "custom_components" / "red_queen")

        for path in _eligible_yaml(temporary):
            text = path.read_text(encoding="utf-8")
            updated, domain_count, calls = rewrite_yaml_source(
                text, configuration_root=(path.relative_to(temporary).as_posix()
                                          == "configuration.yaml"),
                allowed_services=allowed_services
            )
            stats["yaml_root_renames"] += domain_count
            stats["yaml_service_calls"] += calls
            if updated != text:
                path.write_text(updated, encoding="utf-8")
        for path in sorted((temporary / ".storage").glob("lovelace*")):
            if not path.is_file():
                continue
            old_doc = _json_doc(path)
            new_doc, count = rewrite_lovelace_json(
                old_doc, allowed_services=allowed_services)
            if count:
                _write_json(path, new_doc)
            stats["lovelace_service_calls"] += count

        # Verify again after transformation. Never rewrite user entity IDs.
        actual = {name: _json_doc(temporary / ".storage" / name) for name in CORE}
        if actual != transformed:
            raise StageError("Staged HA registries failed round-trip verification")
        _verify_identity(originals, actual)
        if (temporary / "custom_components/wnhf").exists():
            raise StageError("Legacy component still installed in stage")
        if (temporary / "configuration.yaml").exists():
            config_text = (temporary / "configuration.yaml").read_text(encoding="utf-8")
            if DOMAIN_RE.search(config_text):
                raise StageError("Legacy integration root remains in stage")
        # User Stores and the legacy wnhf/ directory are intentionally preserved:
        # existing Smart Living manual settings and dashboard state remain stable.
        result = {
            "schema_version": 1, "state": "STAGING_ONLY_NOT_PRODUCTION",
            "source_modified": False, "new_domain": "red_queen",
            "stats": dict(counts) | dict(stats),
            "legacy_data_stores_preserved": True,
            "entity_ids_renamed": 0,
            "old_registry_sha256": {key: _sha_file(src / ".storage" / key)
                                    for key in CORE},
            "stage_registry_sha256": {key: _sha_file(temporary / ".storage" / key)
                                      for key in CORE},
        }
        _write_json(temporary / "rq12_stage_report.json", result)
        os.rename(temporary, dest)
        return result
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Create NEW offline HA staging COPY only")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1]
                        / "custom_components/red_queen")
    args = parser.parse_args()
    try:
        result = stage(args.source, args.target, args.package)
    except (StageError, DomainMigrationError, OSError, ValueError) as err:
        print("REFUSED: " + str(err), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
