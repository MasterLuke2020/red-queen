"""Constants for Red Queen (technical Home Assistant domain: wnhf)."""

from __future__ import annotations

DOMAIN = "wnhf"
PRODUCT_NAME = "Red Queen"
DEVELOPMENT_NAME = "WNHF"
DEVELOPMENT_BASELINE_VERSION = "1.31.0"
RELEASE_BASELINE = "WP-4.7.12.1"
VERSION = "1.0.0-rc5"

DATA_ENGINE = "engine"

REGISTRY_ROOT = ("wnhf", "house", "registry")
ROOMS_FILE = "rooms.yaml"
LIGHTS_FILE = "lights.yaml"

SERVICE_LIGHTING_ALL_OFF = "lighting_all_off"
SERVICE_LIGHTING_ROOM_OFF = "lighting_room_off"
SERVICE_LIGHTING_OBJECT_OFF = "lighting_object_off"
SERVICE_RELOAD_REGISTRY = "reload_registry"

ATTR_ROOM_ID = "room_id"
ATTR_LIGHT_ID = "light_id"

EVENT_REGISTRY_LOADED = "wnhf_registry_loaded"


# Entity platforms exposed by the YAML-configured integration.
PLATFORMS = ("binary_sensor", "sensor", "cover", "light")

# Dispatcher signal emitted after a successful registry reload.
SIGNAL_REGISTRY_RELOADED = "wnhf_registry_reloaded"


# Diagnostics
MODULE_CORE = "core"
MODULE_LIGHTING = "lighting"
MODULE_DIAGNOSTICS = "diagnostics"

CAPABILITY_HOUSE_MODEL = "house_model"
CAPABILITY_LIGHTING = "lighting"
CAPABILITY_DIAGNOSTICS = "diagnostics"


SIGNAL_PERFORMANCE_UPDATED = "wnhf_performance_updated"

ACTION_REGISTRY_RELOAD = "registry_reload"
ACTION_LIGHTING_ALL_OFF = "lighting_all_off"
ACTION_LIGHTING_ROOM_OFF = "lighting_room_off"
ACTION_LIGHTING_OBJECT_OFF = "lighting_object_off"


# Registry Explorer
SERVICE_LIST_REGISTRY = "list_registry"
SERVICE_GET_OBJECT = "get_object"

ATTR_REGISTRY_TYPE = "type"
ATTR_OBJECT_ID = "id"

REGISTRY_TYPE_ROOMS = "rooms"
REGISTRY_TYPE_LIGHTS = "lights"
REGISTRY_TYPE_OPENINGS = "openings"
REGISTRY_TYPE_COVERS = "covers"

COVERS_FILE = "covers.yaml"
MODULE_COVERS = "covers"
CAPABILITY_COVERS = "covers"
CAPABILITY_GARAGE = "garage"

OPENINGS_FILE = "openings.yaml"
MODULE_OPENINGS = "openings"
CAPABILITY_OPENINGS = "openings"
SUPPORTED_REGISTRY_TYPES = (
    REGISTRY_TYPE_ROOMS,
    REGISTRY_TYPE_LIGHTS,
    REGISTRY_TYPE_OPENINGS,
    REGISTRY_TYPE_COVERS,
)



# Security
MODULE_SECURITY = "security"
CAPABILITY_SECURITY = "security"


# Native cover platform
SIGNAL_COVER_UPDATED = "wnhf_cover_updated"


# Device Registry
DEVICE_FRAMEWORK = "framework"
DEVICE_LIGHTING = "module:lighting"
DEVICE_OPENINGS = "module:openings"
DEVICE_SECURITY = "module:security"


# Validator
SERVICE_VALIDATE_REGISTRY = "validate_registry"
SIGNAL_VALIDATION_UPDATED = "wnhf_validation_updated"
ACTION_VALIDATE_REGISTRY = "validate_registry"
MODULE_VALIDATOR = "validator"
CAPABILITY_VALIDATION = "validation"


# House Engine
SERVICE_HOUSE_SNAPSHOT = "house_snapshot"
SIGNAL_HOUSE_UPDATED = "wnhf_house_updated"
ACTION_HOUSE_SNAPSHOT = "house_snapshot"
MODULE_HOUSE = "house"
CAPABILITY_HOUSE_ENGINE = "house_engine"


