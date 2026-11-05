#!/usr/bin/env python3
"""Build a reproducible *non-production* Red Queen 1.1 release-candidate ZIP.

Uses only committed integration files. It does not read a running Home Assistant,
copy configuration, access a PLC, deploy code, or create a GitHub Release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "wnhf"
DIST = ROOT / "dist"
SKIP = {"__pycache__", ".DS_Store", ".git"}
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def fail(message: str) -> None:
    raise SystemExit("RC package refused: " + message)


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT,
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def package_files() -> list[Path]:
    if not INTEGRATION.is_dir():
        fail("Integration source missing")
    files = []
    for path in sorted(INTEGRATION.rglob("*")):
        if path.is_symlink():
            fail(f"Symlinks forbidden: {path.relative_to(ROOT)}")
        if not path.is_file():
            continue
        if any(part in SKIP for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix in {".pyc", ".pyo", ".swp"}:
            continue
        if not path.resolve().is_relative_to(INTEGRATION.resolve()):
            fail(f"Path escapes integration: {path}")
        files.append(path)
    if len(files) < 100:
        fail("Unexpectedly few integration files")
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir", type=Path, default=DIST,
        help="Destination for RC ZIP and checksums; never HA production config",
    )
    args = parser.parse_args()
    outdir = args.out_dir.resolve()
    if outdir == INTEGRATION or INTEGRATION.is_relative_to(outdir):
        fail("Output directory cannot be the integration source")
    if str(outdir).startswith("/config/") or outdir == Path("/config"):
        fail("Never write package outputs into Home Assistant configuration")

    manifest = json.loads((INTEGRATION / "manifest.json").read_text())
    release = json.loads((INTEGRATION / "RELEASE.json").read_text())
    if not (
        manifest.get("domain") == "wnhf"
        and manifest.get("version") == release.get("version") == "1.1.0"
        and release.get("channel") == "candidate"
        and release.get("phase") == "rc"
        and release.get("candidate_status") == "development"
    ):
        fail("Not the qualified 1.1.0 development candidate metadata")

    outdir.mkdir(parents=True, exist_ok=True)
    name = "red_queen_1.1.0-rc1.zip"
    archive = outdir / name
    files = package_files()
    # Use stable bytes/metadata so identical source builds generate identical ZIP.
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            info = ZipInfo(filename=rel, date_time=ZIP_TIME)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.create_system = 3
            zf.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED,
                        compresslevel=9)

    payload = archive.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    (outdir / (name + ".sha256")).write_text(
        digest + "  " + name + "\n", encoding="utf-8",
    )
    info = {
        "project": "Red Queen",
        "release": "1.1.0",
        "candidate": "rc1",
        "channel": "development_not_production",
        "git_commit": git_head(),
        "archive": name,
        "sha256": digest,
        "size_bytes": len(payload),
        "integration_file_count": len(files),
        "physical_hardware_tested_by_package": False,
        "production_deployed": False,
    }
    (outdir / "red_queen_1.1.0-rc1.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(info, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
