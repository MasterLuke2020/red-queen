#!/usr/bin/env python3
"""Pure, offline HA registry-domain transform for Red Queen 1.2 staging.

This module does not perform file IO, does not import HA and never alters inputs.
It intentionally preserves entity IDs, unique IDs, config-entry IDs and settings.
Only the precise HA integration domain ownership fields are changed.

DO NOT run against live Home Assistant registries; a separately qualified offline
application/recovery tool is necessary before any production cutover.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

OLD = "wnhf"
NEW = "red_queen"


class DomainMigrationError(ValueError):
    """Fail closed if a registry cannot be transformed unambiguously."""


def _records(doc: dict[str, Any], key: str) -> list[dict[str, Any]]:
    data = doc.get("data")
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise DomainMigrationError("Invalid HA registry data." + key)
    records = data[key]
    if not all(isinstance(rec, dict) for rec in records):
        raise DomainMigrationError("Invalid HA registry records." + key)
    return records


def plan_registry_transform(
    config_entries_doc: dict[str, Any],
    entity_registry_doc: dict[str, Any],
    device_registry_doc: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Return independent transformed copies plus non-sensitive change counts.

    HA runtime internals must never be written directly. These outputs can be
    inspected and tested against offline fixtures before designing cutover.
    """
    if not all(isinstance(doc, dict) for doc in (
        config_entries_doc, entity_registry_doc, device_registry_doc
    )):
        raise DomainMigrationError("Registry inputs must be JSON objects")

    docs = {
        "core.config_entries": deepcopy(config_entries_doc),
        "core.entity_registry": deepcopy(entity_registry_doc),
        "core.device_registry": deepcopy(device_registry_doc),
    }
    entries = _records(docs["core.config_entries"], "entries")
    entities = _records(docs["core.entity_registry"], "entities")
    devices = _records(docs["core.device_registry"], "devices")

    old_entries = [e for e in entries if e.get("domain") == OLD]
    new_entries = [e for e in entries if e.get("domain") == NEW]
    if len(old_entries) == 0 and len(new_entries) == 1:
        if any(e.get("platform") == OLD for e in entities):
            raise DomainMigrationError("Mixed-domain entity registry on already migrated entry")
        if any(
            isinstance(d.get("identifiers"), list) and
            any(isinstance(i, (list, tuple)) and len(i) == 2 and i[0] == OLD
                for i in d["identifiers"])
            for d in devices
        ):
            raise DomainMigrationError("Mixed-domain device identifiers after migration")
        return docs, {"already_migrated": True, "entries": 0,
                      "entities": 0, "devices": 0, "namespace_only_devices": 0,
                      "entity_ids_renamed": 0}

    if len(old_entries) != 1 or new_entries:
        raise DomainMigrationError("Expected one old-domain entry and no new-domain entry")

    entry_id = old_entries[0].get("entry_id")
    if not isinstance(entry_id, str) or not entry_id:
        raise DomainMigrationError("Old config entry is missing a stable entry_id")

    if any(e.get("platform") == OLD and e.get("config_entry_id") != entry_id
           for e in entities):
        raise DomainMigrationError("Old-domain entity is linked to an unexpected config entry")
    if any(e.get("platform") == NEW for e in entities):
        raise DomainMigrationError("New-domain entity already registered")

    new_identifiers = {
        tuple(i)
        for d in devices
        for i in (d.get("identifiers") if isinstance(d.get("identifiers"), list) else [])
        if isinstance(i, (list, tuple)) and len(i) == 2 and i[0] == NEW
    }
    changed_devices = 0
    namespace_only_devices = 0
    for device in devices:
        identifiers = device.get("identifiers")
        if identifiers is None:
            continue
        if not isinstance(identifiers, list):
            raise DomainMigrationError("Unexpected device identifier structure")
        old_pairs = [
            pair for pair in identifiers if isinstance(pair, (list, tuple)) and
            len(pair) == 2 and pair[0] == OLD
        ]
        if not old_pairs:
            continue
        # HA 2026.9.2 can omit config_entries on the persisted device
        # records. The precise old-domain identifier namespace is still
        # exclusively owned by this integration, and one old config entry
        # has already been verified above. A present but contradictory
        # association is always rejected.
        if "config_entries" in device:
            linked = device["config_entries"]
            if not isinstance(linked, list) or entry_id not in linked:
                raise DomainMigrationError(
                    "Old-domain device identifier has contradictory entry ownership"
                )
        else:
            namespace_only_devices += 1
        for pair in old_pairs:
            target = (NEW, pair[1])
            if target in new_identifiers:
                raise DomainMigrationError("New device identifier collision")
            new_identifiers.add(target)
        device["identifiers"] = [
            [NEW, pair[1]] if isinstance(pair, (list, tuple))
            and len(pair) == 2 and pair[0] == OLD else pair
            for pair in identifiers
        ]
        changed_devices += 1

    changed_entities = 0
    for entity in entities:
        if entity.get("platform") == OLD:
            entity["platform"] = NEW
            changed_entities += 1

    old_entries[0]["domain"] = NEW

    return docs, {
        "already_migrated": False,
        "entries": 1,
        "entities": changed_entities,
        "devices": changed_devices,
        "namespace_only_devices": namespace_only_devices,
        "entity_ids_renamed": 0,
    }