# Capability & Provider Foundation
SERVICE_CAPABILITIES_SNAPSHOT = "capabilities_snapshot"
SIGNAL_CAPABILITIES_UPDATED = "wnhf_capabilities_updated"
ACTION_CAPABILITIES_SNAPSHOT = "capabilities_snapshot"
MODULE_CAPABILITIES = "capabilities"
CAPABILITY_PROVIDER_MODEL = "provider_model"


# Rule Engine Core
RULES_ROOT = ("wnhf", "contexts", "rules")
SERVICE_RULES_SNAPSHOT = "rules_snapshot"
SERVICE_EVALUATE_RULES = "evaluate_rules"
SERVICE_RELOAD_RULES = "reload_rules"
SIGNAL_RULES_UPDATED = "wnhf_rules_updated"
ACTION_RULES_SNAPSHOT = "rules_snapshot"
ACTION_EVALUATE_RULES = "evaluate_rules"
ACTION_RELOAD_RULES = "reload_rules"
MODULE_RULES = "rules"
CAPABILITY_RULE_ENGINE = "rule_engine"


# Context Engine
SERVICE_CONTEXT_SNAPSHOT = "context_snapshot"
SIGNAL_CONTEXT_UPDATED = "wnhf_context_updated"
ACTION_CONTEXT_SNAPSHOT = "context_snapshot"
MODULE_CONTEXT = "context"
CAPABILITY_CONTEXT_ENGINE = "context_engine"


# Policy Engine
POLICIES_ROOT = ("wnhf", "policies")
POLICY_SETTINGS_FILE = "settings.yaml"
SERVICE_POLICIES_SNAPSHOT = "policies_snapshot"
SERVICE_POLICY_CHECK = "policy_check"
SERVICE_RELOAD_POLICIES = "reload_policies"
SIGNAL_POLICIES_UPDATED = "wnhf_policies_updated"
ACTION_POLICIES_SNAPSHOT = "policies_snapshot"
ACTION_POLICY_CHECK = "policy_check"
ACTION_RELOAD_POLICIES = "reload_policies"
MODULE_POLICIES = "policies"
CAPABILITY_POLICY_ENGINE = "policy_engine"

ATTR_POLICY_ID = "policy_id"


# Decision Engine
DECISIONS_ROOT = ("wnhf", "decisions")
SERVICE_DECISIONS_SNAPSHOT = "decisions_snapshot"
SERVICE_DECISION_EVALUATE = "decision_evaluate"
SERVICE_RELOAD_DECISIONS = "reload_decisions"
SIGNAL_DECISIONS_UPDATED = "wnhf_decisions_updated"
ACTION_DECISIONS_SNAPSHOT = "decisions_snapshot"
ACTION_DECISION_EVALUATE = "decision_evaluate"
ACTION_RELOAD_DECISIONS = "reload_decisions"
MODULE_DECISIONS = "decisions"
CAPABILITY_DECISION_ENGINE = "decision_engine"

ATTR_DECISION_ID = "decision_id"

SERVICE_REGISTRY_RECOVERY_REPORT = "registry_recovery_report"
SIGNAL_RECOVERY_UPDATED = "wnhf_recovery_updated"


# Execution Engine - Dry-Run Core
SERVICE_EXECUTION_PLAN = "execution_plan"
SERVICE_EXECUTIONS_SNAPSHOT = "executions_snapshot"
SIGNAL_EXECUTIONS_UPDATED = "wnhf_executions_updated"
ACTION_EXECUTION_PLAN = "execution_plan"
ACTION_EXECUTIONS_SNAPSHOT = "executions_snapshot"
MODULE_EXECUTIONS = "executions"
CAPABILITY_EXECUTION_ENGINE = "execution_engine"
ATTR_EXECUTION_DECISION_ID = "decision_id"


# Execution Transaction Engine - Stage 1
SERVICE_EXECUTION_COMMIT = "execution_commit"
SERVICE_EXECUTION_AUDIT = "execution_audit"
SIGNAL_EXECUTION_AUDIT_UPDATED = "wnhf_execution_audit_updated"
ACTION_EXECUTION_COMMIT = "execution_commit"
ACTION_EXECUTION_AUDIT = "execution_audit"
ATTR_EXECUTION_CONFIRM = "confirm"
EXECUTION_AUDIT_LIMIT = 100

