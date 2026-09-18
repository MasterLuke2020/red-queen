#!/usr/bin/env python3
"""Static repository checks for the current Red Queen release candidate."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
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
    """Hash text independently of LF/CRLF checkout conversion."""
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


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

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        details = result.stdout.strip() or result.stderr.strip()
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


def module_assignment(path: Path, name: str):
    tree = ast.parse(read_text(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                return ast.literal_eval(node.value)
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            return ast.literal_eval(node.value)
    return None


def class_assignment(path: Path, class_name: str, name: str):
    tree = ast.parse(read_text(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.Assign):
                    if any(
                        isinstance(t, ast.Name) and t.id == name
                        for t in item.targets
                    ):
                        return ast.literal_eval(item.value)
    return None


# ---------------------------------------------------------------------------
# Core metadata
# ---------------------------------------------------------------------------

try:
    manifest = json.loads(read_text(INTEGRATION / "manifest.json"))
except Exception as exc:
    fail(f"manifest.json invalid: {exc}")
    manifest = {}

try:
    release = json.loads(read_text(INTEGRATION / "RELEASE.json"))
except Exception as exc:
    fail(f"RELEASE.json invalid: {exc}")
    release = {}

required_release_fields = (
    "product_name",
    "version",
    "candidate",
    "development_baseline_version",
    "release_baseline",
    "canonical_execution_api_version",
    "canonical_execution_contract",
    "semantic_action_count",
    "canonical_real_action_count",
    "home_assistant_service_count",
    "candidate_status",
)
for field in required_release_fields:
    if field not in release:
        fail(f"RELEASE.json missing required field: {field}")

version = str(release.get("version") or "")
candidate = str(release.get("candidate") or "")
development_baseline = str(release.get("development_baseline_version") or "")
release_baseline = str(release.get("release_baseline") or "")
canonical_contract = str(release.get("canonical_execution_contract") or "")
expected_actions = int(release.get("semantic_action_count") or 0)
expected_real = int(release.get("canonical_real_action_count") or 0)
expected_services = int(release.get("home_assistant_service_count") or 0)
candidate_status = str(release.get("candidate_status") or "")
development_candidate = candidate_status == "development"

if release.get("product_name") != "Red Queen":
    fail("RELEASE.json product_name must be Red Queen")
if release.get("canonical_execution_api_version") != "1.0":
    fail("Canonical execution API must remain 1.0")
if not re.fullmatch(r"1\.0\.0-rc\d+", version):
    fail(f"Unexpected RC version format: {version!r}")
if not re.fullmatch(r"rc\d+", candidate):
    fail(f"Unexpected candidate format: {candidate!r}")
if candidate and not version.endswith(f"-{candidate}"):
    fail(f"Version {version!r} does not match candidate {candidate!r}")

expected_manifest = {
    "domain": "wnhf",
    "name": "Red Queen",
    "version": version,
    "documentation": "https://github.com/MasterLuke2020/red-queen#readme",
    "issue_tracker": "https://github.com/MasterLuke2020/red-queen/issues",
    "codeowners": ["@MasterLuke2020"],
}
for key, value in expected_manifest.items():
    if manifest.get(key) != value:
        fail(f"manifest {key!r}: expected {value!r}, got {manifest.get(key)!r}")


# ---------------------------------------------------------------------------
# Candidate-specific paths derived from metadata
# ---------------------------------------------------------------------------

root_validation = ROOT / "docs" / f"{candidate.upper()}_CANDIDATE_VALIDATION.md"
integration_validation = (
    INTEGRATION / "docs" / f"{candidate.upper()}_CANDIDATE_VALIDATION.md"
)
release_notes = INTEGRATION / "docs" / f"RELEASE_NOTES_{version}.md"
checksum_file = ROOT / "checksums" / f"{candidate}_source.sha256"

required_paths = [
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "REPOSITORY_STATUS.md",
    ROOT / "PUBLISHING_CHECKLIST.md",
    ROOT / "LICENSE",
    ROOT / ".github" / "CODEOWNERS",
    ROOT / ".github" / "workflows" / "hassfest.yml",
    ROOT / ".github" / "workflows" / "static-checks.yml",
    ROOT / "docs" / "CONFIGURATION.md",
    ROOT / "docs" / "FEATURE_MATRIX.md",
    ROOT / "docs" / "KNOWN_LIMITATIONS.md",
    ROOT / "docs" / "RELEASE_STATUS.md",
    ROOT / "docs" / "ROADMAP.md",
    root_validation,
    ROOT / "configuration" / "notification_targets.yaml",
    ROOT / "configuration" / "plants.yaml",
    checksum_file,
    INTEGRATION / "__init__.py",
    INTEGRATION / "binary_sensor.py",
    INTEGRATION / "button.py",
    INTEGRATION / "config_flow.py",
    INTEGRATION / "configuration.py",
    INTEGRATION / "configuration_diagnostics.py",
    INTEGRATION / "migration_repair.py",
    INTEGRATION / "cover.py",
    INTEGRATION / "light.py",
    INTEGRATION / "localization.py",
    INTEGRATION / "lock.py",
    INTEGRATION / "native_execution.py",
    INTEGRATION / "manifest.json",
    INTEGRATION / "RELEASE.json",
    INTEGRATION / "sensor.py",
    INTEGRATION / "services.py",
    INTEGRATION / "services.yaml",
    INTEGRATION / "translations" / "en.json",
    INTEGRATION / "translations" / "de.json",
    INTEGRATION / "domain" / "notification.py",
    INTEGRATION / "providers" / "notifications.py",
    INTEGRATION / "providers" / "plants.py",
    INTEGRATION / "plant_care.py",
    INTEGRATION / "domain" / "plant.py",
    INTEGRATION / "dashboard_model.py",
    INTEGRATION / "dashboard_binding.py",
    INTEGRATION / "dashboard_renderer.py",
    INTEGRATION / "dashboard_adapter.py",
    INTEGRATION / "dashboard_service.py",
    INTEGRATION / "docs" / "RC12_IMPLEMENTATION_PLAN.md",
    INTEGRATION / "docs" / "RC12_DASHBOARD_CONTRACT.md",
    INTEGRATION / "docs" / "RC12_ENTITY_BINDING.md",
    INTEGRATION / "docs" / "RC12_DASHBOARD_RENDERER.md",
    INTEGRATION / "docs" / "RC12_DASHBOARD_LIFECYCLE.md",
    INTEGRATION / "docs" / "RC12_DASHBOARD_GENERATION_SERVICE.md",
    INTEGRATION / "docs" / "RC12_CONFIGURATOR_DASHBOARD.md",
    INTEGRATION / "docs" / "RC12_DASHBOARD_POLISH.md",
    integration_validation,
    release_notes,
]
for path in required_paths:
    if not path.exists():
        fail(f"Missing required path: {path.relative_to(ROOT)}")

git_whitespace_status = verify_git_whitespace()


# ---------------------------------------------------------------------------
# Syntax / JSON / YAML
# ---------------------------------------------------------------------------

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

for path in (
    INTEGRATION / "services.yaml",
    ROOT / "configuration" / "plants.yaml",
    ROOT / "configuration" / "notification_targets.yaml",
):
    if not path.exists():
        continue
    try:
        yaml.safe_load(read_text(path))
    except Exception as exc:
        fail(f"Invalid YAML {path.relative_to(ROOT)}: {exc}")


# ---------------------------------------------------------------------------
# Version / contract consistency
# ---------------------------------------------------------------------------

const_path = INTEGRATION / "const.py"
planner_path = INTEGRATION / "executions" / "generic_planner.py"
real_path = INTEGRATION / "executions" / "generic_real.py"
manager_path = INTEGRATION / "executions" / "generic_manager.py"

try:
    if module_assignment(const_path, "DEVELOPMENT_BASELINE_VERSION") != development_baseline:
        fail("const.py development baseline does not match RELEASE.json")
    if module_assignment(const_path, "RELEASE_BASELINE") != release_baseline:
        fail("const.py release baseline does not match RELEASE.json")
    if module_assignment(const_path, "VERSION") != version:
        fail("const.py public version does not match RELEASE.json")
    if module_assignment(const_path, "RELEASE_CANDIDATE") != candidate:
        fail("const.py candidate marker does not match RELEASE.json")

    generic_execution = module_assignment(
        const_path, "GENERIC_EXECUTION_CONTRACT_VERSION"
    )
    generic_real = module_assignment(const_path, "GENERIC_REAL_EXECUTION_VERSION")
    canonical = module_assignment(
        const_path, "CANONICAL_EXECUTION_CONTRACT_VERSION"
    )
    if canonical != canonical_contract:
        fail("Canonical execution contract does not match RELEASE.json")
    if generic_real != canonical_contract:
        fail("Generic real execution version must match canonical contract")
    if class_assignment(
        planner_path, "GenericExecutionPlanner", "CONTRACT_VERSION"
    ) != generic_execution:
        fail("GenericExecutionPlanner.CONTRACT_VERSION mismatch")
    if class_assignment(real_path, "GenericExecutionEngine", "VERSION") != generic_real:
        fail("GenericExecutionEngine.VERSION mismatch")

    manager_version = class_assignment(
        manager_path, "SemanticExecutionManager", "VERSION"
    )
    if not isinstance(manager_version, str) or candidate not in manager_version:
        fail(
            "SemanticExecutionManager.VERSION must carry the current candidate marker"
        )
except Exception as exc:
    fail(f"Release/version consistency check failed: {exc}")

release_candidate_text = read_text(INTEGRATION / "release_candidate.py")
if "removeprefix('rc')" not in release_candidate_text:
    fail("Release phase name must derive from the explicit candidate label")


# ---------------------------------------------------------------------------
# Home Assistant services
# ---------------------------------------------------------------------------

service_text = read_text(INTEGRATION / "services.yaml")
service_keys = re.findall(r"(?m)^([a-z0-9_]+):\s*$", service_text)
if len(service_keys) != expected_services:
    fail(
        f"Expected {expected_services} service definitions from RELEASE.json, "
        f"found {len(service_keys)}"
    )
if len(set(service_keys)) != len(service_keys):
    fail("Duplicate service keys detected in services.yaml")
for service_id in (
    "execution_execute",
    "execution_dry_run",
    "configuration_snapshot",
    "plants_snapshot",
):
    if service_id not in service_keys:
        fail(f"Missing required Home Assistant service: {service_id}")


# ---------------------------------------------------------------------------
# Capability catalogue
# ---------------------------------------------------------------------------

try:
    capability_tree = ast.parse(
        read_text(INTEGRATION / "capabilities" / "core.py")
    )
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
    if len(actions) != expected_actions or len(set(actions)) != expected_actions:
        fail(
            f"Expected {expected_actions} unique semantic actions, "
            f"found {len(actions)}"
        )

    required_semantic_actions = {
        "lighting.turn_on",
        "lighting.turn_off",
        "covers.open",
        "covers.close",
        "covers.blades_open",
        "covers.blades_close",
        "garage.open",
        "garage.close",
        "garage.stop",
        "openings.lock",
        "openings.unlock",
        "openings.release",
        "notifications.send",
        "notifications.announce",
        "notifications.route",
        "plants.record_watering",
    }
    missing = sorted(required_semantic_actions.difference(actions))
    if missing:
        fail(f"Missing required semantic actions: {', '.join(missing)}")

    for action_id in (
        "garage.open",
        "garage.close",
        "garage.stop",
        "openings.lock",
        "openings.unlock",
        "openings.release",
    ):
        if confirmation.get(action_id) is not True:
            fail(f"{action_id} must require explicit confirmation")

    for action_id in (
        "covers.blades_open",
        "covers.blades_close",
        "notifications.send",
        "notifications.announce",
        "notifications.route",
        "plants.record_watering",
    ):
        if confirmation.get(action_id) is not False:
            fail(f"{action_id} must not require confirmation")
except Exception as exc:
    fail(f"Semantic capability/action catalogue check failed: {exc}")


# ---------------------------------------------------------------------------
# Canonical action contracts
# ---------------------------------------------------------------------------

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
                "allowed": keyword_literal(
                    node, "allowed_parameter_keys", ()
                ),
                "required": keyword_literal(
                    node, "required_parameter_keys", ()
                ),
            }

    if len(contracts) != expected_real:
        fail(
            f"Expected {expected_real} canonical real contracts, "
            f"found {len(contracts)}"
        )

    for action_id in (
        "garage.stop",
        "covers.blades_open",
        "covers.blades_close",
        "openings.release",
        "plants.record_watering",
    ):
        contract = contracts.get(action_id)
        if contract is None:
            fail(f"Missing canonical {action_id} contract")
        elif contract["allowed"] != ():
            fail(f"{action_id} must not accept parameters")

    notification = contracts.get("notifications.send")
    if notification is None:
        fail("Missing canonical notifications.send contract")
    else:
        if notification["allowed"] != ("message", "title"):
            fail("notifications.send allowed parameters must be message,title")
        if notification["required"] != ("message",):
            fail("notifications.send must require message")

    announcement = contracts.get("notifications.announce")
    if announcement is None:
        fail("Missing canonical notifications.announce contract")
    else:
        if announcement["allowed"] != ("message", "level"):
            fail("notifications.announce allowed parameters must be message,level")
        if announcement["required"] != ("message",):
            fail("notifications.announce must require message")
except Exception as exc:
    fail(f"Canonical action contract check failed: {exc}")


# ---------------------------------------------------------------------------
# RC11 safety / managed-configuration invariants
# ---------------------------------------------------------------------------

configuration_text = read_text(INTEGRATION / "configuration.py")
for marker in (
    "configuration_backups",
    "managed_files",
    "uninitialized",
    "manual",
    "managed",
    "os.replace",
    "yaml.safe_dump",
    "rollback",
    "object_options",
    "get_object",
    "update_object",
    "set_object_enabled",
    "delete_object",
    "A stable semantic object ID cannot be changed during maintenance.",
    "Room is still referenced and cannot be deleted",
):
    if marker not in configuration_text:
        fail(f"Missing managed-configuration safety marker: {marker}")

config_flow_text = read_text(INTEGRATION / "config_flow.py")
for marker in (
    "async_step_add_room",
    "async_step_add_light",
    "async_step_add_cover",
    "async_step_add_opening",
    "async_step_add_window",
    "async_step_add_sliding_door",
    "async_step_add_door",
    "async_step_add_garage_door",
    "async_step_add_plant",
    "async_step_manage",
    "async_step_manage_room",
    "async_step_manage_light",
    "async_step_manage_cover",
    "async_step_manage_opening",
    "async_step_manage_plant",
    "async_step_edit_room",
    "async_step_edit_light",
    "async_step_edit_cover",
    "async_step_edit_door",
    "async_step_edit_garage_door",
    "async_step_edit_plant",
    "async_step_delete_confirm",
):
    if marker not in config_flow_text:
        fail(f"Missing managed configurator flow: {marker}")

provider_text = read_text(INTEGRATION / "providers" / "core.py")
capability_text = read_text(INTEGRATION / "executions" / "capability.py")
cover_text = read_text(INTEGRATION / "cover.py")
button_text = read_text(INTEGRATION / "button.py")

for marker in (
    '"garage.stop"',
    "Garage STOP is permitted only while the door is",
    'verification_scope="dispatch"',
):
    if marker not in provider_text:
        fail(f"Missing guarded garage STOP provider marker: {marker}")

for marker in (
    "resolve_garage_stop",
    'strategy="guarded_dedicated_stop_pulse"',
    'provider_id="provider.core.garage.stop"',
):
    if marker not in capability_text:
        fail(f"Missing garage STOP execution capability marker: {marker}")

if "CoverEntityFeature.STOP" not in cover_text or "garage.stop" not in cover_text:
    fail("Native garage cover must expose guarded STOP support")
if "CoverEntityFeature.OPEN_TILT" in cover_text or "CoverEntityFeature.CLOSE_TILT" in cover_text:
    fail("Native cover must not expose ambiguous tilt controls in RC11")

for marker in (
    "covers.blades_open",
    "covers.blades_close",
    "WNHFRecordPlantWateringButton",
):
    if marker not in button_text:
        fail(f"Missing native RC11 button marker: {marker}")

native_execution_text = read_text(INTEGRATION / "native_execution.py")
for marker in (
    "SERVICE_EXECUTION_EXECUTE",
    "return_response=True",
    'payload.get("state") not in {"succeeded", "no_action", "in_progress"}',
    "raise HomeAssistantError",
):
    if marker not in native_execution_text:
        fail(f"Missing response-aware native execution marker: {marker}")


# ---------------------------------------------------------------------------
# Localization / translations
# ---------------------------------------------------------------------------

try:
    de = json.loads(read_text(INTEGRATION / "translations" / "de.json"))
    menu = de["options"]["step"]["init"]["menu_options"]
    for key in (
        "status",
        "add_room",
        "add_light",
        "add_cover",
        "add_opening",
        "add_plant",
        "manage",
        "diagnostics",
        "migration_repair",
        "dashboard",
    ):
        if key not in menu:
            fail(f"German configurator menu missing option: {key}")

    door_message = de["exceptions"]["door_open_lock_blocked"]["message"]
    if "erst bei geschlossener Tür möglich" not in door_message:
        fail("German open-door lock guard translation is missing")
except Exception as exc:
    fail(f"German translation structure check failed: {exc}")



# ---------------------------------------------------------------------------
# RC12 generated dashboard invariants
# ---------------------------------------------------------------------------

dashboard_model_text = read_text(INTEGRATION / "dashboard_model.py")
dashboard_binding_text = read_text(INTEGRATION / "dashboard_binding.py")
dashboard_renderer_text = read_text(INTEGRATION / "dashboard_renderer.py")
dashboard_adapter_text = read_text(INTEGRATION / "dashboard_adapter.py")
dashboard_service_text = read_text(INTEGRATION / "dashboard_service.py")

for marker in (
    'DASHBOARD_CONTRACT_VERSION = "1.0"',
    "build_dashboard_model",
    "DashboardModel",
):
    if marker not in dashboard_model_text:
        fail(f"Missing RC12 dashboard-model marker: {marker}")

for marker in (
    'DASHBOARD_BINDING_CONTRACT_VERSION = "1.0"',
    "async_get_entity_id",
    "resolve_dashboard_bindings",
):
    if marker not in dashboard_binding_text:
        fail(f"Missing RC12 dashboard-binding marker: {marker}")

for marker in (
    'DASHBOARD_RENDERER_CONTRACT_VERSION = "1.0"',
    "render_dashboard",
    '"subview": True',
):
    if marker not in dashboard_renderer_text:
        fail(f"Missing RC12 dashboard-renderer marker: {marker}")

for marker in (
    'DASHBOARD_ADAPTER_CONTRACT_VERSION = "1.0"',
    'DEFAULT_DASHBOARD_ID = "red-queen"',
    "async_register_built_in_panel",
    "async_save",
):
    if marker not in dashboard_adapter_text:
        fail(f"Missing RC12 dashboard-adapter marker: {marker}")

for marker in (
    'DASHBOARD_GENERATION_CONTRACT_VERSION = "1.0"',
    "async_preview",
    "async_apply",
    "resolve_dashboard_bindings",
):
    if marker not in dashboard_service_text:
        fail(f"Missing RC12 dashboard-service marker: {marker}")

if '"dashboard"' not in config_flow_text or "async_step_dashboard" not in config_flow_text:
    fail("Configurator must expose the RC12 dashboard lifecycle step")

for marker in (
    "_finish_dashboard",
    '"dashboard_created"',
    '"dashboard_updated"',
    'description_placeholders={"dashboard_path": dashboard_path}',
):
    if marker not in config_flow_text:
        fail(f"Missing RC13 dashboard flow-completion marker: {marker}")



# ---------------------------------------------------------------------------
# RC13 commissioning diagnostics / dashboard source freshness
# ---------------------------------------------------------------------------

configuration_diagnostics_text = read_text(
    INTEGRATION / "configuration_diagnostics.py"
)
for marker in (
    'CONFIGURATION_DIAGNOSTICS_CONTRACT_VERSION = "1.0"',
    "async_diagnose_configured_entities",
    "ConfiguredEntityIssue",
    "ConfigurationDiagnosticsReport",
    "STATE_UNAVAILABLE",
    "STATE_UNKNOWN",
    "disabled_by",
    "async_add_executor_job",
):
    if marker not in configuration_diagnostics_text:
        fail(f"Missing RC13 configuration diagnostics marker: {marker}")

for marker in (
    "expected_source_registry_sha256",
    "source_outdated",
    "current_source_sha",
):
    if marker not in dashboard_adapter_text:
        fail(f"Missing RC13 dashboard source-freshness marker: {marker}")

for marker in (
    "async_step_diagnostics",
    "async_diagnose_configured_entities",
    "dashboard_refresh_recommended",
):
    if marker not in config_flow_text:
        fail(f"Missing RC13 Configurator diagnostics marker: {marker}")

# ---------------------------------------------------------------------------
# RC14 read-only migration / repair preview
# ---------------------------------------------------------------------------

migration_repair_text = read_text(INTEGRATION / "migration_repair.py")
for marker in (
    'MIGRATION_REPAIR_PREVIEW_CONTRACT_VERSION = "1.0"',
    "MigrationRepairFinding",
    "MigrationRepairPreview",
    "async_build_migration_repair_preview",
    '"duplicate_semantic_id"',
    '"orphan_room_reference"',
    '"registry_validation_error"',
    "proposed_managed_files",
    "write_performed=False",
):
    if marker not in migration_repair_text:
        fail(f"Missing RC14 migration/repair preview marker: {marker}")

for forbidden in (
    "os.replace",
    "_write_transaction",
    "create_managed_base(",
    "update_object(",
    "delete_object(",
    "set_object_enabled(",
):
    if forbidden in migration_repair_text:
        fail(
            "RC14 WP14.1 migration/repair preview must remain read-only; "
            f"found forbidden mutation marker: {forbidden}"
        )

for marker in (
    "async_step_migration_repair",
    "async_build_migration_repair_preview",
    '"migration_repair"',
):
    if marker not in config_flow_text:
        fail(f"Missing RC14 Configurator migration/repair marker: {marker}")

for language in ("de", "en"):
    translation = json.loads(
        read_text(INTEGRATION / "translations" / f"{language}.json")
    )
    migration_description = (
        translation.get("options", {})
        .get("step", {})
        .get("migration_repair", {})
        .get("description", "")
    )
    if "\\n" in migration_description:
        fail(
            "RC14 migration/repair translation contains literal newline escapes: "
            f"{language}"
        )
    if "\n" not in migration_description:
        fail(
            "RC14 migration/repair translation must contain real line breaks: "
            f"{language}"
        )

# ---------------------------------------------------------------------------
# RC14 WP14.2 controlled manual -> managed adoption
# ---------------------------------------------------------------------------

configuration_text = read_text(INTEGRATION / "configuration.py")
for marker in (
    "MANAGED_REGISTRY_FILES",
    "registry_bundle_sha256",
    "def adopt_manual_registry(",
    "expected_source_sha256",
    "Manual registry source changed after preview",
    "Manual registry source changed after validation",
    'action="adopt_manual_registry"',
    "Configuration backup failed; no files were changed",
    "filename == CONFIGURATOR_MANIFEST_FILE",
):
    if marker not in configuration_text:
        fail(f"Missing RC14 WP14.2 configuration invariant: {marker}")

for marker in (
    "ownership_marker_conflict",
    "manager.manifest_path.is_file()",
    "registry_bundle_sha256",
):
    if marker not in migration_repair_text:
        fail(f"Missing RC14 WP14.2 preview invariant: {marker}")

for marker in (
    "CONF_PREPARE_MIGRATION",
    "async_step_migration_repair_confirm",
    "_pending_migration_sha256",
    "manager.adopt_manual_registry",
    "_finish_migration",
    '"registry_mode"] = CONFIGURATOR_MODE_MANAGED',
    '"last_configuration_backup_path"',
    '"last_migration_source_sha256"',
):
    if marker not in config_flow_text:
        fail(f"Missing RC14 WP14.2 Configurator invariant: {marker}")

# ---------------------------------------------------------------------------
# Reference configuration regression
# ---------------------------------------------------------------------------

try:
    plant_registry = yaml.safe_load(
        read_text(ROOT / "configuration" / "plants.yaml")
    )
    plants = plant_registry.get("plants", [])
    if len(plants) != 13:
        fail(
            f"Reference Plant Care registry must contain 13 plants, "
            f"found {len(plants)}"
        )
    plant_ids = [item.get("id") for item in plants]
    if len(set(plant_ids)) != len(plant_ids):
        fail("Reference Plant Care registry contains duplicate plant IDs")
except Exception as exc:
    fail(f"Reference Plant Care registry validation failed: {exc}")


# ---------------------------------------------------------------------------
# Repository documentation consistency
# ---------------------------------------------------------------------------

if development_candidate:
    # During an active RC branch the published root documentation intentionally
    # remains on the last released candidate until candidate freeze. RC13-specific
    # scope/validation documents and checksums are required separately above.
    current_doc_markers = {
        ROOT / "docs" / "ROADMAP.md": (
            "Managed configuration",
        ),
        INTEGRATION / "README.md": (
            "garage.stop",
            "managed configurator",
        ),
    }
else:
    current_doc_markers = {
        ROOT / "README.md": (
            version,
            development_baseline,
            release_baseline,
            "garage.stop",
        ),
        ROOT / "REPOSITORY_STATUS.md": (
            version,
            release_baseline,
            str(expected_actions),
            str(expected_real),
            str(expected_services),
        ),
        ROOT / "docs" / "FEATURE_MATRIX.md": (
            version,
            "garage.stop",
            "Configuration",
        ),
        ROOT / "docs" / "RELEASE_STATUS.md": (
            version,
            "LIVE VERIFIED",
        ),
        ROOT / "docs" / "ROADMAP.md": (
            candidate.upper(),
            "Managed configuration",
        ),
        INTEGRATION / "README.md": (
            version,
            "garage.stop",
            "managed configurator",
        ),
        INTEGRATION / "docs" / "FEATURE_MATRIX.md": (
            version,
            "garage.stop",
        ),
    }
for path, markers in current_doc_markers.items():
    if not path.exists():
        continue
    text = read_text(path)
    for marker in markers:
        if marker not in text:
            fail(
                f"{path.relative_to(ROOT)} missing current candidate marker: "
                f"{marker}"
            )


# ---------------------------------------------------------------------------
# LF-normalized integration source checksum catalogue
# ---------------------------------------------------------------------------

if not checksum_file.exists():
    fail(
        f"Missing source checksum catalogue: "
        f"{checksum_file.relative_to(ROOT)}"
    )
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
        fail(
            f"{candidate.upper()} checksum catalogue must list every "
            "integration file exactly once"
        )


# ---------------------------------------------------------------------------
# Publication boundary
# ---------------------------------------------------------------------------

if (ROOT / "hacs.json").exists():
    fail("hacs.json is active, but this candidate remains pre-publication")


if ERRORS:
    print("Red Queen repository verification FAILED")
    for error in ERRORS:
        print(f"- {error}")
    sys.exit(1)

print("Red Queen repository verification PASS")
print(f"- integration: {manifest.get('name')} {version} ({manifest.get('domain')})")
print(f"- development baseline: {development_baseline} / {release_baseline}")
print(f"- candidate status: {candidate_status}")
print(f"- services: {len(service_keys)}")
print("- capabilities: 8")
print(f"- semantic actions: {expected_actions}")
print(f"- canonical real contracts: {expected_real}")
print("- managed configuration: ownership/transaction/maintenance invariants PASS")
print("- garage STOP: guarded canonical dispatch contract PASS")
print("- native cover UX: directional/no-tilt contract PASS")
print("- generated dashboard: model/binding/renderer/lifecycle invariants PASS")
print("- dashboard configurator: explicit create/update lifecycle PASS")
print("- commissioning diagnostics/dashboard freshness: PASS")
print("- RC14 migration/repair preview: read-only invariants PASS")
print("- RC14 manual adoption: SHA/backup/confirm/rollback invariants PASS")
print("- dashboard OptionsFlow completion: reload-safe PASS")
print("- translations/configurator menu structure: PASS")
print(f"- {candidate.upper()} LF-normalized source checksums: PASS")
print(f"- Git whitespace hygiene: {git_whitespace_status}")
print("- active HACS metadata: intentionally disabled")
