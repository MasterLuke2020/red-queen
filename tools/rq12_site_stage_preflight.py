#!/usr/bin/env python3
"""Offline Red Queen 1.2 house-snapshot staging and rollback rehearsal.

NO live Home Assistant, network, services, WAGO, HACS or Docker operations.
Never start the resulting HA stage against real devices or the home network.
Source must be a CONSISTENT, RESTORED, OFFLINE snapshot, NOT live /config.
Both output folders must be NEW and remain on the local operator machine.
No raw configuration/credentials are printed or uploaded.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from typing import Any

from rq12_domain_registry_transform import plan_registry_transform
from rq12_domain_stage import StageError, stage

CORE = ("core.config_entries", "core.entity_registry", "core.device_registry")
EXPECTED_STORES = ("wnhf.dashboard", "wnhf.smart_living")


class SitePreflightError(ValueError):
    """Rehearsal cannot prove isolation or exact migration consistency."""


def _overlap(first: Path, second: Path) -> bool:
    return first == second or first.is_relative_to(second) or second.is_relative_to(first)


def _file_inventory(root: Path) -> dict[str, str]:
    """Strong digest of every source/restore file. Never expose file contents."""
    if not root.is_dir() or root.is_symlink():
        raise SitePreflightError("Expected a real, non-symlink directory")
    digests: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise SitePreflightError("A snapshot contains symlinks; refuse rehearsal")
        if path.is_dir():
            continue
        if not path.is_file():
            raise SitePreflightError("Snapshot contains a non-regular file")
        h = sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        digests[path.relative_to(root).as_posix()] = h.hexdigest()
    return digests


def _store_bytes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for key in EXPECTED_STORES:
        path = root / ".storage" / key
        if not path.is_file() or path.is_symlink():
            raise SitePreflightError("Missing essential legacy Store: " + key)
        result[key] = sha256(path.read_bytes()).hexdigest()
    return result


def _load_doc(root: Path, name: str) -> dict[str, Any]:
    path = root / ".storage" / name
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise SitePreflightError("Unreadable HA registry: " + name) from exc
    if not isinstance(value, dict):
        raise SitePreflightError("Invalid HA registry: " + name)
    return value


def _guard_paths(source: Path, staged: Path, rollback: Path, live: Path) -> None:
    # Resolve symlinked ancestors before checking overlaps. In particular,
    # never allow any output inside the live config or its parent.
    if not source.is_dir() or not live.is_dir():
        raise SitePreflightError("Source snapshot and live config must exist")
    if any(_overlap(source, p) for p in (live, staged, rollback)):
        raise SitePreflightError("Snapshot overlaps live config or output folder")
    if any(_overlap(live, p) for p in (staged, rollback)):
        raise SitePreflightError("Refusing any output inside/around live HA config")
    if _overlap(staged, rollback):
        raise SitePreflightError("Stage and rollback output locations overlap")
    for target in (staged, rollback):
        if target.exists() or target.is_symlink():
            raise SitePreflightError("Outputs MUST be new; existing folder refused")
        if not target.parent.is_dir():
            raise SitePreflightError("Output parent does not exist")
        if target.parent == Path("/") or target == Path("/"):
            raise SitePreflightError("Cannot use filesystem root as output")
        # Entire HA snapshot contains credentials, keys and device endpoints.
        # A private parent prevents other users from accessing temporary files
        # while copytree preserves the original file permissions.
        if target.parent.stat().st_mode & 0o077:
            raise SitePreflightError(
                "Staging/rollback parent MUST be private (chmod 0700)"
            )


def _space_guard(source: Path, staged: Path, rollback: Path) -> None:
    # Conservatively demand enough free space for BOTH complete copies, even
    # when paths resolve to the same filesystem. No hardlinks, no sparse tricks.
    total_bytes = sum(p.stat().st_size for p in source.rglob("*") if p.is_file())
    needed = int(total_bytes * 1.15) + 64 * 1024 * 1024
    volumes: dict[int, tuple[Path, int]] = {}
    for folder in (staged.parent, rollback.parent):
        dev = folder.stat().st_dev
        path, total = volumes.get(dev, (folder, 0))
        volumes[dev] = (path, total + needed)
    for folder, demand in volumes.values():
        if shutil.disk_usage(folder).free < demand:
            raise SitePreflightError("Insufficient disk space for two full copies")


def rehearse(
    source: Path, staged: Path, rollback: Path, live: Path, package: Path,
    *, expected_entities: int, expected_devices: int,
) -> dict[str, Any]:
    src = source.resolve()
    out = staged.resolve()
    back = rollback.resolve()
    active = live.resolve()
    pkg = package.resolve()
    _guard_paths(src, out, back, active)
    if expected_entities < 1 or expected_devices < 1:
        raise SitePreflightError("Expected entity/device counts must be positive")
    if not (src / "configuration.yaml").is_file():
        raise SitePreflightError("Missing offline HA configuration.yaml")
    if not (src / "custom_components/wnhf/manifest.json").is_file():
        raise SitePreflightError("Missing old-domain component from snapshot")

    originals = tuple(_load_doc(src, key) for key in CORE)
    transformed, counts = plan_registry_transform(*originals)
    del transformed  # the real stage builds its own independent registry docs
    if counts["already_migrated"]:
        raise SitePreflightError("Expected an old-domain source snapshot")
    if counts["entities"] != expected_entities:
        raise SitePreflightError(
            f"Old-domain entity count changed: expected {expected_entities}, "
            f"found {counts['entities']}"
        )
    if counts["devices"] != expected_devices:
        raise SitePreflightError(
            f"Old-domain device count changed: expected {expected_devices}, "
            f"found {counts['devices']}"
        )
    if counts["entries"] != 1:
        raise SitePreflightError("Exactly one old config entry required")

    legacy_stores = _store_bytes(src)
    _space_guard(src, out, back)
    before = _file_inventory(src)
    stage_report = stage(src, out, pkg)
    if stage_report["stats"]["entities"] != expected_entities or (
        stage_report["stats"]["devices"] != expected_devices
    ):
        raise SitePreflightError("Stage registry totals changed unexpectedly")
    if stage_report["entity_ids_renamed"] != 0:
        raise SitePreflightError("Stage unexpectedly renamed entity IDs")
    if _store_bytes(out) != legacy_stores:
        raise SitePreflightError("Stage changed existing Smart Living / Dashboard stores")
    # The old data/registries must be preserved byte-for-byte.
    legacy_registry = "wnhf/house/registry/"
    src_legacy = {
        key: digest for key, digest in before.items()
        if key.startswith(legacy_registry)
    }
    staged_files = _file_inventory(out)
    for key, digest in src_legacy.items():
        if staged_files.get(key) != digest:
            raise SitePreflightError("Stage changed existing house registry file")

    # This is a *copy-based* rollback rehearsal, not a live restore or HA boot.
    shutil.copytree(src, back, symlinks=False)
    if _file_inventory(back) != before:
        raise SitePreflightError("Rollback copy differs from original snapshot")
    if _file_inventory(src) != before:
        raise SitePreflightError("Source snapshot modified during rehearsal")
    for name in CORE:
        if _load_doc(src, name) != _load_doc(back, name):
            raise SitePreflightError("Rollback registry mismatch")
    if _store_bytes(back) != legacy_stores:
        raise SitePreflightError("Rollback Store mismatch")
    result = {
        "state": "OFFLINE_SITE_REHEARSAL_PASSED_NOT_PRODUCTION",
        "schema_version": 1,
        "source_modified": False,
        "home_assistant_started": False,
        "actual_hardware_tested": False,
        "rollback_copy_exact": True,
        "original_files_count": len(before),
        "legacy_store_keys_preserved": list(EXPECTED_STORES),
        "legacy_house_registry_files_preserved": len(src_legacy),
        "old_domain_entries": counts["entries"],
        "old_domain_entities": counts["entities"],
        "old_domain_devices": counts["devices"],
        "staging_stats": stage_report["stats"],
        "release_approved": False,
    }
    # No path names, tokens, credentials, names of users or device endpoints
    # in the summary. Do not write anything inside the original snapshot.
    (out / "rq12_site_preflight.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Offline house staging + copy-rollback proof")
    p.add_argument("--source", type=Path, required=True,
                   help="CONSISTENT OFFLINE restored HA snapshot, never live config")
    p.add_argument("--stage", type=Path, required=True,
                   help="New, non-existing staging output directory")
    p.add_argument("--rollback", type=Path, required=True,
                   help="New, non-existing independent restored-copy directory")
    p.add_argument("--live-config", type=Path, required=True,
                   help="Current productive Docker /config host mount for path interlock")
    p.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1]
                   / "custom_components/red_queen")
    p.add_argument("--expected-entities", type=int, required=True)
    p.add_argument("--expected-devices", type=int, required=True)
    args = p.parse_args()
    try:
        result = rehearse(
            args.source, args.stage, args.rollback, args.live_config, args.package,
            expected_entities=args.expected_entities,
            expected_devices=args.expected_devices,
        )
    except (SitePreflightError, StageError, OSError, ValueError) as err:
        print("REFUSED: " + str(err), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