SERVICE_EXECUTE = "execute"
ATTR_PUBLIC_EXECUTION_ID = "id"
ACTION_PUBLIC_EXECUTE = "execute"
SIGNAL_PUBLIC_EXECUTION_UPDATED = "wnhf_public_execution_updated"


# Multi-Step Planner - Stage 2.1
SERVICE_MULTI_STEP_PLAN = "multi_step_plan"
ACTION_MULTI_STEP_PLAN = "multi_step_plan"
SIGNAL_MULTI_STEP_PLAN_UPDATED = "wnhf_multi_step_plan_updated"


# Execution Capability Adapter
SERVICE_EXECUTION_CAPABILITIES_SNAPSHOT = "execution_capabilities_snapshot"
ACTION_EXECUTION_CAPABILITIES_SNAPSHOT = "execution_capabilities_snapshot"
SIGNAL_EXECUTION_CAPABILITIES_UPDATED = "wnhf_execution_capabilities_updated"


# Multi-Step Transaction Simulator - Stage 2.2
SERVICE_MULTI_STEP_SIMULATE = "multi_step_simulate"
SERVICE_MULTI_STEP_SIMULATIONS_SNAPSHOT = "multi_step_simulations_snapshot"
ACTION_MULTI_STEP_SIMULATE = "multi_step_simulate"
ACTION_MULTI_STEP_SIMULATIONS_SNAPSHOT = "multi_step_simulations_snapshot"
SIGNAL_MULTI_STEP_SIMULATION_UPDATED = "wnhf_multi_step_simulation_updated"
MULTI_STEP_SIMULATION_AUDIT_LIMIT = 100

SERVICE_GENERIC_TRANSACTION_RUN = "generic_transaction_run"
SERVICE_GENERIC_TRANSACTIONS_SNAPSHOT = "generic_transactions_snapshot"
ACTION_GENERIC_TRANSACTION_RUN = "generic_transaction_run"
ACTION_GENERIC_TRANSACTIONS_SNAPSHOT = "generic_transactions_snapshot"
SIGNAL_GENERIC_TRANSACTION_UPDATED = "wnhf_generic_transaction_updated"
GENERIC_TRANSACTION_AUDIT_LIMIT = 100


# Real Step Executor - Stage 3.2
SERVICE_REAL_STEP_EXECUTE = "real_step_execute"
SERVICE_REAL_STEP_AUDIT = "real_step_audit"
ACTION_REAL_STEP_EXECUTE = "real_step_execute"
ACTION_REAL_STEP_AUDIT = "real_step_audit"
SIGNAL_REAL_STEP_UPDATED = "wnhf_real_step_updated"
REAL_STEP_AUDIT_LIMIT = 100
REAL_STEP_FEEDBACK_TIMEOUT_SECONDS = 2.0
REAL_STEP_FEEDBACK_INTERVAL_SECONDS = 0.10


# Sequential Room Executor - Stage 3.3
SERVICE_SEQUENTIAL_ROOM_EXECUTE = "sequential_room_execute"
SERVICE_SEQUENTIAL_ROOM_AUDIT = "sequential_room_audit"
ACTION_SEQUENTIAL_ROOM_EXECUTE = "sequential_room_execute"
ACTION_SEQUENTIAL_ROOM_AUDIT = "sequential_room_audit"
SIGNAL_SEQUENTIAL_ROOM_UPDATED = "wnhf_sequential_room_updated"
SEQUENTIAL_ROOM_AUDIT_LIMIT = 100
SEQUENTIAL_FEEDBACK_TIMEOUT_SECONDS = 2.0
SEQUENTIAL_FEEDBACK_INTERVAL_SECONDS = 0.10


