#!/usr/bin/env python3
"""Static repository checks for the Red Queen 1.0.0-rc10 candidate."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import yaml

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
        parent = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--verify", "HEAD^"],
            capture_output=True,
            text=True,
            check=False,
        )
        if parent.returncode != 0:
            fail(
                "Git parent commit unavailable for whitespace verification; "
                "checkout with fetch-depth >= 2"
            )
            return "FAILED"
        command = [
            "git",
            "-C",
            str(ROOT),
            "diff",
            "--check",
            "HEAD^",
            "HEAD",
            "--",
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
    ROOT / "docs" / "RC10_CANDIDATE_VALIDATION.md",
    ROOT / "configuration" / "notification_targets.yaml",
    ROOT / "configuration" / "plants.yaml",
    INTEGRATION / "__init__.py",
    INTEGRATION / "binary_sensor.py",
    INTEGRATION / "button.py",
    INTEGRATION / "cover.py",
    INTEGRATION / "light.py",
    INTEGRATION / "lock.py",
    INTEGRATION / "native_execution.py",
    INTEGRATION / "manifest.json",
    INTEGRATION / "RELEASE.json",
    INTEGRATION / "services.yaml",
    INTEGRATION / "translations" / "en.json",
    INTEGRATION / "translations" / "de.json",
    INTEGRATION / "domain" / "notification.py",
    INTEGRATION / "providers" / "notifications.py",
    INTEGRATION / "providers" / "plants.py",
    INTEGRATION / "plant_care.py",
    INTEGRATION / "domain" / "plant.py",
    INTEGRATION / "docs" / "RELEASE_NOTES_1.0.0-rc10.md",
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
    "version": "1.0.0-rc10",
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
    "version": "1.0.0-rc10",
    "candidate": "rc10",
    "development_baseline_version": "1.36.0",
    "release_baseline": "WP-4.7.16.0",
    "canonical_execution_api_version": "1.0",
    "canonical_execution_contract": "2.2-rc10",
}
for key, value in expected_release.items():
    if release.get(key) != value:
        fail(f"RELEASE.json {key!r}: expected {value!r}, got {release.get(key)!r}")

const_text = read_text(INTEGRATION / "const.py")
for marker in (
    'DEVELOPMENT_BASELINE_VERSION = "1.36.0"',
    'RELEASE_BASELINE = "WP-4.7.16.0"',
    'GENERIC_EXECUTION_CONTRACT_VERSION = "2.1-rc10"',
    'GENERIC_REAL_EXECUTION_VERSION = "2.2-rc10"',
    'CANONICAL_EXECUTION_CONTRACT_VERSION = "2.2-rc10"',
    '"lock",',
):
    if marker not in const_text:
        fail(f"Missing release/version marker: {marker}")

planner_text = read_text(INTEGRATION / "executions" / "generic_planner.py")
if 'CONTRACT_VERSION = "2.1-rc10"' not in planner_text:
    fail("GenericExecutionPlanner.CONTRACT_VERSION must be 2.1-rc10")

real_text = read_text(INTEGRATION / "executions" / "generic_real.py")
if 'VERSION = "2.2-rc10"' not in real_text:
    fail("GenericExecutionEngine.VERSION must be 2.2-rc10")

manager_text = read_text(INTEGRATION / "executions" / "generic_manager.py")
if 'VERSION = "2.0-rc10"' not in manager_text:
    fail("SemanticExecutionManager.VERSION must be 2.0-rc10")

release_candidate_text = read_text(INTEGRATION / "release_candidate.py")
if 'f"Release Candidate {cls.CANDIDATE.removeprefix(\'rc\')}"' not in (
    release_candidate_text
):
    fail("Release phase name must derive from the explicit RC10 candidate label")
if '"phase_name": "Release Candidate 6"' in release_candidate_text:
    fail("Stale RC6 release phase name remains active")

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
if len(service_keys) != 67:
    fail(f"Expected 67 service definitions, found {len(service_keys)}")
if len(set(service_keys)) != len(service_keys):
    fail("Duplicate service keys detected in services.yaml")
for action_id in (
    "covers.blades_open",
    "covers.blades_close",
    "openings.release",
    "notifications.send",
    "notifications.announce",
    "notifications.route",
    "plants.record_watering",
):
    if action_id not in service_text:
        fail(f"services.yaml does not document {action_id}")

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

    if len(capabilities) != 8 or len(set(capabilities)) != 8:
        fail(f"Expected 8 unique capabilities, found {len(capabilities)}")
    if "notifications" not in capabilities:
        fail("Missing semantic notifications capability")
    if len(actions) != 22 or len(set(actions)) != 22:
        fail(f"Expected 22 unique semantic actions, found {len(actions)}")
    for action_id in ("plants.snapshot", "plants.record_watering"):
        if action_id not in actions:
            fail(f"Missing semantic Plant Care action: {action_id}")
    for action_id in (
        "notifications.snapshot",
        "notifications.send",
        "notifications.announce",
        "notifications.route",
    ):
        if action_id not in actions:
            fail(f"Missing semantic notification action: {action_id}")
    for action_id in (
        "notifications.send",
        "notifications.announce",
        "notifications.route",
        "covers.blades_open",
        "covers.blades_close",
        "plants.record_watering",
    ):
        if confirmation.get(action_id) is not False:
            fail(f"{action_id} must not require confirmation")
    for action_id in (
        "garage.open",
        "garage.close",
        "openings.lock",
        "openings.unlock",
        "openings.release",
    ):
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

    if len(contracts) != 15:
        fail(f"Expected 15 unique canonical real contracts, found {len(contracts)}")
    plant_contract = contracts.get("plants.record_watering")
    if plant_contract is None:
        fail("Missing canonical plants.record_watering contract")
    elif plant_contract["allowed"] != ():
        fail("plants.record_watering must not accept parameters")
    for action_id in ("covers.blades_open", "covers.blades_close"):
        blade_contract = contracts.get(action_id)
        if blade_contract is None:
            fail(f"Missing canonical {action_id} contract")
        elif blade_contract["allowed"] != ():
            fail(f"{action_id} must not accept parameters")
    release_contract = contracts.get("openings.release")
    if release_contract is None:
        fail("Missing canonical openings.release contract")
    elif release_contract["allowed"] != ():
        fail("openings.release must not accept parameters")
    notification_contract = contracts.get("notifications.send")
    if notification_contract is None:
        fail("Missing canonical notifications.send contract")
    else:
        if notification_contract["allowed"] != ("message", "title"):
            fail("notifications.send allowed parameters must be message,title")
        if notification_contract["required"] != ("message",):
            fail("notifications.send required parameters must contain only message")

    announcement_contract = contracts.get("notifications.announce")
    if announcement_contract is None:
        fail("Missing canonical notifications.announce contract")
    else:
        if announcement_contract["allowed"] != ("message", "level"):
            fail("notifications.announce allowed parameters must be message,level")
        if announcement_contract["required"] != ("message",):
            fail("notifications.announce required parameters must contain only message")

    route_contract = contracts.get("notifications.route")
    if route_contract is None:
        fail("Missing canonical notifications.route contract")
    else:
        if route_contract["allowed"] != (
            "message",
            "title",
            "priority",
            "profile",
            "source",
            "category",
        ):
            fail("notifications.route allowed parameter envelope changed")
        if route_contract["required"] != ("message",):
            fail("notifications.route required parameters must contain only message")

    action_contract_text = read_text(
        INTEGRATION / "executions" / "action_contracts.py"
    )
    for marker in (
        "parameters.message must be a non-empty string.",
        "parameters.title must be a string or null.",
        "parameters.level must be one of: info, notice, warning, alarm.",
        "parameters.priority must be one of:",
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
    '"tts",\n                    "speak"',
    '"media_player",\n                    "play_media"',
    '"announce": True',
    '"restore_strategy": "sonos_native_announce"',
    'f"media-source://tts/{target.tts_entity_id}?{query}"',
    '_ACTION_ANNOUNCE = "notifications.announce"',
    '_ACTION_ROUTE = "notifications.route"',
    'verification_scope="dispatch"',
    '"delivery_receipt_claimed": False',
    '"read_receipt_claimed": False',
    '"playback_heard_claimed": False',
):
    if marker not in notification_provider_text:
        fail(f"Missing notification provider contract marker: {marker}")
if '"sonos",\n                        "snapshot"' in notification_provider_text:
    fail("Native Sonos announcements must not take a second framework snapshot")
if '"sonos",\n                            "restore"' in notification_provider_text:
    fail("Native Sonos announcements must not send a second framework restore")

cover_provider_text = read_text(INTEGRATION / "providers" / "core.py")
cover_capability_text = read_text(INTEGRATION / "executions" / "capability.py")
for marker in (
    '"covers.blades_open"',
    '"covers.blades_close"',
    'verification_scope="dispatch"',
    '"blade_position_confirmed": False',
):
    if marker not in cover_provider_text:
        fail(f"Missing canonical blade provider marker: {marker}")
for marker in (
    'strategy="dispatch_scoped_blade_pulse"',
    'feedback_required=False',
    'idempotency="non_idempotent_dispatch"',
    'effect_confirmation=EffectConfirmationMode.NONE',
):
    if marker not in cover_capability_text:
        fail(f"Missing dispatch-scoped blade capability marker: {marker}")

for marker in (
    '"openings.release": "access.door_open"',
    '"Door opener dispatch requires a proven closed door."',
    '"door_release_confirmed": False',
    '"physical_opening_claimed": False',
    'verification_scope="dispatch"',
):
    if marker not in cover_provider_text:
        fail(f"Missing canonical door-opener provider marker: {marker}")
if 'strategy="confirmed_dispatch_scoped_momentary_pulse"' not in cover_capability_text:
    fail("Missing confirmed dispatch-scoped door-opener capability strategy")

collector_text = read_text(
    INTEGRATION / "qualification" / "execution_qualification_collector.py"
)
for marker in (
    'provider_result.get("verification_scope") or "effect"',
    'hardware_verified = verification_scope == "effect"',
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
    fail("Notifications must remain active in RC10 release scope")

plant_scope = re.search(
    r'"plants":\s*DomainReleaseState\(\s*"plants",\s*'
    r"LifecycleStage\.ACTIVE,\s*True,",
    release_scope_text,
)
if plant_scope is None:
    fail("Plant Care must be active in RC10 release scope")

plant_provider_text = read_text(INTEGRATION / "providers" / "plants.py")
for marker in (
    'return "provider.core.plants"',
    'return ("plants",)',
    'strategy": "persistent_verified_state_event"',
    'verification_scope="state"',
    '"hardware_effect_claimed": False',
    "SIGNAL_PLANTS_UPDATED",
):
    if marker not in plant_provider_text:
        fail(f"Missing Plant Care provider contract marker: {marker}")

plant_store_text = read_text(INTEGRATION / "plant_care.py")
for marker in ("NamedTemporaryFile", "os.fsync", "os.replace", "schema_version"):
    if marker not in plant_store_text:
        fail(f"Missing atomic Plant Care persistence marker: {marker}")

plant_button_text = read_text(INTEGRATION / "button.py")
for marker in (
    "class WNHFRecordPlantWateringButton",
    "async_execute_canonical",
    'action_id="plants.record_watering"',
    'f"wnhf_plant_water_{slug}"',
    '"physical_watering_claimed": False',
):
    if marker not in plant_button_text:
        fail(f"Missing native Plant Care button contract marker: {marker}")
if "engine.async_record_plant_watering" in plant_button_text:
    fail("Plant Care button must not bypass the canonical execution service")

native_execution_text = read_text(INTEGRATION / "native_execution.py")
for marker in (
    "SERVICE_EXECUTION_EXECUTE",
    "return_response=True",
    'payload.get("state") != "succeeded"',
    "raise HomeAssistantError(reason)",
):
    if marker not in native_execution_text:
        fail(f"Missing response-aware native execution marker: {marker}")

binary_sensor_text = read_text(INTEGRATION / "binary_sensor.py")
for marker in (
    "class WNHFNativeOpeningState",
    "house.enabled_openings",
    "room_device_info(engine, opening.room_id)",
    "BinarySensorDeviceClass.GARAGE_DOOR",
    "access_object_snapshot",
):
    if marker not in binary_sensor_text:
        fail(f"Missing native room opening marker: {marker}")

lock_text = read_text(INTEGRATION / "lock.py")
for marker in (
    "class WNHFDoorLockEntity",
    'action_id="openings.lock"',
    'action_id="openings.unlock"',
    "confirmed=True",
    "room_device_info(engine, opening.room_id)",
):
    if marker not in lock_text:
        fail(f"Missing native room lock marker: {marker}")

for marker in (
    "class WNHFCoverBladeButton",
    "class WNHFDoorReleaseButton",
    'action_id="openings.release"',
    '"native_button_press"',
):
    if marker not in plant_button_text:
        fail(f"Missing native room button marker: {marker}")

cover_entity_text = read_text(INTEGRATION / "cover.py")
for marker in (
    "class WNHFGarageDoorEntity",
    '"garage.open"',
    '"garage.close"',
    "CoverDeviceClass.GARAGE",
    "async_execute_canonical",
):
    if marker not in cover_entity_text:
        fail(f"Missing native garage/canonical cover marker: {marker}")

light_entity_text = read_text(INTEGRATION / "light.py")
for marker in (
    "async_execute_canonical",
    'action_id="lighting.turn_on"',
    'action_id="lighting.turn_off"',
):
    if marker not in light_entity_text:
        fail(f"Missing canonical native light marker: {marker}")

entity_text = read_text(INTEGRATION / "entity.py")
for marker in (
    "class WNHFPlantEntity",
    "room_id: str",
    "room_device_info(engine, room_id)",
):
    if marker not in entity_text:
        fail(f"Missing room-associated Plant Care entity marker: {marker}")
plant_entity_block = entity_text.split("class WNHFPlantEntity", 1)[1].split(
    "class WNHFSecurityEntity", 1
)[0]
if 'module_device_info("plants"' in plant_entity_block:
    fail("Plant Care entities must not remain attached to a central module device")

sensor_text = read_text(INTEGRATION / "sensor.py")
context_entity_block = sensor_text.split("class WNHFContext(", 1)[1].split(
    "class WNHFContextMessage", 1
)[0]
for marker in (
    '"full_snapshot_service": "wnhf.context_snapshot"',
    '"matched_count": snapshot.rule_snapshot.matched_count',
    '"scores": snapshot.scores.as_dict()',
):
    if marker not in context_entity_block:
        fail(f"Missing bounded Context entity marker: {marker}")
if "snapshot.as_dict()" in context_entity_block:
    fail("Native Context entity must not expose the unbounded full snapshot")

try:
    plant_registry = yaml.safe_load(
        read_text(ROOT / "configuration" / "plants.yaml")
    )
    plants = plant_registry.get("plants", [])
    if len(plants) != 13:
        fail(f"Reference Plant Care registry must contain 13 plants, found {len(plants)}")
    plant_ids = [item.get("id") for item in plants]
    if len(set(plant_ids)) != 13:
        fail("Reference Plant Care registry contains duplicate plant IDs")
    if any(item.get("moisture_sensor_entity_id") for item in plants):
        fail("RC10 reference plants must remain sensor-independent")
    intervals = {item.get("watering_interval_days") for item in plants}
    if intervals != {7, 14}:
        fail(f"Reference watering intervals changed: {sorted(intervals)}")
except Exception as exc:
    fail(f"Plant Care registry validation failed: {exc}")

try:
    registry_namespace = runpy.run_path(
        str(INTEGRATION / "domain" / "notification.py")
    )
    registry = registry_namespace["load_notification_registry"](
        ROOT / "configuration" / "notification_targets.yaml"
    )
    if len(registry.notification_targets) != 1:
        fail("Reference registry must contain one direct notification target")
    if len(registry.announcement_targets) != 2:
        fail("Reference registry must contain office and house announcements")
    if len(registry.notification_routes) != 1:
        fail("Reference registry must contain one native notification route")
    house_target = registry.announcement_targets.get("announcement.target.house")
    if house_target is None or house_target.tts_entity_id != "tts.google_translate_de_at":
        fail("Reference house announcement must use Google Translate de-at")
    if house_target is not None and house_target.levels["alarm"].volume != 0.55:
        fail("Reference alarm announcement volume must remain 0.55")
except Exception as exc:
    fail(f"Native notification registry validation failed: {exc}")

current_doc_markers = {
    ROOT / "README.md": (
        "1.0.0-rc10",
        "plants.record_watering",
        "Plant Care",
    ),
    ROOT / "REPOSITORY_STATUS.md": (
        "1.0.0-rc10",
        "WP-4.7.16.0",
        "Plant Care",
    ),
    ROOT / "docs" / "FEATURE_MATRIX.md": (
        "1.0.0-rc10",
        "plants.snapshot",
        "plants.record_watering",
        "Native room controls",
    ),
    ROOT / "docs" / "ROADMAP.md": (
        "RC10",
        "Semantic Plant Care",
        "Climate / temperature semantics",
    ),
    ROOT / "docs" / "RELEASE_STATUS.md": (
        "1.0.0-rc10",
        "LIVE VERIFIED",
    ),
    INTEGRATION / "README.md": (
        "1.0.0-rc10",
        "plants.record_watering",
        "native room surface",
    ),
    INTEGRATION / "docs" / "FEATURE_MATRIX.md": (
        "1.0.0-rc10",
        "plants.record_watering",
    ),
}
for path, markers in current_doc_markers.items():
    if not path.exists():
        continue
    text = read_text(path)
    for marker in markers:
        if marker not in text:
            fail(f"{path.relative_to(ROOT)} missing current RC10 marker: {marker}")

checksum_file = ROOT / "checksums" / "rc10_source.sha256"
if not checksum_file.exists():
    fail("Missing RC10 source checksum catalogue: checksums/rc10_source.sha256")
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
        fail("RC10 checksum catalogue must list every integration file exactly once")

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
print("- capabilities: 8")
print("- semantic actions: 22")
print("- canonical real contracts: 15")
print("- native room completeness: openings/locks/garage/blades PASS")
print("- native productive controls: canonical response bridge PASS")
print("- plant care: persistent watering and native button contract PASS")
print("- context entity: recorder-bounded attributes PASS")
print("- cover blades: dispatch-scoped canonical contract PASS")
print("- door opener: confirmed dispatch-scoped canonical contract PASS")
print("- native notification routing/announcements: static contract PASS")
print("- notifications: dispatch-scoped qualification guard PASS")
print("- RC10 LF-normalized source checksums: PASS")
print(f"- Git whitespace hygiene: {git_whitespace_status}")
print("- active HACS metadata: intentionally disabled")
