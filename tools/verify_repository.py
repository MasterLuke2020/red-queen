#!/usr/bin/env python3
"""Static repository checks for the Red Queen 1.0.0-rc6 candidate."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "wnhf"
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized_sha256(path: Path) -> str:
    """Hash repository text independently of LF/CRLF checkout conversion."""
    source_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(source_bytes).hexdigest()


def verify_git_whitespace() -> str:
    """Run Git's canonical whitespace check when repository metadata exists."""
    if shutil.which("git") is None:
        return "SKIPPED (Git unavailable)"

    probe = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return "SKIPPED (no Git metadata)"

    staged = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--cached", "--quiet", "--"],
        check=False,
    )
    if staged.returncode == 1:
        command = ["git", "-C", str(ROOT), "diff", "--cached", "--check"]
    elif staged.returncode == 0:
        command = [
            "git",
            "-C",
            str(ROOT),
            "diff-tree",
            "--check",
            "--root",
            "-r",
            "HEAD",
        ]
    else:
        fail("Unable to determine staged Git state for whitespace verification")
        return "FAILED"

    check_result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if check_result.returncode != 0:
        details = check_result.stdout.strip() or check_result.stderr.strip()
        fail(f"Git whitespace check failed:\n{details}")
        return "FAILED"
    return "PASS"


def keyword_literal(node: ast.Call, name: str, default=None):
    for keyword in node.keywords:
        if keyword.arg == name:
            try:
                return ast.literal_eval(keyword.value)
            except (ValueError, TypeError):
                return default
    return default


required_paths = [
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "REPOSITORY_STATUS.md",
    ROOT / "PUBLISHING_CHECKLIST.md",
    ROOT / "LICENSE",
    ROOT / ".github" / "CODEOWNERS",
    ROOT / ".github" / "workflows" / "hassfest.yml",
    ROOT / "docs" / "CONFIGURATION.md",
    ROOT / "docs" / "FEATURE_MATRIX.md",
    ROOT / "docs" / "KNOWN_LIMITATIONS.md",
    ROOT / "docs" / "RELEASE_STATUS.md",
    ROOT / "docs" / "ROADMAP.md",
    ROOT / "docs" / "RC6_CANDIDATE_VALIDATION.md",
    INTEGRATION / "__init__.py",
    INTEGRATION / "manifest.json",
    INTEGRATION / "RELEASE.json",
    INTEGRATION / "services.yaml",
    INTEGRATION / "translations" / "en.json",
    INTEGRATION / "translations" / "de.json",
    INTEGRATION / "domain" / "notification.py",
    INTEGRATION / "providers" / "notifications.py",
    INTEGRATION / "docs" / "RELEASE_NOTES_1.0.0-rc6.md",
]
for path in required_paths:
    if not path.exists():
        fail(f"Missing required path: {path.relative_to(ROOT)}")

git_whitespace_status = verify_git_whitespace()

try:
    manifest = json.loads(read_text(INTEGRATION / "manifest.json"))
except Exception as exc:
    fail(f"manifest.json invalid: {exc}")
    manifest = {}

expected_manifest = {
    "domain": "wnhf",
    "name": "Red Queen",
    "version": "1.0.0-rc6",
    "documentation": "https://github.com/MasterLuke2020/red-queen#readme",
    "issue_tracker": "https://github.com/MasterLuke2020/red-queen/issues",
    "codeowners": ["@MasterLuke2020"],
}
for key, value in expected_manifest.items():
    if manifest.get(key) != value:
        fail(f"manifest {key!r}: expected {value!r}, got {manifest.get(key)!r}")

try:
    release = json.loads(read_text(INTEGRATION / "RELEASE.json"))
except Exception as exc:
    fail(f"RELEASE.json invalid: {exc}")
    release = {}

expected_release = {
    "product_name": "Red Queen",
    "version": "1.0.0-rc6",
    "candidate": "rc6",
    "development_baseline_version": "1.32.0",
    "release_baseline": "WP-4.7.13.1",
    "canonical_execution_api_version": "1.0",
    "canonical_execution_contract": "1.8-rc6",
}
for key, value in expected_release.items():
    if release.get(key) != value:
        fail(f"RELEASE.json {key!r}: expected {value!r}, got {release.get(key)!r}")

const_text = read_text(INTEGRATION / "const.py")
for marker in (
    'DEVELOPMENT_BASELINE_VERSION = "1.32.0"',
    'RELEASE_BASELINE = "WP-4.7.13.1"',
    'GENERIC_EXECUTION_CONTRACT_VERSION = "1.7-rc6"',
    'GENERIC_REAL_EXECUTION_VERSION = "1.8-rc6"',
    'CANONICAL_EXECUTION_CONTRACT_VERSION = "1.8-rc6"',
):
    if marker not in const_text:
        fail(f"Missing release/version marker: {marker}")