# House Execution Pipeline - Stage 3.4
SERVICE_HOUSE_EXECUTE = "house_execute"
SERVICE_HOUSE_EXECUTION_AUDIT = "house_execution_audit"
ACTION_HOUSE_EXECUTE = "house_execute"
ACTION_HOUSE_EXECUTION_AUDIT = "house_execution_audit"
SIGNAL_HOUSE_EXECUTION_UPDATED = "wnhf_house_execution_updated"
HOUSE_EXECUTION_AUDIT_LIMIT = 100
PIPELINE_FEEDBACK_TIMEOUT_SECONDS = 2.0
PIPELINE_FEEDBACK_INTERVAL_SECONDS = 0.10


# Central Execution Manager - Stage 3.5
ACTION_EXECUTION_MANAGER = "execution_manager"
SIGNAL_EXECUTION_MANAGER_UPDATED = "wnhf_execution_manager_updated"


# Transaction Lock Manager - Stage 3.6
SERVICE_TRANSACTION_LOCKS = "transaction_locks"
ACTION_TRANSACTION_LOCKS = "transaction_locks"
SIGNAL_TRANSACTION_LOCKS_UPDATED = "wnhf_transaction_locks_updated"


# Execution Queue & Scheduler - Stage 3.7
ATTR_CONFLICT_POLICY = "conflict_policy"
ATTR_QUEUE_TIMEOUT = "queue_timeout"
CONFLICT_POLICY_REJECT = "reject"
CONFLICT_POLICY_WAIT = "wait"
DEFAULT_CONFLICT_POLICY = CONFLICT_POLICY_REJECT
DEFAULT_QUEUE_TIMEOUT_SECONDS = 15.0
MAX_QUEUE_TIMEOUT_SECONDS = 300.0
SERVICE_TRANSACTION_QUEUE = "transaction_queue"
ACTION_TRANSACTION_QUEUE = "transaction_queue"
SIGNAL_TRANSACTION_QUEUE_UPDATED = "wnhf_transaction_queue_updated"


# System Diagnostics & Runtime Readiness - Stage 3.8 / WP-4.7.8.5
SERVICE_SYSTEM_STATUS = "system_status"
ACTION_SYSTEM_STATUS = "system_status"
SIGNAL_SYSTEM_STATUS_UPDATED = "wnhf_system_status_updated"
SYSTEM_STATUS_API_VERSION = "1.3"


# Release Scope & Diagnostic Classification - Stage 3.9
SERVICE_RELEASE_SCOPE = "release_scope"
ACTION_RELEASE_SCOPE = "release_scope"
SIGNAL_RELEASE_SCOPE_UPDATED = "wnhf_release_scope_updated"
RELEASE_SCOPE_API_VERSION = "1.1"
RELEASE_CHANNEL = "release_candidate"
RELEASE_PHASE = "rc"


# Release Profile - Stage 3.10 / WP-4.7.8.5
SERVICE_RELEASE_INFO = "release_info"
SERVICE_PUBLIC_API = "public_api"
SERVICE_QUALIFICATION = "qualification"
SERVICE_UPGRADE_CHECK = "upgrade_check"
ACTION_RELEASE_INFO = "release_info"
ACTION_PUBLIC_API = "public_api"
ACTION_QUALIFICATION = "qualification"
ACTION_UPGRADE_CHECK = "upgrade_check"
SIGNAL_RELEASE_INFO_UPDATED = "wnhf_release_info_updated"
SIGNAL_PUBLIC_API_UPDATED = "wnhf_public_api_updated"
SIGNAL_QUALIFICATION_UPDATED = "wnhf_qualification_updated"
SIGNAL_UPGRADE_CHECK_UPDATED = "wnhf_upgrade_check_updated"
RELEASE_INFO_API_VERSION = "1.1"
PUBLIC_API_REGISTRY_VERSION = "1.1"
QUALIFICATION_API_VERSION = "1.1"
UPGRADE_CHECK_API_VERSION = "1.1"
# Red Queen 1.0.0-rc5 is the fifth explicitly assigned public release candidate.
RELEASE_CANDIDATE = "rc5"
CANONICAL_EXECUTION_API_VERSION = "1.0"
CANONICAL_EXECUTION_CONTRACT_VERSION = "1.7-rc5"
LEGACY_PUBLIC_EXECUTION_API_VERSION = "1.3"
# Compatibility name now follows the canonical public execution entry.
PUBLIC_EXECUTION_API_VERSION = CANONICAL_EXECUTION_API_VERSION
MINIMUM_REGISTRY_SCHEMA_VERSION = "1.0"
MINIMUM_DECISION_SCHEMA_VERSION = "1.0"
MINIMUM_POLICY_SCHEMA_VERSION = "1.0"


