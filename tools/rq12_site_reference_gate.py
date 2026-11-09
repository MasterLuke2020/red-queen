#!/usr/bin/env python3
"""READ ONLY: validate service references and identity of an existing OFFLINE HA stage.

Does not boot HA, change files, contact devices, or make release decisions.
Hidden old backup YAML is counted separately, because stage deliberately
preserves historical snapshots. Only active YAML and Lovelace references
block the cutover; stable old-prefix entity IDs remain unchanged by design.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from rq12_domain_reference_audit import audit
from rq12_domain_registry_transform import plan_registry_transform

CORE = ("core.config_entries", "core.entity_registry", "core.device_registry")
BLOCKERS = (
    "literal_service_calls", "root_domain_keys", "legacy_logger_keys",
    "logger_channel_mentions", "template_or_domain_calls",
    "unclassified_dotted_mentions",
)
STORES = {"wnhf.dashboard", "wnhf.smart_living"}


class AcceptanceError(ValueError):
    pass


def _overlap(a: Path, b: Path) -> bool:
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


def _json(root: Path, relative: str) -> dict[str, Any]:
    try:
        obj = json.loads((root / relative).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise AcceptanceError("Cannot read required offline JSON registry") from exc
    if not isinstance(obj, dict):
        raise AcceptanceError("Invalid offline JSON document")
    return obj


def _historical(relative: str) -> bool:
    parts = Path(relative).parts
    if len(parts) == 2 and parts[0] == ".storage" and parts[1].startswith("lovelace"):
        return False
    return any(part.startswith(".") for part in parts)


def _partition(report: dict[str, Any]) -> tuple[Counter[str], Counter[str]]:
    active: Counter[str] = Counter()
    archived: Counter[str] = Counter()
    for item in report["files_with_legacy_references"]:
        (archived if _historical(item["file"]) else active).update(item["counts"])
    return active, archived


def inspect(
    source: Path, stage: Path, live: Path, *,
    expected_entities: int = 245, expected_devices: int = 36,
) -> dict[str, Any]:
    src, dst, prod = (p.resolve() for p in (source, stage, live))
    if not all(p.is_dir() for p in (src, dst, prod)):
        raise AcceptanceError("Source, stage and live config must exist")
    if _overlap(src, dst) or _overlap(src, prod) or _overlap(dst, prod):
        raise AcceptanceError("Refusing overlapping live/backup/staging paths")

    report = _json(dst, "rq12_stage_report.json")
    site = _json(dst, "rq12_site_preflight.json")
    if report.get("state") != "STAGING_ONLY_NOT_PRODUCTION":
        raise AcceptanceError("Staging report missing or has wrong state")
    if site.get("state") != "OFFLINE_SITE_REHEARSAL_PASSED_NOT_PRODUCTION":
        raise AcceptanceError("Site recovery report missing or has wrong state")
    if not site.get("rollback_copy_exact") or site.get("release_approved"):
        raise AcceptanceError("Rollback copy unverified or incorrectly released")
    if (site.get("old_domain_entities"), site.get("old_domain_devices")) != (
        expected_entities, expected_devices
    ):
        raise AcceptanceError("Real house inventory changed from approved baseline")
    if site.get("original_files_count", 0) < 1:
        raise AcceptanceError("No verified files in site snapshot")

    old = tuple(_json(src, ".storage/" + name) for name in CORE)
    new = {name: _json(dst, ".storage/" + name) for name in CORE}
    transformed, plan = plan_registry_transform(*old)
    if plan["already_migrated"] or (
        plan["entities"], plan["devices"]
    ) != (expected_entities, expected_devices):
        raise AcceptanceError("Unexpected source domain or registry counts")
    if new != transformed:
        raise AcceptanceError("Staged HA registry differs from exact domain transform")
    if (dst / "custom_components/wnhf").exists() or not (
        dst / "custom_components/red_queen/manifest.json"
    ).is_file():
        raise AcceptanceError("Staged integration package is ambiguous")
    if report.get("entity_ids_renamed") != 0:
        raise AcceptanceError("Entity IDs unexpectedly changed")

    before, _old_archived = _partition(audit(src))
    scanned = audit(dst)
    after, archived = _partition(scanned)
    if not scanned["legacy_data_directory_exists"]:
        raise AcceptanceError("Legacy house data directory was lost")
    if set(scanned["legacy_store_keys"]) != STORES:
        raise AcceptanceError("Expected two legacy Stores not preserved")
    if scanned["new_store_keys"]:
        raise AcceptanceError("Unexpected Store namespace collision")
    if before["entity_id_mentions"] != after["entity_id_mentions"]:
        raise AcceptanceError("Active HA entity references changed unexpectedly")

    unresolved = {key: after[key] for key in BLOCKERS if after[key]}
    return {
        "state": ("OFFLINE_REFERENCE_GATE_PASSED_NOT_PRODUCTION"
                  if not unresolved else "OFFLINE_REFERENCE_GATE_BLOCKED"),
        "release_approved": False,
        "production_changed": False,
        "old_domain_entities": plan["entities"],
        "old_domain_devices": plan["devices"],
        "original_files_compared": site["original_files_count"],
        "rollback_copy_exact": site["rollback_copy_exact"],
        "preserved_active_entity_reference_mentions": after["entity_id_mentions"],
        "service_calls_before": before["literal_service_calls"],
        "service_calls_after": after["literal_service_calls"],
        "logger_channels_before": before["logger_channel_mentions"],
        "logger_channels_after": after["logger_channel_mentions"],
        "active_legacy_reference_blockers": unresolved,
        "historical_hidden_backup_references": {
            key: archived[key] for key in BLOCKERS if archived[key]
        },
        "old_store_keys_retained": sorted(STORES),
        "limits": [
            "YAML/Lovelace scanning is heuristic",
            "External consumers outside HA config not scanned",
            "No HA boot, PLC, physical lights or network tested",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only house stage reference acceptance")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--live-config", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = inspect(args.source, args.stage, args.live_config)
    except (AcceptanceError, ValueError, OSError, KeyError, TypeError) as err:
        print("REFUSED: " + str(err), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if result["active_legacy_reference_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
