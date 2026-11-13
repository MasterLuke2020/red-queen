#!/usr/bin/env python3
"""Restore a dated real Restic HA snapshot to a private OFFLINE lab, then rehearse 1.2.

Requires an already-mounted existing Restic repository and its existing password
file. Never mounts disks, changes backup schedules, modifies Restic repository,
starts HA, calls hardware, or writes to live Home Assistant /config.
Only prints non-sensitive summary; the restored backup remains CONFIDENTIAL.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo
from typing import Any

from rq12_site_stage_preflight import SitePreflightError, rehearse

DEFAULT_HA_BACKUP_PATH = "/srv/containers/homeassistant/config"
ROOT = Path(__file__).resolve().parents[1]


class ResticRehearsalError(ValueError):
    """Fail-closed refusal, no automatic production change."""


def choose_snapshot(
    snapshots: list[dict[str, Any]], *,
    day: date, ha_path: str, host: str, timezone: str,
) -> dict[str, Any]:
    """Select exact-day, exact-host full HA backup, NOT generic 'latest'."""
    matching: list[tuple[datetime, dict[str, Any]]] = []
    tz = ZoneInfo(timezone)
    for obj in snapshots:
        if not isinstance(obj, dict):
            continue
        if obj.get("hostname") != host:
            continue
        paths = obj.get("paths", [])
        if not isinstance(paths, list) or not any(
            isinstance(p, str) and (
                ha_path == p.rstrip("/")
                or ha_path.startswith(p.rstrip("/") + "/")
            ) for p in paths
        ):
            continue
        try:
            stamp = datetime.fromisoformat(
                obj["time"].replace("Z", "+00:00")
            )
        except (KeyError, AttributeError, TypeError, ValueError):
            continue
        if stamp.tzinfo is None or stamp.astimezone(tz).date() != day:
            continue
        snap_id = obj.get("id", "")
        if not isinstance(snap_id, str) or len(snap_id) != 64 or not all(
            char in "0123456789abcdef" for char in snap_id
        ):
            continue
        matching.append((stamp, obj))
    if not matching:
        raise ResticRehearsalError(
            "No full Home Assistant snapshot on selected local date/host; "
            "inspect the backup job without switching to an arbitrary snapshot"
        )
    return max(matching, key=lambda item: item[0])[1]


def _restic(restic_path: str, repo: Path, password: Path, args: list[str]) -> str:
    cmd = [
        restic_path, "--no-lock", "--repo", str(repo), "--password-file", str(password),
        *args,
    ]
    try:
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True,
            timeout=60 * 45,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ResticRehearsalError("Unable to execute Restic command") from exc
    if result.returncode:
        # Do not disclose repository, paths, secret endpoints, Restic stdout
        # or stderr in the terminal output.
        raise ResticRehearsalError(
            f"Restic command failed (exit {result.returncode}); "
            "inspect secure host-local backup diagnostics"
        )
    return result.stdout


def _private(path: Path) -> None:
    if not path.is_dir() or path.is_symlink() or path.stat().st_mode & 0o077:
        raise ResticRehearsalError("Parent lab folder must be private 0700")


def _guard(
    *, repo: Path, mounted: Path, password: Path, lab: Path,
    live: Path, ha_path: str, restic_bin: str,
) -> None:
    if os.geteuid() != 0:
        raise ResticRehearsalError("Run as root (sudo); Restic credential file is private")
    if not mounted.is_dir() or not os.path.ismount(mounted):
        raise ResticRehearsalError(
            "Existing backup storage is not mounted; no mount attempted"
        )
    if not repo.is_dir() or not repo.is_relative_to(mounted):
        raise ResticRehearsalError("Expected repository not available on mounted volume")
    if not password.is_file():
        raise ResticRehearsalError("Configured Restic password file not found")
    if not live.is_dir() or not (live / ".storage").is_dir():
        raise ResticRehearsalError("Live Home Assistant mount not recognized")
    if not restic_bin:
        raise ResticRehearsalError("Restic binary unavailable")
    if lab.exists() or lab.is_symlink():
        raise ResticRehearsalError("Lab directory already exists; refuse overwrite")
    _private(lab.parent)
    # The lab is never the same as, inside, or a parent of any sensitive
    # production location or the Restic repository itself.
    for protected in (live, repo, mounted, password.parent):
        if lab.is_relative_to(protected) or protected.is_relative_to(lab):
            raise ResticRehearsalError("Lab overlaps a protected production path")
    if not ha_path.startswith("/") or ha_path == "/":
        raise ResticRehearsalError("HA backup path must be an absolute subdirectory")
    # Avoid restoring a very large backup to a system with almost no space.
    # Stage preflight performs the exact size-based two-copy check later.
    if shutil.disk_usage(lab.parent).free < 6 * 1024 ** 3:
        raise ResticRehearsalError(
            "Less than 6 GiB free space for source restore + 2 staged copies"
        )


def run(
    *, repo: Path, mounted: Path, password: Path, lab: Path,
    live: Path, package: Path, on_date: date, host: str,
    ha_path: str = DEFAULT_HA_BACKUP_PATH, timezone: str = "Europe/Vienna",
) -> dict[str, Any]:
    repo, mounted, password, lab, live, package = (
        p.resolve() for p in (repo, mounted, password, lab, live, package)
    )
    binary = shutil.which("restic") or ""
    _guard(
        repo=repo, mounted=mounted, password=password, lab=lab,
        live=live, ha_path=ha_path, restic_bin=binary,
    )
    # No writes occur until an exact-day and exact-host snapshot is found.
    stdout = _restic(binary, repo, password, ["snapshots", "--json"])
    try:
        snapshots = json.loads(stdout)
    except ValueError as exc:
        raise ResticRehearsalError("Invalid Restic snapshot JSON") from exc
    if not isinstance(snapshots, list):
        raise ResticRehearsalError("Restic snapshots must be a JSON array")
    snap = choose_snapshot(
        snapshots, day=on_date, ha_path=ha_path, host=host, timezone=timezone,
    )
    snap_id = snap["id"]

    # All confidential snapshot data stays under a newly created 0700 dir.
    lab.mkdir(mode=0o700)
    restore_base = lab / "restored"
    stage_parent = lab / "stage-output"
    rollback_parent = lab / "rollback-output"
    for path in (restore_base, stage_parent, rollback_parent):
        path.mkdir(mode=0o700)
    try:
        _restic(
            binary, repo, password,
            ["restore", snap_id, "--target", str(restore_base),
             "--include", ha_path],
        )
        source = restore_base / ha_path.lstrip("/")
        if not (source / ".storage/core.config_entries").is_file():
            raise ResticRehearsalError(
                "Restored snapshot has no HA config registry at expected path"
            )
        if not (source / "custom_components/wnhf/manifest.json").is_file():
            raise ResticRehearsalError(
                "Restored snapshot missing old-domain integration package"
            )
        result = rehearse(
            source=source, staged=stage_parent / "red_queen_12",
            rollback=rollback_parent / "wnhf_11",
            live=live, package=package,
            expected_entities=245, expected_devices=36,
        )
    except Exception:
        # Do not delete recovered backup automatically. Sensitive contents
        # remain local under a private directory for operator-only inspection.
        raise
    return {
        "state": "OFFLINE_RESTIC_SITE_REHEARSAL_PASSED_NOT_PRODUCTION",
        "snapshot": snap_id[:12],
        "snapshot_local_date": on_date.isoformat(),
        "snapshot_host_matched": True,
        "source_untouched": result["source_modified"] is False,
        "rollback_copy_exact": result["rollback_copy_exact"],
        "entities": result["old_domain_entities"],
        "devices": result["old_domain_devices"],
        "files_compared": result["original_files_count"],
        "legacy_stores_preserved": result["legacy_store_keys_preserved"],
        "no_home_assistant_boot": True,
        "release_approved": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Existing Restic snapshot -> OFFLINE Red Queen 1.2 rehearsal")
    p.add_argument("--repository", type=Path, required=True)
    p.add_argument("--repository-mount", type=Path, required=True)
    p.add_argument("--password-file", type=Path, required=True)
    p.add_argument("--lab", type=Path, required=True)
    p.add_argument("--live-config", type=Path, required=True)
    p.add_argument("--host", required=True)
    p.add_argument("--date", type=date.fromisoformat, required=True)
    p.add_argument("--ha-backup-path", default=DEFAULT_HA_BACKUP_PATH)
    p.add_argument("--package", type=Path, default=ROOT / "custom_components/red_queen")
    args = p.parse_args()
    try:
        result = run(
            repo=args.repository, mounted=args.repository_mount,
            password=args.password_file, lab=args.lab,
            live=args.live_config, package=args.package,
            on_date=args.date, host=args.host,
            ha_path=args.ha_backup_path,
        )
    except (ResticRehearsalError, SitePreflightError, OSError, ValueError) as exc:
        print("REFUSED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