# Access Runtime Snapshot - WP-4.2.1
SERVICE_ACCESS_SNAPSHOT = "access_snapshot"
ACTION_ACCESS_SNAPSHOT = "access_snapshot"
SIGNAL_ACCESS_UPDATED = "wnhf_access_updated"
ACCESS_SNAPSHOT_API_VERSION = "1.0"


# Semantic Access House State - WP-4.2.2
SIGNAL_SECURITY_UPDATED = "wnhf_security_updated"
HOUSE_SECURITY_MODEL_VERSION = "1.0-access"


# Generic Object Capability Contract - WP-4.3.1A
SERVICE_OBJECT_CAPABILITIES_SNAPSHOT = "object_capabilities_snapshot"
ACTION_OBJECT_CAPABILITIES_SNAPSHOT = "object_capabilities_snapshot"
SIGNAL_OBJECT_CAPABILITIES_UPDATED = "wnhf_object_capabilities_updated"
OBJECT_CAPABILITY_API_VERSION = "1.0"


# Access Object Execution - WP-4.3.2B.1
SERVICE_ACCESS_OBJECT_EXECUTE = "access_object_execute"
SERVICE_ACCESS_EXECUTION_AUDIT = "access_execution_audit"
ATTR_ACCESS_OBJECT_ID = "object_id"
ATTR_ACCESS_CAPABILITY_ID = "capability_id"
SIGNAL_ACCESS_EXECUTION_UPDATED = "wnhf_access_execution_updated"
ACTION_ACCESS_OBJECT_EXECUTE = "access_object_execute"
ACTION_ACCESS_EXECUTION_AUDIT = "access_execution_audit"
ACCESS_EXECUTION_AUDIT_LIMIT = 50
ACCESS_LOCK_FEEDBACK_TIMEOUT_SECONDS = 8.0
ACCESS_LOCK_FEEDBACK_INTERVAL_SECONDS = 0.2


# Access Unlock Execution - WP-4.3.2B.2
ACCESS_UNLOCK_FEEDBACK_TIMEOUT_SECONDS = 8.0
ACCESS_UNLOCK_FEEDBACK_INTERVAL_SECONDS = 0.2


# Universal Command / Effect Result Contract - WP-4.3.2B.4A
REAL_STEP_RESULT_CONTRACT_VERSION = "2.0-command-effect"


# Universal Observable Execution - WP-4.3.2B.4B
CONFIRMATION_POLICY_VERSION = "2.0"
COMMAND_DISPATCHER_VERSION = "1.0-stage4.3.2B.4B"
EFFECT_OBSERVER_VERSION = "1.0-stage4.3.2B.4B"
DOOR_OPENER_OBSERVE_TIMEOUT_MS = 5000


# Garage Toggle Transition Execution - WP-4.3.2B.5.1
GARAGE_TOGGLE_TRANSITION_TIMEOUT_MS = 5000
GARAGE_TOGGLE_TRANSITION_INTERVAL_MS = 100


# Garage Terminal-State Completion - WP-4.3.2B.5.2
GARAGE_TERMINAL_TIMEOUT_MS = 45000
GARAGE_TERMINAL_INTERVAL_MS = 200
REAL_STEP_MULTI_EFFECT_CONTRACT_VERSION = "2.1-multi-effect"


# Public Access Execution API - WP-4.4.1
ACCESS_EXECUTION_API_CONTRACT_VERSION = "1.0"
ACCESS_EXECUTION_RESULT_CONTRACT_VERSION = "2.1-multi-effect"
ACCESS_EXECUTION_API_STABILITY = "stable_additive"


# Access Result Catalog - WP-4.4.2
SERVICE_ACCESS_RESULT_CATALOG = "access_result_catalog"
SIGNAL_ACCESS_RESULT_CATALOG_UPDATED = "wnhf_access_result_catalog_updated"
ACCESS_RESULT_CATALOG_VERSION = "1.0"