planner_text = read_text(INTEGRATION / "executions" / "generic_planner.py")
if 'CONTRACT_VERSION = "1.7-rc6"' not in planner_text:
    fail("GenericExecutionPlanner.CONTRACT_VERSION must be 1.7-rc6")

real_text = read_text(INTEGRATION / "executions" / "generic_real.py")
if 'VERSION = "1.8-rc6"' not in real_text:
    fail("GenericExecutionEngine.VERSION must be 1.8-rc6")

manager_text = read_text(INTEGRATION / "executions" / "generic_manager.py")
if 'VERSION = "1.6-rc6"' not in manager_text:
    fail("SemanticExecutionManager.VERSION must be 1.6-rc6")
if "1.5-rc5" in manager_text:
    fail("Stale SemanticExecutionManager RC5 marker remains")

for path in ROOT.rglob("*.json"):
    if path.name.endswith(".example"):
        continue
    try:
        json.loads(read_text(path))
    except Exception as exc:
        fail(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")

for path in INTEGRATION.rglob("*.py"):
    try:
        compile(read_text(path), str(path), "exec")
    except Exception as exc:
        fail(f"Python syntax error {path.relative_to(ROOT)}: {exc}")

service_text = read_text(INTEGRATION / "services.yaml")
service_keys = re.findall(r"(?m)^([a-z0-9_]+):\s*$", service_text)
if len(service_keys) != 66:
    fail(f"Expected 66 service definitions, found {len(service_keys)}")
if len(set(service_keys)) != len(service_keys):
    fail("Duplicate service keys detected in services.yaml")
if "notifications.send" not in service_text:
    fail("services.yaml does not document notifications.send")

# Verify capability definitions and semantic actions without importing Home Assistant.
try:
    capability_tree = ast.parse(read_text(INTEGRATION / "capabilities" / "core.py"))
    capabilities: list[str] = []
    actions: list[str] = []
    confirmation: dict[str, bool] = {}
    for node in ast.walk(capability_tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id == "CapabilityDefinition":
            capability_id = keyword_literal(node, "capability_id")
            if isinstance(capability_id, str):
                capabilities.append(capability_id)
        elif node.func.id == "CapabilityAction":
            action_id = keyword_literal(node, "action_id")
            confirmation_required = keyword_literal(
                node, "confirmation_required", False
            )
            if isinstance(action_id, str):
                actions.append(action_id)
                confirmation[action_id] = bool(confirmation_required)

    if len(capabilities) != 7 or len(set(capabilities)) != 7:
        fail(f"Expected 7 unique capabilities, found {len(capabilities)}")
    if "notifications" not in capabilities:
        fail("Missing semantic notifications capability")
    if len(actions) != 15 or len(set(actions)) != 15:
        fail(f"Expected 15 unique semantic actions, found {len(actions)}")
    for action_id in ("notifications.snapshot", "notifications.send"):
        if action_id not in actions:
            fail(f"Missing semantic notification action: {action_id}")
    if confirmation.get("notifications.send") is not False:
        fail("notifications.send must not require confirmation")
    for action_id in ("garage.open", "garage.close", "openings.lock", "openings.unlock"):
        if confirmation.get(action_id) is not True:
            fail(f"{action_id} must require explicit confirmation")
except Exception as exc:
    fail(f"Semantic capability/action catalogue check failed: {exc}")

# Verify canonical request contracts and the notification parameter envelope.
try:
    contract_tree = ast.parse(
        read_text(INTEGRATION / "executions" / "action_contracts.py")
    )
    contracts: dict[str, dict[str, object]] = {}
    for node in ast.walk(contract_tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "CanonicalActionExecutionContract"
        ):
            continue
        action_id = keyword_literal(node, "action_id")
        if isinstance(action_id, str):
            contracts[action_id] = {
                "allowed": keyword_literal(node, "allowed_parameter_keys", ()),
                "required": keyword_literal(node, "required_parameter_keys", ()),
            }

    if len(contracts) != 9:
        fail(f"Expected 9 unique canonical real contracts, found {len(contracts)}")
    notification_contract = contracts.get("notifications.send")
    if notification_contract is None:
        fail("Missing canonical notifications.send contract")
    else:
        if notification_contract["allowed"] != ("message", "title"):
            fail("notifications.send allowed parameters must be message,title")
        if notification_contract["required"] != ("message",):
            fail("notifications.send required parameters must contain only message")

    action_contract_text = read_text(
        INTEGRATION / "executions" / "action_contracts.py"
    )
    for marker in (
        "parameters.message must be a non-empty string.",
        "parameters.title must be a string or null.",
    ):
        if marker not in action_contract_text:
            fail(f"Missing notification request guard: {marker}")
except Exception as exc:
    fail(f"Canonical action contract check failed: {exc}")

provider_result_text = read_text(INTEGRATION / "providers" / "execution.py")
if 'verification_scope: str = "effect"' not in provider_result_text:
    fail("ProviderExecutionResult default verification scope must remain effect")

notification_provider_text = read_text(INTEGRATION / "providers" / "notifications.py")
for marker in (
    'return "provider.core.notifications"',
    'return ("notifications",)',
    '"notify", "send_message"',
    'verification_scope="dispatch"',
    '"delivery_receipt_claimed": False',
    '"read_receipt_claimed": False',
):
    if marker not in notification_provider_text:
        fail(f"Missing notification provider contract marker: {marker}")

collector_text = read_text(
    INTEGRATION / "qualification" / "execution_qualification_collector.py"
)
for marker in (
    'provider_result.get("verification_scope") or "effect"',
    'hardware_verified = verification_scope != "dispatch"',
    "framework_verified=True",
):
    if marker not in collector_text:
        fail(f"Missing dispatch qualification guard: {marker}")

evidence_text = read_text(
    INTEGRATION / "qualification" / "execution_evidence.py"
)
for marker in (
    "hardware_verified=self.hardware_verified",
    "framework_verified=self.framework_verified",
):
    if marker not in evidence_text:
        fail(f"Evidence merge does not preserve verification flags: {marker}")
if '"message"' in evidence_text or '"title"' in evidence_text:
    fail("Persistent ExecutionEvidence must not contain message/title payload fields")

release_scope_text = read_text(INTEGRATION / "release_scope.py")
notification_scope = re.search(
    r'"notifications":\s*DomainReleaseState\(\s*"notifications",\s*'
    r"LifecycleStage\.ACTIVE,\s*True,",
    release_scope_text,
)
if notification_scope is None:
    fail("Notifications must be active and in RC6 release scope")

current_doc_markers = {
    ROOT / "README.md": ("1.0.0-rc6", "LIVE VERIFIED", "notifications.send"),
    ROOT / "REPOSITORY_STATUS.md": (
        "1.0.0-rc6",
        "WP-4.7.13.1",
        "17 active domains",
    ),
    ROOT / "docs" / "FEATURE_MATRIX.md": (
        "1.0.0-rc6",
        "Notifications",
        "LIVE VERIFIED RC6",
    ),
    ROOT / "docs" / "ROADMAP.md": (
        "RC6",
        "Notification routing / announcements",
        "Climate / temperature semantics",
    ),
    ROOT / "docs" / "RELEASE_STATUS.md": (
        "1.0.0-rc6",
        "LIVE VERIFIED",
        "PUBLICATION PENDING",
    ),
    INTEGRATION / "README.md": ("1.0.0-rc6", "notifications.send"),
    INTEGRATION / "docs" / "FEATURE_MATRIX.md": (
        "1.0.0-rc6",
        "LIVE VERIFIED RC6",
    ),
}
for path, markers in current_doc_markers.items():
    if not path.exists():
        continue
    text = read_text(path)
    for marker in markers:
        if marker not in text:
            fail(f"{path.relative_to(ROOT)} missing RC6 marker: {marker}")

checksum_file = ROOT / "checksums" / "rc6_source.sha256"
if not checksum_file.exists():
    fail("Missing RC6 source checksum catalogue: checksums/rc6_source.sha256")
else:
    checksum_paths: list[str] = []
    for line_number, line in enumerate(
        read_text(checksum_file).splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            expected_hash, rel = line.split(maxsplit=1)
        except ValueError:
            fail(f"Malformed checksum line {line_number}")
            continue
        rel = rel.strip()
        checksum_paths.append(rel)
        path = ROOT / rel
        if not path.exists():
            fail(f"Checksum path missing: {rel}")
            continue
        actual = normalized_sha256(path)
        if actual != expected_hash:
            fail(f"Checksum mismatch: {rel}")

    expected_source_paths = sorted(
        path.relative_to(ROOT).as_posix()
        for path in INTEGRATION.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    if checksum_paths != expected_source_paths:
        fail("RC6 checksum catalogue must list every integration file exactly once")

if (ROOT / "hacs.json").exists():
    fail("hacs.json is active, but this candidate remains pre-publication")

if ERRORS:
    print("Red Queen repository verification FAILED")
    for error in ERRORS:
        print(f"- {error}")
    sys.exit(1)

print("Red Queen repository verification PASS")
print(
    f"- integration: {manifest.get('name')} {manifest.get('version')} "
    f"({manifest.get('domain')})"
)
print(f"- services: {len(service_keys)}")
print("- capabilities: 7")
print("- semantic actions: 15")
print("- canonical real contracts: 9")
print("- notifications: dispatch-scoped qualification guard PASS")
print("- RC6 LF-normalized source checksums: PASS")
print(f"- Git whitespace hygiene: {git_whitespace_status}")
print("- active HACS metadata: intentionally disabled")
