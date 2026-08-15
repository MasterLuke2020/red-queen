#!/usr/bin/env python3
"""Static repository checks for the Red Queen 1.0.0-rc4 candidate."""
from __future__ import annotations

import compileall
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "wnhf"
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


for path in [
    ROOT / "README.md",
    ROOT / "PUBLISHING_CHECKLIST.md",
    ROOT / "LICENSE",
    ROOT / ".github" / "CODEOWNERS",
    ROOT / ".github" / "workflows" / "hassfest.yml",
    INTEGRATION / "__init__.py",
    INTEGRATION / "manifest.json",
    INTEGRATION / "services.yaml",
    INTEGRATION / "translations" / "en.json",
    INTEGRATION / "translations" / "de.json",
    ROOT / "docs" / "RC4_CANDIDATE_VALIDATION.md",
]:
    if not path.exists():
        fail(f"Missing required path: {path.relative_to(ROOT)}")

try:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
except Exception as exc:
    fail(f"manifest.json invalid: {exc}")
    manifest = {}

expected = {
    "domain": "wnhf",
    "name": "Red Queen",
    "version": "1.0.0-rc4",
    "documentation": "https://github.com/MasterLuke2020/red-queen#readme",
    "issue_tracker": "https://github.com/MasterLuke2020/red-queen/issues",
    "codeowners": ["@MasterLuke2020"],
}
for key, value in expected.items():
    if manifest.get(key) != value:
        fail(f"manifest {key!r}: expected {value!r}, got {manifest.get(key)!r}")

for path in ROOT.rglob("*.json"):
    if path.name.endswith(".example"):
        continue
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")

if not compileall.compile_dir(str(INTEGRATION), quiet=1, force=True):
    fail("Python compileall failed")

service_text = (INTEGRATION / "services.yaml").read_text(encoding="utf-8")
service_keys = re.findall(r"(?m)^([a-z0-9_]+):\s*$", service_text)
if len(service_keys) != 66:
    fail(f"Expected 66 service definitions, found {len(service_keys)}")
if len(set(service_keys)) != len(service_keys):
    fail("Duplicate service keys detected in services.yaml")

checksum_file = ROOT / "checksums" / "rc4_source.sha256"
if not checksum_file.exists():
    fail("Missing RC4 source checksum catalogue: checksums/rc4_source.sha256")
else:
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected_hash, rel = line.split(maxsplit=1)
        rel = rel.strip()
        path = ROOT / rel
        if not path.exists():
            fail(f"Checksum path missing: {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected_hash:
            fail(f"Checksum mismatch: {rel}")

if (ROOT / "hacs.json").exists():
    fail("hacs.json is active, but this candidate remains pre-publication")

if ERRORS:
    print("Red Queen repository verification FAILED")
    for error in ERRORS:
        print(f"- {error}")
    sys.exit(1)

print("Red Queen repository verification PASS")
print(f"- integration: {manifest.get('name')} {manifest.get('version')} ({manifest.get('domain')})")
print(f"- services: {len(service_keys)}")
print("- RC4 source checksums: PASS")
print("- active HACS metadata: intentionally disabled")