# Provider Qualification API - WP-4.4.3A
SERVICE_PROVIDER_QUALIFICATION = "provider_qualification"
SIGNAL_PROVIDER_QUALIFICATION_UPDATED = "wnhf_provider_qualification_updated"
PROVIDER_QUALIFICATION_API_VERSION = "1.1"
PROVIDER_QUALIFICATION_MODEL_VERSION = "2.0-stage4.7.8.3"


# Provider Base Contract - current cumulative baseline
SERVICE_PROVIDER_CONTRACT = "provider_contract"
SIGNAL_PROVIDER_CONTRACT_UPDATED = "wnhf_provider_contract_updated"
PROVIDER_CONTRACT_VERSION = "1.0"
PROVIDER_DISCOVERY_ENABLED = True
PROVIDER_DISCOVERY_EXTERNAL_ENTRY_POINTS = False
PROVIDER_DEPENDENCY_INJECTION_ENABLED = False


# Provider Contract Capability-ID Validation Fix - WP-4.5.1.1
PROVIDER_CONTRACT_PATCH_VERSION = "1.0.1"


# Provider Registry Migration - WP-4.5.2
SERVICE_PROVIDER_REGISTRY = "provider_registry"
SIGNAL_PROVIDER_REGISTRY_UPDATED = "wnhf_provider_registry_updated"
PROVIDER_REGISTRY_VERSION = "1.0-stage4.5.2"
PROVIDER_REGISTRY_MIGRATED = True


# Automatic Provider Discovery - WP-4.5.3
SERVICE_PROVIDER_DISCOVERY = "provider_discovery"
SIGNAL_PROVIDER_DISCOVERY_UPDATED = "wnhf_provider_discovery_updated"
PROVIDER_DISCOVERY_VERSION = "1.0-stage4.5.3"


# Unified Provider Diagnostics - WP-4.5.4
SERVICE_PROVIDER_DIAGNOSTICS = "provider_diagnostics"
SIGNAL_PROVIDER_DIAGNOSTICS_UPDATED = "wnhf_provider_diagnostics_updated"
PROVIDER_DIAGNOSTICS_API_VERSION = "1.0"
PROVIDER_DIAGNOSTICS_VERSION = "1.0-stage4.5.4"


# Capability Contract & Registry - WP-4.6.1
SERVICE_CAPABILITY_REGISTRY = "capability_registry"
SIGNAL_CAPABILITY_REGISTRY_UPDATED = "wnhf_capability_registry_updated"
CAPABILITY_CONTRACT_VERSION = "1.0"
CAPABILITY_REGISTRY_VERSION = "1.0-stage4.6.1"
CAPABILITY_RESOLVER_ENABLED = True
CAPABILITY_MANAGER_ENABLED = True
CAPABILITY_EXECUTION_MIGRATION_ENABLED = True


# Capability Import Integration Fix - WP-4.6.1.1
CAPABILITY_INTEGRATION_PATCH_VERSION = "1.0.1"


# Capability Resolver - WP-4.6.2
SERVICE_CAPABILITY_RESOLVER = "capability_resolver"
SIGNAL_CAPABILITY_RESOLVER_UPDATED = "wnhf_capability_resolver_updated"
CAPABILITY_RESOLVER_VERSION = "1.0-stage4.6.2"


# Capability Manager - WP-4.6.3
SERVICE_CAPABILITY_MANAGER = "capability_manager"
SERVICE_CAPABILITY_LIST = "capability_list"
SERVICE_CAPABILITY_INFO = "capability_info"
SIGNAL_CAPABILITY_MANAGER_UPDATED = "wnhf_capability_manager_updated"
CAPABILITY_MANAGER_VERSION = "1.0-stage4.6.3"
CAPABILITY_MANAGER_READ_ONLY = True


# Generic Execution Manager Foundation - WP-4.7.1
SERVICE_EXECUTION_MANAGER = "execution_manager"
SERVICE_EXECUTION_ACTION = "execution_action"
SIGNAL_EXECUTION_MANAGER_UPDATED = "wnhf_execution_manager_updated"
GENERIC_EXECUTION_MANAGER_VERSION = "1.6-rc5"
GENERIC_EXECUTION_ENABLED = True
GENERIC_EXECUTION_READ_ONLY = False


