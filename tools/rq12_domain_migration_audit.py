#!/usr/bin/env python3
"""Read-only impact audit for migrating the Home Assistant domain wnhf -> red_queen.

It never imports Home Assistant, mutates configuration, or prints storage values.
Only explicitly named local HA registries and automation/dashboard sources are read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

OLD = "wnhf"
NEW = "red_queen"
CORE_FILES = ("core.config_entries", "core.entity_registry", "core.device_registry")
TEXT_FILES = ("configuration.yaml", "automations.yaml", "scripts.yaml", "scenes.yaml")
MAX_EXAMPLES = 12


def _read_storage(storage: Path, name: str, errors: list[str]) -> dict[str, Any]:
    path = storage / name
    if not path.is_file():
        errors.append("Missing HA registry: .storage/" + name)
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        errors.append("Unreadable/invalid HA registry: .storage/" + name)
        return {}
    if not isinstance(obj, dict) or not isinstance(obj.get("data"), dict):
        errors.append("Unexpected HA registry structure: .storage/" + name)
        return {}
    return obj["data"]


def _items(obj: dict[str, Any], key: str, errors: list[str]) -> list[dict[str, Any]]:
    value = obj.get(key, [])
    if not isinstance(value, list):
        errors.append("Unexpected registry list: " + key)
        return []
    return [item for item in value if isinstance(item, dict)]


def _source_counts(root: Path) -> dict[str, int]:
    """Count references only; never return or log raw configuration contents."""
    candidates = [root / name for name in TEXT_FILES]
    storage = root / ".storage"
    if storage.is_dir():
        candidates += sorted(storage.glob("lovelace*"))
        candidates += sorted(storage.glob("wnhf*"))
        candidates += sorted(storage.glob("red_queen*"))
    findings: dict[str, int] = {}
    for path in candidates:
        if not path.is_file() or path.is_symlink():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        count = content.count(OLD)
        if count:
            findings[str(path.relative_to(root))] = count
    return findings


def inspect(config: Path) -> dict[str, Any]:
    """Inspect a *copy* or live HA config read-only; never change its contents."""
    root = config.expanduser().resolve()
    errors: list[str] = []
    blockers: list[str] = []
    if not root.is_dir():
        return {"schema_version": 1, "status": "invalid_path",
                "blockers": ["Configuration directory does not exist"],
                "errors": [], "note": "Read-only audit; no migration performed"}

    storage = root / ".storage"
    entries = _items(_read_storage(storage, CORE_FILES[0], errors), "entries", errors)
    entities = _items(_read_storage(storage, CORE_FILES[1], errors), "entities", errors)
    devices = _items(_read_storage(storage, CORE_FILES[2], errors), "devices", errors)

    old_entries = [e for e in entries if e.get("domain") == OLD]
    new_entries = [e for e in entries if e.get("domain") == NEW]
    old_entities = [e for e in entities if e.get("platform") == OLD]
    new_entities = [e for e in entities if e.get("platform") == NEW]
    old_entry_ids = {e.get("entry_id") for e in old_entries}
    linked_entities = [e for e in entities if e.get("config_entry_id") in old_entry_ids]
    old_devices = [
        d for d in devices
        if any(isinstance(pair, (list, tuple)) and len(pair) == 2 and pair[0] == OLD
               for pair in d.get("identifiers", []) if isinstance(d.get("identifiers"), list))
    ]

    if len(old_entries) != 1:
        blockers.append("Expected exactly one existing wnhf config entry")
    if new_entries:
        blockers.append("red_queen config entry already exists: investigate duplicate integration")

    existing_ids = {e.get("entity_id") for e in entities if isinstance(e.get("entity_id"), str)}
    proposed: dict[str, str] = {}
    foreign_prefix_ids: list[str] = []
    conflicts: list[str] = []
    for item in entities:
        entity_id = item.get("entity_id")
        if not isinstance(entity_id, str) or "." not in entity_id:
            continue
        prefix, object_id = entity_id.split(".", 1)
        if not object_id.startswith("wnhf_"):
            continue
        if item.get("platform") != OLD or item.get("config_entry_id") not in old_entry_ids:
            # A user-named Automation or unrelated integration is NOT owned by
            # Red Queen even if its entity_id starts with the legacy prefix.
            foreign_prefix_ids.append(entity_id)
            continue
        target = prefix + ".red_queen_" + object_id[len("wnhf_"):]
        proposed[entity_id] = target
        if target in existing_ids:
            conflicts.append(target)
    if conflicts:
        blockers.append("Potential red_queen entity_id collisions detected")

    source_counts = _source_counts(root)
    old_storage_keys = sorted(
        p.name for p in storage.iterdir()
        if p.is_file() and not p.is_symlink() and p.name.startswith(OLD)
    ) if storage.is_dir() else []
    new_storage_keys = sorted(
        p.name for p in storage.iterdir()
        if p.is_file() and not p.is_symlink() and p.name.startswith(NEW)
    ) if storage.is_dir() else []

    if errors:
        blockers.append("Missing/invalid registry data: inspect audit errors")
    if (root / "custom_components" / OLD).is_dir() and (
            root / "custom_components" / NEW).exists():
        blockers.append("Both integration directories exist; cutover would be ambiguous")

    return {
        "schema_version": 1,
        "status": "needs_review" if blockers else "inventory_complete",
        "note": "Read-only inventory, NOT permission to rename or edit live .storage",
        "domain": {"current": OLD, "target": NEW},
        "counts": {
            "old_config_entries": len(old_entries),
            "new_config_entries": len(new_entries),
            "old_platform_entities": len(old_entities),
            "new_platform_entities": len(new_entities),
            "entities_linked_to_old_entry": len(linked_entities),
            "old_domain_device_identifiers": len(old_devices),
            "proposed_entity_id_changes": len(proposed),
            "foreign_wnhf_prefix_entity_ids": len(foreign_prefix_ids),
            "entity_id_collisions": len(conflicts),
        },
        "sample_old_entity_ids": sorted(
            str(item.get("entity_id")) for item in old_entities
            if isinstance(item.get("entity_id"), str)
        )[:MAX_EXAMPLES],
        "sample_proposed_entity_id_changes": [
            {"from": old_id, "to": proposed[old_id]}
            for old_id in sorted(proposed)[:MAX_EXAMPLES]
        ],
        "colliding_target_ids": sorted(set(conflicts))[:MAX_EXAMPLES],
        "sample_foreign_wnhf_prefix_entity_ids": sorted(foreign_prefix_ids)[:MAX_EXAMPLES],
        "legacy_storage_keys": old_storage_keys,
        "new_storage_keys": new_storage_keys,
        "reference_counts_by_file": source_counts,
        "integration_dirs": {
            "old_exists": (root / "custom_components" / OLD).is_dir(),
            "new_exists": (root / "custom_components" / NEW).is_dir(),
        },
        "errors": errors,
        "blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="READ ONLY: inventory Red Queen wnhf-to-red_queen migration impact"
    )
    parser.add_argument("--config", type=Path, required=True,
                        help="Home Assistant /config directory (prefer a backup copy)")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero when blockers or registry errors were found")
    args = parser.parse_args()
    result = inspect(args.config)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if args.strict and (result["blockers"] or result["errors"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
