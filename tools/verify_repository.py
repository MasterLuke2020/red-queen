#!/usr/bin/env python3
"""Static repository checks for the Red Queen 1.0.0-rc5 candidate."""
from __future__ import annotations

import ast
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
    ROOT / "docs" / "RC5_CANDIDATE_VALIDATION.md",
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
    "version": "1.0.0-rc5",
    "documentation": "https://github.com/MasterLuke2020/red-queen#readme",
    "issue_tracker": "https://github.com/MasterLuke2020/red-queen/issues",
    "codeowners": ["@MasterLuke2020"],
}
for key, value in expected.items():
    if manifest.get(key) != value:
        fail(f"manifest {key!r}: expected {value!r}, got {manifest.get(key)!r}")

# Keep the layered execution version markers coherent. The dry-run planner has
# its own contract implementation version, while the public real-execution
# contract is versioned separately. Both are intentionally checked here.
release = json.loads((INTEGRATION / "RELEASE.json").read_text(encoding="utf-8"))
if release.get("canonical_execution_contract") != "1.7-rc5":
    fail("RELEASE.json canonical_execution_contract must be 1.7-rc5")

const_text = (INTEGRATION / "const.py").read_text(encoding="utf-8")
for marker in (
    'GENERIC_EXECUTION_CONTRACT_VERSION = "1.6-rc5"',
    'GENERIC_REAL_EXECUTION_VERSION = "1.7-rc5"',
    'CANONICAL_EXECUTION_CONTRACT_VERSION = "1.7-rc5"',
):
    if marker not in const_text:
        fail(f"Missing execution version marker: {marker}")

planner_text = (INTEGRATION / "executions" / "generic_planner.py").read_text(encoding="utf-8")
if 'CONTRACT_VERSION = "1.6-rc5"' not in planner_text:
    fail("GenericExecutionPlanner.CONTRACT_VERSION must be 1.6-rc5")

real_text = (INTEGRATION / "executions" / "generic_real.py").read_text(encoding="utf-8")
if 'VERSION = "1.7-rc5"' not in real_text:
    fail("GenericExecutionEngine.VERSION must be 1.7-rc5")

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

# Verify the semantic action catalogue without importing Home Assistant.
try:
    capability_tree = ast.parse(
        (INTEGRATION / "capabilities" / "core.py").read_text(encoding="utf-8")
    )
    actions: list[str] = []
    confirmation: dict[str, bool] = {}
    for node in ast.walk(capability_tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "CapabilityAction"
        ):
            continue
        action_id = None
        confirmation_required = None
        for keyword in node.keywords:
            if keyword.arg == "action_id" and isinstance(keyword.value, ast.Constant):
                action_id = keyword.value.value
            elif (
                keyword.arg == "confirmation_required"
                and isinstance(keyword.value, ast.Constant)
            ):
                confirmation_required = bool(keyword.value.value)
        if isinstance(action_id, str):
            actions.append(action_id)
            confirmation[action_id] = bool(confirmation_required)

    if len(actions) != 13 or len(set(actions)) != 13:
        fail(f"Expected 13 unique semantic actions, found {len(actions)}")
    for action_id in ("garage.snapshot", "garage.open", "garage.close"):
        if action_id not in actions:
            fail(f"Missing semantic garage action: {action_id}")
    for action_id in ("garage.open", "garage.close"):
        if confirmation.get(action_id) is not True:
            fail(f"{action_id} must require explicit confirmation")
except Exception as exc:
    fail(f"Semantic action catalogue check failed: {exc}")

try:
    contract_tree = ast.parse(
        (INTEGRATION / "executions" / "action_contracts.py").read_text(
            encoding="utf-8"
        )
    )
    contracts: list[str] = []
    for node in ast.walk(contract_tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "CanonicalActionExecutionContract"
        ):
            continue
        for keyword in node.keywords:
            if keyword.arg == "action_id" and isinstance(keyword.value, ast.Constant):
                if isinstance(keyword.value.value, str):
                    contracts.append(keyword.value.value)
    if len(contracts) != 8 or len(set(contracts)) != 8:
        fail(f"Expected 8 unique canonical real contracts, found {len(contracts)}")
    for action_id in ("garage.open", "garage.close"):
        if action_id not in contracts:
            fail(f"Missing canonical garage contract: {action_id}")
except Exception as exc:
    fail(f"Canonical action contract check failed: {exc}")

checksum_file = ROOT / "checksums" / "rc5_source.sha256"
if not checksum_file.exists():
    fail("Missing RC5 source checksum catalogue: checksums/rc5_source.sha256")
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
        # Git normalizes text files to LF in the repository, while a Windows
        # working tree may expose CRLF. Source integrity must therefore be
        # independent of the host platform's checkout line endings.
        source_bytes = path.read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha256(source_bytes).hexdigest()
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
print("- semantic actions: 13")
print("- canonical real contracts: 8")
print("- RC5 source checksums: PASS")
print("- active HACS metadata: intentionally disabled")