# Generic Execution Contract & Dry-Run - WP-4.7.2
SERVICE_EXECUTION_DRY_RUN = "execution_dry_run"
SIGNAL_EXECUTION_DRY_RUN_UPDATED = "wnhf_execution_dry_run_updated"
GENERIC_EXECUTION_CONTRACT_VERSION = "1.6-rc5"
GENERIC_EXECUTION_DRY_RUN_ENABLED = True
GENERIC_EXECUTION_HARDWARE_ENABLED = True


# First Real Generic Execution - WP-4.7.3
SERVICE_EXECUTION_EXECUTE = "execution_execute"
SIGNAL_EXECUTION_EXECUTE_UPDATED = "wnhf_execution_execute_updated"
GENERIC_REAL_EXECUTION_VERSION = "1.7-rc5"
GENERIC_REAL_EXECUTION_ENABLED = True
GENERIC_REAL_EXECUTION_ACTIONS = (
    "lighting.turn_on",
    "lighting.turn_off",
    "covers.open",
    "covers.close",
    "garage.open",
    "garage.close",
    "openings.lock",
    "openings.unlock",
)


# Execution Plan Promotion - WP-4.7.3A
GENERIC_EXECUTION_PLAN_PROMOTION_VERSION = "1.0-stage4.7.3A"
GENERIC_EXECUTION_PLAN_PROMOTION_ENABLED = True


# Semantic Execution Routing - WP-4.7.4
SEMANTIC_EXECUTION_ROUTER_VERSION = "1.0-stage4.7.4"
SEMANTIC_EXECUTION_ROUTING_ENABLED = True
GENERIC_EXECUTOR_DIRECT_PROVIDER_REGISTRY_ACCESS = False


# Generic Execution Qualification - current cumulative baseline
SERVICE_EXECUTION_QUALIFICATION = "execution_qualification"
SIGNAL_EXECUTION_QUALIFICATION_UPDATED = "wnhf_execution_qualification_updated"
EXECUTION_QUALIFICATION_VERSION = "1.1-stage4.7.5B.1"
EXECUTION_QUALIFICATION_AUTOMATIC_COLLECTION_ENABLED = True
EXECUTION_QUALIFICATION_PERSISTENCE_ENABLED = True


# Execution Qualification Store Path Fix - WP-4.7.5A.1
EXECUTION_QUALIFICATION_STORE_PATH_VERSION = "1.0-stage4.7.5A.1"


# Complete Replace Build - WP-4.7.5B.1
EXECUTION_QUALIFICATION_COMPLETE_REPLACE_VERSION = "1.0-stage4.7.5B.1"


# Structural Engine Fix - WP-4.7.5B.2
EXECUTION_QUALIFICATION_ENGINE_STRUCTURE_FIX_VERSION = "1.0-stage4.7.5B.2"


# Generic Execution Runtime Diagnostics - WP-4.7.6
SERVICE_EXECUTION_RUNTIME_HEALTH = "execution_runtime_health"
SIGNAL_EXECUTION_RUNTIME_HEALTH_UPDATED = "wnhf_execution_runtime_health_updated"
EXECUTION_RUNTIME_DIAGNOSTICS_VERSION = "1.1-stage4.7.9.1"


# Runtime Diagnostics Provider Registry API Fix - WP-4.7.6A
EXECUTION_RUNTIME_DIAGNOSTICS_PROVIDER_API_FIX_VERSION = "1.0-stage4.7.6A"


# Async Core Cleanup - WP-4.7.7.1
ASYNC_CORE_CLEANUP_VERSION = "1.0-stage4.7.7.1"
EXECUTION_EVIDENCE_ASYNC_LOAD_ENABLED = True
PROVIDER_DISCOVERY_EXECUTOR_SCAN_ENABLED = True


# Entity & Logging Production Cleanup - WP-4.7.7.2
ENTITY_LOGGING_PRODUCTION_CLEANUP_VERSION = "1.0-stage4.7.7.2"
SECURITY_MESSAGE_STATE_CONTRACT_VERSION = "2.0-short-state"
OPENINGS_MESSAGE_STATE_CONTRACT_VERSION = "2.0-short-state"
DISABLED_REGISTRY_OBJECTS_ARE_WARNINGS = False
