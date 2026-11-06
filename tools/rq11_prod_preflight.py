#!/usr/bin/env python3
"""Read-only production preflight for Red Queen 1.1.0 upgrade planning.

No HA API token, credentials, historical states or integration configuration
are read. No container restarts, Docker writes or PLC actions. This is NOT
the installer and does NOT verify any Restic backup.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

CONTAINER_NAME = "homeassistant"
REPORT = Path.home() / "redqueen11_production_preflight.json"


def docker(*args: str) -> bytes:
    proc = subprocess.run(
        ["sudo", "docker", *args], check=False,
        capture_output=True,
    )
    if proc.returncode:
        # Do not print stderr blindly: Docker may include sensitive metadata.
        raise RuntimeError(f"Docker command failed: {args[0]} (exit {proc.returncode})")
    return proc.stdout


def parse_json(path: str) -> dict:
    raw = docker("exec", CONTAINER_NAME, "cat", path)
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise RuntimeError(f"Invalid or unreadable JSON at {path}") from err


def memory_available_kib() -> int:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return 0


def main() -> int:
    report = {
        "schema": "rq11.production_preflight.v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "host_architecture": platform.machine(),
        "container_name": CONTAINER_NAME,
        "production_modified": False,
        "backup_verified": False,
        "candidate_installed": False,
        "warnings": [],
    }
    try:
        info = json.loads(docker("inspect", CONTAINER_NAME))[0]
        state = info.get("State") or {}
        config = info.get("Config") or {}
        host = info.get("HostConfig") or {}
        mounts = info.get("Mounts") or []
        conf_mount = next(
            (mount for mount in mounts if mount.get("Destination") == "/config"),
            None,
        )
        report["container_running"] = bool(state.get("Running"))
        report["container_image_reference"] = config.get("Image")
        report["container_image_id"] = str(info.get("Image", ""))[:32]
        report["restart_policy"] = (host.get("RestartPolicy") or {}).get("Name")
        labels = config.get("Labels") or {}
        report["docker_compose_managed"] = bool(
            labels.get("com.docker.compose.project")
        )
        report["config_mount"] = (
            {
                "type": conf_mount.get("Type"),
                "source": conf_mount.get("Source"),
                "read_write": conf_mount.get("RW"),
            } if conf_mount is not None else None
        )
        report["available_host_memory_mib"] = memory_available_kib() // 1024
        if conf_mount and conf_mount.get("Source"):
            try:
                st = os.statvfs(conf_mount["Source"])
                report["available_config_disk_mib"] = (
                    st.f_bavail * st.f_frsize // 1024 // 1024
                )
            except (OSError, PermissionError):
                report["available_config_disk_mib"] = None
        manifest_path = "/config/custom_components/wnhf/manifest.json"
        release_path = "/config/custom_components/wnhf/RELEASE.json"
        manifest_raw = docker("exec", CONTAINER_NAME, "cat", manifest_path)
        release_raw = docker("exec", CONTAINER_NAME, "cat", release_path)
        manifest = json.loads(manifest_raw)
        release = json.loads(release_raw)
        report["installed_manifest_version"] = manifest.get("version")
        report["installed_release_version"] = release.get("version")
        report["installed_release_channel"] = release.get("channel")
        report["installed_manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
        report["installed_release_sha256"] = hashlib.sha256(release_raw).hexdigest()
        if not report["container_running"]:
            report["warnings"].append("Production Home Assistant is not running")
        if manifest.get("domain") != "wnhf":
            report["warnings"].append("Unexpected integration domain")
        if manifest.get("version") != "1.0.0":
            report["warnings"].append("Installed version differs from 1.0.0 baseline")
        if release.get("version") != manifest.get("version"):
            report["warnings"].append("Manifest/RELEASE metadata mismatch")
        if conf_mount is None or conf_mount.get("Type") != "bind":
            report["warnings"].append(
                "Configuration is not a normal Docker bind mount; installer must adapt"
            )
        if conf_mount and conf_mount.get("RW") is not True:
            report["warnings"].append("Configuration mount is not read-write")
        report["status"] = "READ_ONLY_PREFLIGHT_COMPLETE"
    except (ValueError, RuntimeError, IndexError, KeyError, TypeError) as err:
        report["status"] = "INCOMPLETE"
        report["warnings"].append(type(err).__name__ + ": " + str(err))
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    REPORT.chmod(0o600)
    print("Red Queen 1.1 production preflight: " + report["status"])
    print("Production code and HA container were NOT modified.")
    print("Report saved at " + str(REPORT))
    if report.get("installed_manifest_version"):
        print("Current installed version: " + report["installed_manifest_version"])
    for warning in report["warnings"]:
        print("WARNING: " + warning)
    return 0 if report["status"] == "READ_ONLY_PREFLIGHT_COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
