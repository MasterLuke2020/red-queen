#!/usr/bin/env python3
"""Branch-only checks while the immutable stable 1.0.0 verifier is preserved.

Full 1.1 release qualification will replace this development gate before merge.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


for path in sorted((ROOT / "custom_components" / "wnhf").rglob("*.py")):
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as err:
        fail(f"Python syntax: {path.relative_to(ROOT)}: {err}")

for path in sorted((ROOT / "tools").glob("*.py")):
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as err:
        fail(f"Tools syntax: {path.relative_to(ROOT)}: {err}")

for path in sorted((ROOT / "custom_components" / "wnhf").rglob("*.json")):
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as err:
        fail(f"JSON validation: {path.relative_to(ROOT)}: {err}")

for path in (ROOT / "custom_components" / "wnhf").rglob("*.yaml"):
    try:
        yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as err:
        fail(f"YAML validation: {path.relative_to(ROOT)}: {err}")

manifest = json.loads(
    (ROOT / "custom_components" / "wnhf" / "manifest.json").read_text()
)
if manifest.get("domain") != "wnhf":
    fail("Technical domain must remain wnhf")
if manifest.get("version") != "1.0.0":
    fail("Development branch must not masquerade as promoted 1.1.0")
platform_constants = (ROOT / "custom_components" / "wnhf" / "const.py").read_text(encoding="utf-8")
for marker in ('"light"', '"select"', '"text"', '"button"'):
    if marker not in platform_constants:
        fail("Smart Living platform marker missing: " + marker)

required = (
    "smart_living_logic.py",
    "smart_living_runtime.py",
    "smart_living_messages.py",
    "select.py",
    "text.py",
    "light.py",
)
for filename in required:
    if not (ROOT / "custom_components" / "wnhf" / filename).is_file():
        fail("Missing Smart Living module: " + filename)

# Smart Living must reuse the already-tested native asyncua DALI sources.
# Prevent reintroduction of duplicate wnhf_* RGBW proxy entities in HA.
light_source = (ROOT / "custom_components" / "wnhf" / "light.py").read_text(encoding="utf-8")
light_tree = ast.parse(light_source)
if any(
    isinstance(node, ast.ClassDef) and node.name == "WNHFSmartRGBWLight"
    for node in light_tree.body
):
    fail("Do not register duplicate Smart Living light proxy entities")
dashboard_bindings = (ROOT / "custom_components" / "wnhf" / "dashboard_binding.py").read_text(encoding="utf-8")
for marker in ("allowed_sources", "entry.entity_id in allowed_sources", 'entry.platform != DOMAIN'):
    if marker not in dashboard_bindings:
        fail("Dashboard DALI source allowlist check missing: " + marker)

result = subprocess.run(
    ["git", "diff", "--check", "HEAD^", "HEAD"],
    cwd=ROOT, capture_output=True, text=True, check=False,
)
if result.returncode != 0:
    fail("Git whitespace: " + result.stdout + result.stderr)

if ERRORS:
    print("Red Queen 1.1 development verification FAILED")
    for error in ERRORS:
        print("- " + error)
    sys.exit(1)

print("Red Queen 1.1 development verification PASS")
print("NOTE: This is NOT a stable-release qualification")
