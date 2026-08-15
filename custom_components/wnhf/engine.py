"""Runtime engine for WNHF."""

from __future__ import annotations

import asyncio
from collections import deque
from uuid import uuid4
import logging
from datetime import UTC, datetime
from pathlib import Path
from functools import partial
from time import perf_counter
from typing import Any

from homeassistant.core import HomeAssistant

from .capabilities import (
    CapabilityDiagnostics,
    CapabilityManager,
    CapabilityRegistry,
    CapabilityResolver,
    register_core_capabilities,
)

from .domain.capability import (
    CapabilityCatalog,
    CapabilitySnapshot,
    ObjectCapability,
)
from .decisions import (
    DecisionEvaluator,
    DecisionRegistry,
    load_decision_registry,
)
from .public_api import PublicExecutionResult
from .executions import (
    SemanticExecutionManager,
    ExecutionPlanner,
    ExecutionRuntimeDiagnostics,
    GenericExecutionEngine,
    GenericExecutionPlanner,
    SemanticExecutionRouter,
    ExecutionTransaction,
    ExecutionTransactionStatus,
    MultiStepBlueprint,
    MultiStepBlueprintStep,
    ExecutionCapabilityAdapter,
    TransactionLockManager,
    LegacyExecutionManager,
    ExecutionPipeline,
    HouseExecutionResult,
    HouseExecutionState,
    HouseExecutionTransition,
    HouseRoomResult,
    SequentialRoomResult,
    SequentialRoomState,
    SequentialRoomTransition,
    SequentialStepResult,
    SequentialStepState,
    AccessResultCatalog,
    CommandDispatcher,
    CommandOutcome,
    CommandStatus,
    ConfirmationPolicy,
    EffectConfirmationMode,
    EffectObserver,
    EffectOutcome,
    EffectStatus,
    RealStepResult,
    RealStepState,
    RealStepTransition,
    GenericTransactionResult,
    GenericTransactionState,
    GenericTransactionTransition,
    MultiStepSimulation,
    MultiStepSimulationStatus,
    MultiStepSimulationStep,
    MultiStepSimulationStepStatus,
)
from .domain.context import ContextScores, ContextSnapshot
from .domain.cover_state import CoverSnapshot, CoverState, CoverStateMachine
from .domain.house import House
from .domain.house_state import HouseSnapshot, HouseState
from .domain.light import Light
from .domain.light_state import LightSnapshot
from .domain.security import SecurityEngine, SecuritySnapshot
from .domain.access_state import (
    AccessObjectSnapshot,
    AccessSnapshot,
    GarageDoorRuntimeState,
    LockRuntimeState,
    OpeningRuntimeState,
)
from .diagnostics import DiagnosticsSnapshot, ModuleDiagnostic
from .system_status import SystemCheck, SystemStatusSnapshot
from .release_scope import ReleaseScopeManager
from .release_candidate import ReleaseProfile
from .registry import load_house
from .rules import (
    RuleEvaluator,
    RuleRegistry,
    RuleSnapshot,
    combined_context_registry,
    load_rule_registry,
)
from .performance import PerformanceStore
from .policies import PolicyEvaluator, PolicyRegistry, load_policy_registry
from .qualification import (
    ExecutionEvidenceStore,
    ExecutionQualificationCollector,
    ExecutionQualificationService,
    ProviderQualificationService,
)
from .providers import (
    ProviderDiscovery,
    UnifiedProviderDiagnostics,
    WNHFProvider,
    WNHFProviderRegistry,
    provider_contract_definition,
    validate_provider_contract,
    CoversCapabilityProvider,
    LightingCapabilityProvider,
    OpeningsCapabilityProvider,
    SecurityCapabilityProvider,
    ValidatorCapabilityProvider,
)
from .validator import ValidationReport, WNHFValidator
from .const import (
    CAPABILITY_COVERS,
    CAPABILITY_DIAGNOSTICS,
    CAPABILITY_HOUSE_MODEL,
    CAPABILITY_HOUSE_ENGINE,
    CAPABILITY_PROVIDER_MODEL,
    CAPABILITY_RULE_ENGINE,
    CAPABILITY_CONTEXT_ENGINE,
    CAPABILITY_POLICY_ENGINE,
    CAPABILITY_DECISION_ENGINE,
    CAPABILITY_EXECUTION_ENGINE,
    CAPABILITY_LIGHTING,
    CAPABILITY_OPENINGS,
    CAPABILITY_SECURITY,
    CAPABILITY_VALIDATION,
    MODULE_CORE,
    MODULE_HOUSE,
    MODULE_CAPABILITIES,
    MODULE_RULES,
    MODULE_CONTEXT,
    MODULE_POLICIES,
    MODULE_DECISIONS,
    MODULE_EXECUTIONS,
    MODULE_COVERS,
    MODULE_DIAGNOSTICS,
    MODULE_LIGHTING,
    MODULE_OPENINGS,
    MODULE_SECURITY,
    MODULE_VALIDATOR,
    VERSION,
    ACTION_REGISTRY_RELOAD,
    ACTION_LIGHTING_ALL_OFF,
    ACTION_LIGHTING_ROOM_OFF,
    ACTION_LIGHTING_OBJECT_OFF,
    ACTION_VALIDATE_REGISTRY,
    ACTION_HOUSE_SNAPSHOT,
    ACTION_ACCESS_SNAPSHOT,
    ACTION_CAPABILITIES_SNAPSHOT,
    ACTION_RULES_SNAPSHOT,
    ACTION_EVALUATE_RULES,
    ACTION_RELOAD_RULES,
    ACTION_CONTEXT_SNAPSHOT,
    ACTION_POLICIES_SNAPSHOT,
    ACTION_POLICY_CHECK,
    ACTION_RELOAD_POLICIES,
    ACTION_DECISIONS_SNAPSHOT,
    ACTION_DECISION_EVALUATE,
    ACTION_RELOAD_DECISIONS,
    ACTION_EXECUTION_PLAN,
    ACTION_EXECUTIONS_SNAPSHOT,
    ACTION_EXECUTION_COMMIT,
    ACTION_EXECUTION_AUDIT,
    ACTION_PUBLIC_EXECUTE,
    ACTION_EXECUTION_MANAGER,
    ACTION_TRANSACTION_LOCKS,
    ACTION_TRANSACTION_QUEUE,
    ACTION_SYSTEM_STATUS,
    ACTION_RELEASE_SCOPE,
    ACTION_RELEASE_INFO,
    ACTION_PUBLIC_API,
    ACTION_QUALIFICATION,
    ACTION_UPGRADE_CHECK,
    SYSTEM_STATUS_API_VERSION,
    ACTION_MULTI_STEP_PLAN,
    ACTION_EXECUTION_CAPABILITIES_SNAPSHOT,
    ACTION_MULTI_STEP_SIMULATE,
    ACTION_GENERIC_TRANSACTION_RUN,
    ACTION_REAL_STEP_EXECUTE,
    ACTION_SEQUENTIAL_ROOM_EXECUTE,
    ACTION_HOUSE_EXECUTE,
    ACTION_HOUSE_EXECUTION_AUDIT,
    HOUSE_EXECUTION_AUDIT_LIMIT,
    PIPELINE_FEEDBACK_TIMEOUT_SECONDS,
    PIPELINE_FEEDBACK_INTERVAL_SECONDS,
    ACTION_SEQUENTIAL_ROOM_AUDIT,
    SEQUENTIAL_ROOM_AUDIT_LIMIT,
    SEQUENTIAL_FEEDBACK_TIMEOUT_SECONDS,
    SEQUENTIAL_FEEDBACK_INTERVAL_SECONDS,
    ACTION_REAL_STEP_AUDIT,
    REAL_STEP_AUDIT_LIMIT,
    REAL_STEP_FEEDBACK_TIMEOUT_SECONDS,
    REAL_STEP_FEEDBACK_INTERVAL_SECONDS,
    ACCESS_EXECUTION_AUDIT_LIMIT,
    ACCESS_LOCK_FEEDBACK_INTERVAL_SECONDS,
    ACCESS_LOCK_FEEDBACK_TIMEOUT_SECONDS,
    ACCESS_UNLOCK_FEEDBACK_INTERVAL_SECONDS,
    ACCESS_UNLOCK_FEEDBACK_TIMEOUT_SECONDS,
    ACTION_ACCESS_EXECUTION_AUDIT,
    ACTION_ACCESS_OBJECT_EXECUTE,
    GARAGE_TERMINAL_INTERVAL_MS,
    GARAGE_TERMINAL_TIMEOUT_MS,
    ACTION_GENERIC_TRANSACTIONS_SNAPSHOT,
    GENERIC_TRANSACTION_AUDIT_LIMIT,
    ACTION_MULTI_STEP_SIMULATIONS_SNAPSHOT,
    MULTI_STEP_SIMULATION_AUDIT_LIMIT,
    EXECUTION_AUDIT_LIMIT,
    REGISTRY_TYPE_COVERS,
    REGISTRY_TYPE_LIGHTS,
    REGISTRY_TYPE_ROOMS,
    REGISTRY_TYPE_OPENINGS,
)

_LOGGER = logging.getLogger(__name__)


class WNHFEngine:
    """Red Queen runtime and service implementation."""

    def __init__(self, hass: HomeAssistant, registry_dir: Path) -> None:
        self.hass = hass
        self.registry_dir = registry_dir
        self.house: House | None = None
        self.registry_warnings: tuple[str, ...] = ()
        self.registry_loaded_at: datetime | None = None
        self.registry_load_ms: float | None = None
        self.performance = PerformanceStore()
        self.validation_report: ValidationReport | None = None
        self.providers = WNHFProviderRegistry()
        self.semantic_capabilities = CapabilityRegistry()
        register_core_capabilities(self.semantic_capabilities)
        self.capability_resolver = CapabilityResolver(
            self.semantic_capabilities,
            self.providers,
        )
        self.capability_manager = CapabilityManager(
            self.semantic_capabilities,
            self.capability_resolver,
        )
        self.semantic_execution_manager = SemanticExecutionManager(
            self.capability_manager,
            self.semantic_capabilities,
        )
        self.generic_execution_planner = GenericExecutionPlanner(
            self.semantic_execution_manager,
            self.providers,
        )
        self.semantic_execution_router = SemanticExecutionRouter(
            self.providers
        )
        self.generic_execution_engine = GenericExecutionEngine(
            self.generic_execution_planner,
            self.semantic_execution_router,
        )
        self.execution_evidence_store = ExecutionEvidenceStore(
            Path(
                hass.config.path(
                    "wnhf",
                    "qualification",
                    "execution_evidence_store.json",
                )
            )
        )
        self.execution_qualification_collector = (
            ExecutionQualificationCollector()
        )
        self.execution_qualification_service = (
            ExecutionQualificationService(
                self.execution_evidence_store,
                self.execution_qualification_collector,
            )
        )
        self.execution_runtime_diagnostics = ExecutionRuntimeDiagnostics(
            execution_manager=self.semantic_execution_manager,
            semantic_router=self.semantic_execution_router,
            provider_registry=self.providers,
            qualification_service=self.execution_qualification_service,
        )
        self.capability_diagnostics = CapabilityDiagnostics(
            self.semantic_capabilities,
            self.providers,
            self.capability_resolver,
        )
        self.provider_discovery = ProviderDiscovery(
            hass,
            self,
            self.providers,
        )
        self.unified_provider_diagnostics = (
            UnifiedProviderDiagnostics(self.providers)
        )
        self.capability_catalog = CapabilityCatalog.builtin()
        self.provider_qualification_service = ProviderQualificationService(
            self.providers,
            self.execution_evidence_store,
            legacy_store_path=str(
                self.registry_dir.parents[1]
                / "qualification"
                / "provider_evidence_store.json"
            ),
        )
        self.command_dispatcher = CommandDispatcher(hass)
        self.effect_observer = EffectObserver()
        self.rules_dir = self.registry_dir.parents[1] / "contexts" / "rules"
        self.rule_registry = RuleRegistry()
        self.rule_snapshot: RuleSnapshot | None = None
        self.context_snapshot_cache: ContextSnapshot | None = None
        self.policies_dir = self.registry_dir.parents[1] / "policies"
        self.policy_registry = PolicyRegistry()
        self.last_policy_decision = None
        self.decisions_dir = self.registry_dir.parents[1] / "decisions"
        self.decision_registry = DecisionRegistry()
        self.last_decision_result = None
        self.last_execution_plan = None
        self.last_execution_transaction = None
        # Canonical Stage-4.7 public execution is tracked separately from the
        # Decision-ID legacy compatibility service.
        self.last_canonical_execution = None
        self.last_legacy_public_execution = None
        self.last_public_execution = None  # Deprecated legacy compatibility alias.
        self.transaction_lock_manager = TransactionLockManager()
        self.last_lock_decision = None
        self.last_system_status = None
        self.last_release_scope = None
        self.last_release_info = None
        self.last_public_api = None
        self.last_qualification = None
        self.last_upgrade_check = None
        self.last_multi_step_blueprint = None
        self.last_multi_step_simulation = None
        self.last_generic_transaction = None
        self.last_real_step_result = None
        self.last_access_execution_result = None
        self.last_sequential_room_result = None
        self.last_house_execution_result = None
        self.house_execution_audit = deque(
            maxlen=HOUSE_EXECUTION_AUDIT_LIMIT
        )
        self.sequential_room_audit = deque(
            maxlen=SEQUENTIAL_ROOM_AUDIT_LIMIT
        )
        self.real_step_audit = deque(maxlen=REAL_STEP_AUDIT_LIMIT)
        self.access_execution_audit = deque(
            maxlen=ACCESS_EXECUTION_AUDIT_LIMIT
        )
        self.generic_transaction_audit = deque(maxlen=GENERIC_TRANSACTION_AUDIT_LIMIT)
        self.multi_step_simulation_audit = deque(
            maxlen=MULTI_STEP_SIMULATION_AUDIT_LIMIT
        )
        self.execution_audit = deque(maxlen=EXECUTION_AUDIT_LIMIT)
        self._execution_lock = asyncio.Lock()
        self.safe_mode = False
        self.startup_error: str | None = None

    def registry_recovery_report(self) -> dict[str, Any]:
        """Return a non-destructive registry preflight report."""
        required = ("rooms.yaml", "lights.yaml", "covers.yaml", "openings.yaml")
        files = {
            name: {
                "path": str(self.registry_dir / name),
                "exists": (self.registry_dir / name).is_file(),
            }
            for name in required
        }
        missing = [name for name, item in files.items() if not item["exists"]]
        return {
            "safe_mode": self.safe_mode,
            "startup_error": self.startup_error,
            "registry_dir": str(self.registry_dir),
            "status": "healthy" if not missing and not self.safe_mode else "recovery_required",
            "required_files": files,
            "missing_files": missing,
            "recovery_hint": (
                "Restore missing files and restart Home Assistant."
                if missing else
                "Registry files are present."
            ),
        }

    def register_provider(
        self,
        provider: WNHFProvider,
        *,
        replace: bool = False,
    ) -> None:
        """Register one external provider through the provider registry."""
        if replace:
            self.providers.replace(provider)
        else:
            self.providers.register(provider)

    async def execution_runtime_health(
        self,
    ) -> dict[str, Any]:
        started = perf_counter()
        result = await self.execution_runtime_diagnostics.async_snapshot()
        self.performance.record(
            "execution_runtime_health",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def execution_qualification_snapshot(self) -> dict[str, Any]:
        """Return generic execution qualification architecture diagnostics."""
        started = perf_counter()
        result = self.execution_qualification_service.snapshot()
        self.performance.record(
            "execution_qualification",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def execution_execute(
        self,
        *,
        action_id: str,
        target: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        """Execute one semantic action and persist qualifying evidence."""
        started = perf_counter()

        result = await self.generic_execution_engine.async_execute(
            action_id=action_id,
            target=target,
            parameters=parameters,
            confirmed=confirmed,
        )
        payload = result.as_dict()

        decision = self.execution_qualification_collector.classify(
            payload
        )
        qualification = decision.as_dict()
        qualification["persisted"] = False
        qualification["store_write_error"] = None

        if decision.qualified and decision.evidence is not None:
            existing = self.execution_evidence_store.get(
                decision.evidence.evidence_id
            )
            merged = (
                self.execution_qualification_collector
                .merge_with_existing(
                    decision=decision,
                    existing=existing,
                )
            )

            if merged is not None:
                self.execution_evidence_store.upsert(merged)
                qualification["evidence"] = merged.as_dict()
                write_at = datetime.now(UTC).isoformat()

                try:
                    await self.hass.async_add_executor_job(
                        partial(
                            self.execution_evidence_store.persist,
                            last_write_at=write_at,
                        )
                    )
                    qualification["persisted"] = True
                except Exception as err:  # noqa: BLE001
                    qualification["store_write_error"] = (
                        f"{type(err).__name__}: {err}"
                    )

        payload["qualification"] = qualification
        self.last_canonical_execution = payload
        self.execution_runtime_diagnostics.record_execution(payload)

        self.performance.record(
            "execution_execute",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return payload
    async def execution_dry_run(
        self,
        *,
        action_id: str,
        target: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        """Build a generic semantic dry-run execution plan."""
        started = perf_counter()
        result = await self.generic_execution_planner.async_dry_run(
            action_id=action_id,
            target=target,
            parameters=parameters,
            confirmed=confirmed,
        )
        payload = result.as_dict()
        self.performance.record(
            "execution_dry_run",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return payload

    async def execution_manager_status(
        self,
    ) -> dict[str, Any]:
        started = perf_counter()
        result = await self.semantic_execution_manager.async_status()
        self.performance.record(
            "execution_manager",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def execution_action_resolution(
        self,
        action_id: str,
    ) -> dict[str, Any]:
        started = perf_counter()
        result = (
            await self.semantic_execution_manager.async_resolve_action(action_id)
        ).as_dict()
        self.performance.record(
            "execution_action",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def capability_manager_status(
        self,
    ) -> dict[str, Any]:
        """Return public aggregate Capability Manager status."""
        started = perf_counter()
        result = await self.capability_manager.async_status()
        self.performance.record(
            "capability_manager",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def capability_manager_list(
        self,
    ) -> dict[str, Any]:
        """Return public compact Capability Manager list."""
        started = perf_counter()
        result = await self.capability_manager.async_get_capabilities()
        self.performance.record(
            "capability_list",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def capability_manager_info(
        self,
        capability_id: str,
    ) -> dict[str, Any]:
        """Return public detailed Capability Manager response."""
        started = perf_counter()
        result = await self.capability_manager.async_get_capability(
            capability_id
        )
        self.performance.record(
            "capability_info",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def capability_resolver_snapshot(self) -> dict[str, Any]:
        """Return explainable semantic capability resolutions."""
        started = perf_counter()
        result = self.capability_resolver.snapshot()
        self.performance.record(
            "capability_resolver",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def capability_registry_snapshot(self) -> dict[str, Any]:
        """Return semantic capability contract and registry diagnostics."""
        started = perf_counter()
        result = self.capability_diagnostics.snapshot()
        self.performance.record(
            "capability_registry",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def provider_diagnostics_snapshot(self) -> dict[str, Any]:
        """Return unified provider diagnostics across all subsystems."""
        started = perf_counter()

        discovery_snapshot = self.provider_discovery.snapshot()
        qualification_snapshot = (
            self.provider_qualification_snapshot()
        )
        result = self.unified_provider_diagnostics.snapshot(
            discovery_snapshot=discovery_snapshot,
            qualification_snapshot=qualification_snapshot,
        )

        self.performance.record(
            "provider_diagnostics",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def provider_discovery_snapshot(self) -> dict[str, Any]:
        """Return automatic provider-discovery diagnostics."""
        started = perf_counter()
        result = self.provider_discovery.snapshot()
        result["registry_revision"] = self.providers.revision
        result["registered_provider_ids"] = list(
            self.providers.provider_ids()
        )
        self.performance.record(
            "provider_discovery",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def provider_registry_snapshot(self) -> dict[str, Any]:
        """Return provider-centric registry and resolution diagnostics."""
        started = perf_counter()
        result = self.providers.diagnostics()
        self.performance.record(
            "provider_registry",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def provider_contract_snapshot(self) -> dict[str, Any]:
        """Return side-effect-free provider-contract diagnostics."""
        started = perf_counter()
        providers: list[dict[str, Any]] = []

        for provider in self.providers.providers():
            if isinstance(provider, WNHFProvider):
                diagnostic = provider.diagnostics().as_dict()
            else:
                diagnostic = {
                    "metadata": {
                        "provider_id": getattr(
                            provider,
                            "provider_id",
                            None,
                        ),
                        "class_name": type(provider).__name__,
                        "contract_version": None,
                    },
                    "runtime": None,
                    "contract": {
                        "valid": False,
                        "errors": [
                            "Provider does not inherit WNHFProvider."
                        ],
                    },
                    "qualification": None,
                }
            providers.append(diagnostic)

        valid = sum(
            bool(item["contract"]["valid"])
            for item in providers
        )
        result = {
            "api_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "contract": provider_contract_definition(),
            "summary": {
                "registered": len(providers),
                "contract_valid": valid,
                "contract_invalid": len(providers) - valid,
                "all_valid": valid == len(providers),
                "registry_migrated": True,
                "discovery_enabled": True,
                "dependency_injection_enabled": False,
            },
            "providers": providers,
        }
        self.performance.record(
            "provider_contract",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def capability_snapshot(
        self,
        capability_id: str,
    ) -> CapabilitySnapshot:
        """Return one capability snapshot, including unsupported state."""
        provider = self.providers.resolve_provider(capability_id)
        if provider is None:
            from .domain.capability import CapabilityState

            return CapabilitySnapshot(
                capability_id=capability_id,
                provider_id=None,
                supported=False,
                available=False,
                healthy=False,
                state=CapabilityState.UNSUPPORTED,
                message=f"Capability '{capability_id}' is not configured.",
                details={},
            )
        return provider.snapshot()

    def capabilities_snapshot(self) -> dict[str, dict]:
        """Return every registered capability snapshot."""
        snapshots = self.providers.snapshots()
        return {
            capability_id: snapshot.as_dict()
            for capability_id, snapshot in snapshots.items()
        }

    def object_capabilities_snapshot(self) -> dict[str, Any]:
        """Return semantic capability contracts for Registry objects."""
        started = perf_counter()
        house = self._require_house()
        declarations: list[ObjectCapability] = []

        for light in house.lights.values():
            declarations.extend(light.object_capabilities())
        for cover in house.covers.values():
            declarations.extend(cover.object_capabilities())
        for opening in house.openings.values():
            declarations.extend(opening.object_capabilities())

        declarations.sort(key=lambda item: (
            item.object_type,
            item.room_id,
            item.object_id,
            item.capability_id,
        ))

        unknown = sorted({
            item.capability_id
            for item in declarations
            if not self.capability_catalog.contains(item.capability_id)
        })

        monitor_count = 0
        action_count = 0
        by_domain: dict[str, int] = {}
        for item in declarations:
            definition = self.capability_catalog.get(item.capability_id)
            if definition is None:
                continue
            by_domain[definition.domain_id] = (
                by_domain.get(definition.domain_id, 0) + 1
            )
            if definition.kind.value == "action":
                action_count += 1
            else:
                monitor_count += 1

        result = {
            "api_version": "1.0",
            "catalog": self.capability_catalog.as_dict(),
            "summary": {
                "objects": len({item.object_id for item in declarations}),
                "declarations": len(declarations),
                "monitor_declarations": monitor_count,
                "action_declarations": action_count,
                "unknown_capability_count": len(unknown),
                "valid": not unknown,
                "by_domain": dict(sorted(by_domain.items())),
            },
            "unknown_capability_ids": unknown,
            "objects": [item.as_dict() for item in declarations],
        }
        self.performance.record(
            "object_capabilities_snapshot",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def async_prepare_runtime(self) -> None:
        """Prepare blocking-backed runtime resources asynchronously."""
        await self.execution_evidence_store.async_load(self.hass)

    async def async_load_registry(self) -> House:
        """Load the registry, build the House model, and record diagnostics."""
        started = perf_counter()
        house, warnings = await self.hass.async_add_executor_job(
            load_house, self.registry_dir
        )
        self.registry_load_ms = round((perf_counter() - started) * 1000, 2)
        called_at = datetime.now(UTC)
        self.registry_loaded_at = called_at
        self.performance.record(
            ACTION_REGISTRY_RELOAD,
            self.registry_load_ms,
            called_at,
        )
        self.house = house
        self.registry_warnings = warnings
        await self.async_load_rules()
        await self.async_load_policies()
        await self.async_load_decisions()
        return house

    def execution_plan(self, decision_id: str):
        """Build one non-executing, validated execution plan."""
        started = perf_counter()
        decision = self.decision_evaluate(decision_id)
        plan = ExecutionPlanner.plan(
            decision=decision,
            house=self._require_house(),
            light_snapshots=self.light_snapshots(),
        )
        self.last_execution_plan = plan
        self.performance.record(
            ACTION_EXECUTION_PLAN,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return plan

    def executions_snapshot(self) -> dict[str, Any]:
        """Build dry-run plans for every configured decision."""
        started = perf_counter()
        plans = {
            item.decision_id: self.execution_plan(
                item.decision_id
            ).as_dict()
            for item in self.decision_registry.decisions
        }
        self.performance.record(
            ACTION_EXECUTIONS_SNAPSHOT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "dry_run": True,
            "executed": False,
            "supported_actions": sorted(
                ExecutionPlanner.SUPPORTED_ACTIONS
            ),
            "plans": plans,
        }


    def house_execution_audit_snapshot(self) -> dict[str, Any]:
        """Return the bounded in-memory house execution audit."""
        started = perf_counter()
        records = [
            item.as_dict()
            for item in reversed(self.house_execution_audit)
        ]
        self.performance.record(
            ACTION_HOUSE_EXECUTION_AUDIT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "count": len(records),
            "limit": HOUSE_EXECUTION_AUDIT_LIMIT,
            "records": records,
        }

    async def async_house_execute(
        self,
        decision_id: str,
        confirmed: bool,
    ) -> HouseExecutionResult:
        """Execute a lighting.all_off blueprint grouped by room."""
        async with self._execution_lock:
            started_perf = perf_counter()
            generated_at = datetime.now(UTC)
            transaction_id = (
                f"hex_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
                f"{uuid4().hex[:8]}"
            )
            blueprint = self.multi_step_plan(decision_id)
            transitions: list[HouseExecutionTransition] = []
            room_results: list[HouseRoomResult] = []
            transition_sequence = 0

            def move(
                to_state: HouseExecutionState,
                reason: str,
                room_id: str | None = None,
                step_id: str | None = None,
            ) -> None:
                nonlocal transition_sequence
                transition_sequence += 1
                previous = (
                    transitions[-1].to_state.value
                    if transitions
                    else None
                )
                transitions.append(
                    HouseExecutionTransition(
                        sequence=transition_sequence,
                        at=datetime.now(UTC),
                        from_state=previous,
                        to_state=to_state,
                        reason=reason,
                        room_id=room_id,
                        step_id=step_id,
                    )
                )

            move(HouseExecutionState.CREATED, "House transaction created.")
            move(
                HouseExecutionState.VALIDATING,
                "Confirmation, blueprint and room queue are validated.",
            )

            accepted = False
            state = HouseExecutionState.REJECTED
            executed = False
            command_count = 0
            failed_room_id = None
            failed_step_id = None
            reason = "House execution rejected."
            transaction_error = None

            try:
                if not confirmed:
                    reason = "Explicit confirmation is required."
                    move(state, reason)
                elif not blueprint.accepted_for_planning:
                    reason = "Blueprint is not accepted for planning."
                    move(state, reason)
                elif blueprint.status != "ready":
                    reason = f"Blueprint status is {blueprint.status!r}."
                    move(state, reason)
                elif blueprint.action != "lighting.all_off":
                    reason = (
                        "Stage 3.4 supports only lighting.all_off Decisions."
                    )
                    move(state, reason)
                elif not blueprint.stop_on_error:
                    reason = "Stage 3.4 requires stop_on_error=true."
                    move(state, reason)
                elif not blueprint.steps:
                    accepted = True
                    state = HouseExecutionState.NO_ACTION
                    reason = "No active steps require execution."
                    move(state, reason)
                else:
                    room_steps: dict[str, list] = {}
                    for step in blueprint.steps:
                        room_steps.setdefault(step.room_id, []).append(step)

                    room_queue = sorted(room_steps.items(), key=lambda item: item[0])

                    invalid_steps = []
                    for _room_id, steps in room_queue:
                        for step in steps:
                            valid, _ = ExecutionPipeline.validate_guarded_step(step)
                            if not valid:
                                invalid_steps.append(step.step_id)

                    if invalid_steps:
                        reason = (
                            "One or more pipeline steps are invalid: "
                            + ", ".join(invalid_steps)
                        )
                        move(state, reason)
                    else:
                        accepted = True
                        state = HouseExecutionState.READY
                        move(state, "All rooms and steps passed validation.")
                        state = HouseExecutionState.RUNNING
                        move(state, "House execution started.")

                        house = self._require_house()
                        total_house_steps = len(blueprint.steps)
                        processed_house_steps = 0

                        for room_index, (room_id, steps) in enumerate(
                            room_queue,
                            start=1,
                        ):
                            room_name = (
                                house.rooms[room_id].name
                                if room_id in house.rooms
                                else room_id
                            )
                            move(
                                HouseExecutionState.RUNNING,
                                "Room execution started.",
                                room_id=room_id,
                            )

                            room_step_results = []
                            room_completed = 0
                            room_skipped = 0
                            room_failed = 0
                            room_commands = 0
                            room_failed_step_id = None
                            room_reason = "Room completed successfully."
                            room_state = "succeeded"

                            for step in steps:
                                move(
                                    HouseExecutionState.RUNNING,
                                    "Executing guarded room step.",
                                    room_id=room_id,
                                    step_id=step.step_id,
                                )
                                pipeline_result = (
                                    await ExecutionPipeline.async_execute_guarded_step(
                                        hass=self.hass,
                                        step=step,
                                        snapshot_reader=self.light_snapshot,
                                        feedback_timeout_seconds=(
                                            PIPELINE_FEEDBACK_TIMEOUT_SECONDS
                                        ),
                                        feedback_interval_seconds=(
                                            PIPELINE_FEEDBACK_INTERVAL_SECONDS
                                        ),
                                    )
                                )

                                processed_house_steps += 1
                                if pipeline_result.command_sent:
                                    command_count += 1
                                    room_commands += 1
                                    executed = True

                                if pipeline_result.state == "succeeded":
                                    room_completed += 1
                                elif pipeline_result.state == "skipped":
                                    room_skipped += 1
                                else:
                                    room_failed += 1
                                    room_failed_step_id = step.step_id
                                    failed_step_id = step.step_id

                                room_step_results.append({
                                    "step_id": step.step_id,
                                    "sequence": step.sequence,
                                    "object_id": step.object_id,
                                    "object_name": step.object_name,
                                    "room_id": step.room_id,
                                    "progress_percent": round(
                                        (
                                            processed_house_steps
                                            / total_house_steps
                                        ) * 100,
                                        1,
                                    ),
                                    "capability": step.capability,
                                    "command_entity_id": (
                                        step.command_entity_id
                                    ),
                                    **pipeline_result.as_dict(),
                                })

                                if pipeline_result.state == "failed":
                                    room_state = "failed"
                                    room_reason = (
                                        "Room stopped at the first failed step."
                                    )
                                    failed_room_id = room_id
                                    break

                            room_progress = round(
                                (
                                    len(room_step_results)
                                    / len(steps)
                                ) * 100,
                                1,
                            )
                            room_results.append(
                                HouseRoomResult(
                                    room_id=room_id,
                                    room_name=room_name,
                                    sequence=room_index,
                                    state=room_state,
                                    total_steps=len(steps),
                                    completed_steps=room_completed,
                                    skipped_steps=room_skipped,
                                    failed_steps=room_failed,
                                    command_count=room_commands,
                                    progress_percent=room_progress,
                                    failed_step_id=room_failed_step_id,
                                    reason=room_reason,
                                    steps=tuple(room_step_results),
                                )
                            )

                            if room_state == "failed":
                                state = HouseExecutionState.FAILED
                                reason = (
                                    "House execution stopped at the first "
                                    "failed room."
                                )
                                move(
                                    state,
                                    reason,
                                    room_id=room_id,
                                    step_id=room_failed_step_id,
                                )
                                break

                            move(
                                HouseExecutionState.RUNNING,
                                "Room execution completed.",
                                room_id=room_id,
                            )

                        if state != HouseExecutionState.FAILED:
                            state = HouseExecutionState.SUCCEEDED
                            reason = "All house rooms completed successfully."
                            move(state, reason)

            except Exception as err:  # noqa: BLE001
                state = HouseExecutionState.FAILED
                transaction_error = f"{type(err).__name__}: {err}"
                reason = "House execution failed with an exception."
                move(state, reason)
                _LOGGER.exception(
                    "Red Queen house execution failed: %s",
                    transaction_id,
                )

            finished_at = datetime.now(UTC)
            completed_rooms = sum(
                1 for item in room_results if item.state == "succeeded"
            )
            failed_rooms = sum(
                1 for item in room_results if item.state == "failed"
            )
            completed_steps = sum(
                item.completed_steps for item in room_results
            )
            skipped_steps = sum(
                item.skipped_steps for item in room_results
            )
            failed_steps = sum(
                item.failed_steps for item in room_results
            )
            total_rooms = len({
                step.room_id for step in blueprint.steps
            })
            total_steps = len(blueprint.steps)
            processed_steps = sum(
                len(item.steps) for item in room_results
            )
            progress_percent = (
                round((processed_steps / total_steps) * 100, 1)
                if total_steps
                else 100.0
            )

            result = HouseExecutionResult(
                transaction_id=transaction_id,
                generated_at=generated_at,
                finished_at=finished_at,
                duration_ms=round(
                    (perf_counter() - started_perf) * 1000,
                    2,
                ),
                decision_id=decision_id,
                plan_id=blueprint.plan_id,
                confirmed=confirmed,
                accepted=accepted,
                state=state,
                dry_run=False,
                executed=executed,
                command_count=command_count,
                total_rooms=total_rooms,
                completed_rooms=completed_rooms,
                failed_rooms=failed_rooms,
                total_steps=total_steps,
                completed_steps=completed_steps,
                skipped_steps=skipped_steps,
                failed_steps=failed_steps,
                progress_percent=progress_percent,
                failed_room_id=failed_room_id,
                failed_step_id=failed_step_id,
                reason=reason,
                error=transaction_error,
                transitions=tuple(transitions),
                rooms=tuple(room_results),
                blueprint=blueprint.as_dict(),
                executor_version="1.0-stage3.4",
                pipeline_version=ExecutionPipeline.VERSION,
            )
            self.last_house_execution_result = result
            self.house_execution_audit.append(result)
            self.performance.record(
                ACTION_HOUSE_EXECUTE,
                result.duration_ms,
                finished_at,
            )
            return result

    def sequential_room_audit_snapshot(self) -> dict[str, Any]:
        """Return the bounded in-memory sequential room audit."""
        started = perf_counter()
        records = [
            item.as_dict()
            for item in reversed(self.sequential_room_audit)
        ]
        self.performance.record(
            ACTION_SEQUENTIAL_ROOM_AUDIT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "count": len(records),
            "limit": SEQUENTIAL_ROOM_AUDIT_LIMIT,
            "records": records,
        }

    async def async_sequential_room_execute(
        self,
        decision_id: str,
        confirmed: bool,
    ) -> SequentialRoomResult:
        """Execute all active steps of one room strictly sequentially."""
        async with self._execution_lock:
            started_perf = perf_counter()
            generated_at = datetime.now(UTC)
            transaction_id = (
                f"sre_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
                f"{uuid4().hex[:8]}"
            )
            blueprint = self.multi_step_plan(decision_id)
            transitions: list[SequentialRoomTransition] = []
            step_results: list[SequentialStepResult] = []
            transition_sequence = 0

            def move(
                to_state: SequentialRoomState,
                reason: str,
                step_id: str | None = None,
            ) -> None:
                nonlocal transition_sequence
                transition_sequence += 1
                previous = (
                    transitions[-1].to_state.value
                    if transitions
                    else None
                )
                transitions.append(
                    SequentialRoomTransition(
                        sequence=transition_sequence,
                        at=datetime.now(UTC),
                        from_state=previous,
                        to_state=to_state,
                        reason=reason,
                        step_id=step_id,
                    )
                )

            move(
                SequentialRoomState.CREATED,
                "Sequential room transaction created.",
            )
            move(
                SequentialRoomState.VALIDATING,
                "Confirmation, blueprint and all capabilities are validated.",
            )

            accepted = False
            state = SequentialRoomState.REJECTED
            executed = False
            command_count = 0
            failed_step_id = None
            reason = "Sequential room execution rejected."
            transaction_error = None

            try:
                if not confirmed:
                    reason = "Explicit confirmation is required."
                    move(state, reason)
                elif not blueprint.accepted_for_planning:
                    reason = "Blueprint is not accepted for planning."
                    move(state, reason)
                elif blueprint.status != "ready":
                    reason = f"Blueprint status is {blueprint.status!r}."
                    move(state, reason)
                elif blueprint.action != "lighting.room_off":
                    reason = (
                        "Stage 3.3 supports only lighting.room_off Decisions."
                    )
                    move(state, reason)
                elif not blueprint.stop_on_error:
                    reason = "Stage 3.3 requires stop_on_error=true."
                    move(state, reason)
                elif not blueprint.steps:
                    accepted = True
                    state = SequentialRoomState.NO_ACTION
                    reason = "No active steps require execution."
                    move(state, reason)
                else:
                    invalid_steps = []
                    for step in blueprint.steps:
                        capability = step.capability
                        command = capability.get("command") or {}
                        valid = (
                            capability.get("capability_id")
                            == "lighting.turn_off"
                            and capability.get("supported") is True
                            and capability.get("available") is True
                            and capability.get("healthy") is True
                            and capability.get("strategy")
                            == "guarded_momentary_pulse"
                            and command.get("domain") == "button"
                            and command.get("service") == "press"
                            and command.get("entity_id")
                            == step.command_entity_id
                        )
                        if not valid:
                            invalid_steps.append(step.step_id)

                    if invalid_steps:
                        reason = (
                            "One or more capabilities are not permitted by "
                            "Stage 3.3: "
                            + ", ".join(invalid_steps)
                        )
                        move(state, reason)
                    else:
                        accepted = True
                        state = SequentialRoomState.READY
                        move(
                            state,
                            "All sequential room steps passed validation.",
                        )
                        state = SequentialRoomState.RUNNING
                        move(
                            state,
                            "Sequential execution started.",
                        )

                        total_steps = len(blueprint.steps)
                        for index, step in enumerate(
                            blueprint.steps,
                            start=1,
                        ):
                            capability = dict(step.capability)
                            command = dict(
                                capability.get("command") or {}
                            )
                            feedback_before = None
                            feedback_after = None
                            command_sent = False
                            step_executed = False
                            feedback_confirmed = False
                            feedback_wait_ms = 0.0
                            step_error = None

                            try:
                                snapshot_before = self.light_snapshot(
                                    step.object_id
                                )
                                feedback_before = (
                                    snapshot_before.as_dict()
                                )

                                if not snapshot_before.available:
                                    step_state = SequentialStepState.FAILED
                                    step_reason = (
                                        "Runtime feedback is unavailable."
                                    )
                                elif snapshot_before.is_off:
                                    step_state = SequentialStepState.SKIPPED
                                    step_reason = (
                                        "Object already reports off; "
                                        "no command sent."
                                    )
                                elif not snapshot_before.is_on:
                                    step_state = SequentialStepState.FAILED
                                    step_reason = (
                                        "Runtime feedback is ambiguous."
                                    )
                                else:
                                    move(
                                        SequentialRoomState.RUNNING,
                                        "Dispatching sequential step.",
                                        step.step_id,
                                    )
                                    await self.hass.services.async_call(
                                        command["domain"],
                                        command["service"],
                                        {
                                            "entity_id":
                                            command["entity_id"]
                                        },
                                        blocking=True,
                                    )
                                    command_sent = True
                                    step_executed = True
                                    command_count += 1
                                    executed = True

                                    move(
                                        SequentialRoomState.RUNNING,
                                        "Waiting for step feedback.",
                                        step.step_id,
                                    )
                                    feedback_started = perf_counter()
                                    deadline = (
                                        feedback_started
                                        + SEQUENTIAL_FEEDBACK_TIMEOUT_SECONDS
                                    )

                                    while True:
                                        snapshot_after = self.light_snapshot(
                                            step.object_id
                                        )
                                        feedback_after = (
                                            snapshot_after.as_dict()
                                        )
                                        if (
                                            snapshot_after.available
                                            and snapshot_after.is_off
                                        ):
                                            feedback_confirmed = True
                                            break
                                        if perf_counter() >= deadline:
                                            break
                                        await asyncio.sleep(
                                            SEQUENTIAL_FEEDBACK_INTERVAL_SECONDS
                                        )

                                    feedback_wait_ms = round(
                                        (
                                            perf_counter()
                                            - feedback_started
                                        ) * 1000,
                                        2,
                                    )

                                    if feedback_confirmed:
                                        step_state = (
                                            SequentialStepState.SUCCEEDED
                                        )
                                        step_reason = (
                                            "Command sent and off feedback "
                                            "confirmed."
                                        )
                                    else:
                                        step_state = (
                                            SequentialStepState.FAILED
                                        )
                                        step_reason = (
                                            "Command sent, but off feedback "
                                            "was not confirmed before timeout."
                                        )

                            except Exception as err:  # noqa: BLE001
                                step_state = SequentialStepState.FAILED
                                step_error = (
                                    f"{type(err).__name__}: {err}"
                                )
                                step_reason = (
                                    "Sequential step failed with an exception."
                                )
                                _LOGGER.exception(
                                    "Red Queen sequential step failed: %s",
                                    step.step_id,
                                )

                            progress = round(
                                (index / total_steps) * 100,
                                1,
                            )
                            step_result = SequentialStepResult(
                                step_id=step.step_id,
                                sequence=step.sequence,
                                object_id=step.object_id,
                                object_name=step.object_name,
                                room_id=step.room_id,
                                state=step_state,
                                progress_percent=progress,
                                command_entity_id=step.command_entity_id,
                                capability=capability,
                                command=command,
                                command_sent=command_sent,
                                executed=step_executed,
                                feedback_confirmed=feedback_confirmed,
                                feedback_before=feedback_before,
                                feedback_after=feedback_after,
                                feedback_wait_ms=feedback_wait_ms,
                                reason=step_reason,
                                error=step_error,
                            )
                            step_results.append(step_result)

                            if step_state == SequentialStepState.FAILED:
                                failed_step_id = step.step_id
                                state = SequentialRoomState.FAILED
                                reason = (
                                    "Sequential execution stopped at the "
                                    "first failed step."
                                )
                                transaction_error = step_error
                                move(
                                    state,
                                    reason,
                                    step.step_id,
                                )
                                break

                        if state != SequentialRoomState.FAILED:
                            state = SequentialRoomState.SUCCEEDED
                            reason = (
                                "All sequential room steps completed."
                            )
                            move(state, reason)

            except Exception as err:  # noqa: BLE001
                state = SequentialRoomState.FAILED
                transaction_error = f"{type(err).__name__}: {err}"
                reason = (
                    "Sequential room transaction failed with an exception."
                )
                move(state, reason)
                _LOGGER.exception(
                    "Red Queen sequential room execution failed: %s",
                    transaction_id,
                )

            finished_at = datetime.now(UTC)
            completed_steps = sum(
                1 for item in step_results
                if item.state == SequentialStepState.SUCCEEDED
            )
            skipped_steps = sum(
                1 for item in step_results
                if item.state == SequentialStepState.SKIPPED
            )
            failed_steps = sum(
                1 for item in step_results
                if item.state == SequentialStepState.FAILED
            )
            total_steps = len(blueprint.steps)
            processed_steps = len(step_results)
            progress_percent = (
                round((processed_steps / total_steps) * 100, 1)
                if total_steps
                else 100.0
            )

            result = SequentialRoomResult(
                transaction_id=transaction_id,
                generated_at=generated_at,
                finished_at=finished_at,
                duration_ms=round(
                    (perf_counter() - started_perf) * 1000,
                    2,
                ),
                decision_id=decision_id,
                plan_id=blueprint.plan_id,
                confirmed=confirmed,
                accepted=accepted,
                state=state,
                dry_run=False,
                executed=executed,
                command_count=command_count,
                total_steps=total_steps,
                completed_steps=completed_steps,
                skipped_steps=skipped_steps,
                failed_steps=failed_steps,
                progress_percent=progress_percent,
                failed_step_id=failed_step_id,
                reason=reason,
                error=transaction_error,
                transitions=tuple(transitions),
                steps=tuple(step_results),
                blueprint=blueprint.as_dict(),
                executor_version="1.0-stage3.3",
            )
            self.last_sequential_room_result = result
            self.sequential_room_audit.append(result)
            self.performance.record(
                ACTION_SEQUENTIAL_ROOM_EXECUTE,
                result.duration_ms,
                finished_at,
            )
            return result

    def real_step_audit_snapshot(self) -> dict[str, Any]:
        """Return the bounded in-memory real-step audit."""
        started = perf_counter()
        records = [
            item.as_dict()
            for item in reversed(self.real_step_audit)
        ]
        self.performance.record(
            ACTION_REAL_STEP_AUDIT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "count": len(records),
            "limit": REAL_STEP_AUDIT_LIMIT,
            "records": records,
        }


    def access_execution_audit_snapshot(self) -> dict[str, Any]:
        """Return the bounded audit of Access object execution attempts."""
        started = perf_counter()
        records = [
            item.as_dict()
            for item in reversed(self.access_execution_audit)
        ]
        self.performance.record(
            ACTION_ACCESS_EXECUTION_AUDIT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "count": len(records),
            "limit": ACCESS_EXECUTION_AUDIT_LIMIT,
            "records": records,
        }

    async def async_access_object_execute(
        self,
        object_id: str,
        capability_id: str,
        confirmed: bool,
    ) -> RealStepResult:
        """Execute one tightly constrained Access capability."""
        async with self._execution_lock:
            started_perf = perf_counter()
            generated_at = datetime.now(UTC)
            execution_id = (
                f"axe_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
                f"{uuid4().hex[:8]}"
            )
            plan_id = (
                f"access_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
                f"{uuid4().hex[:8]}"
            )
            transitions: list[RealStepTransition] = []
            transition_sequence = 0

            def move(to_state: RealStepState, reason: str) -> None:
                nonlocal transition_sequence
                transition_sequence += 1
                previous = (
                    transitions[-1].to_state.value
                    if transitions
                    else None
                )
                transitions.append(
                    RealStepTransition(
                        sequence=transition_sequence,
                        at=datetime.now(UTC),
                        from_state=previous,
                        to_state=to_state,
                        reason=reason,
                    )
                )

            move(
                RealStepState.CREATED,
                "Access object transaction created.",
            )
            move(
                RealStepState.VALIDATING,
                "Confirmation, object, capability and feedback are validated.",
            )

            accepted = False
            state = RealStepState.REJECTED
            command_sent = False
            executed = False
            feedback_confirmed = False
            feedback_wait_ms = 0.0
            command_outcome = CommandOutcome(
                status=CommandStatus.NOT_ATTEMPTED,
                attempted=False,
                dispatched=False,
                completed=False,
                message="Command has not been evaluated yet.",
            )
            effect_outcome = EffectOutcome(
                status=EffectStatus.NOT_EXECUTED,
                required=False,
                expected=None,
                observed=None,
                confirmed=False,
                wait_ms=0.0,
                message="Effect has not been evaluated yet.",
            )
            transition_effect = None
            terminal_effect = None
            capability = None
            command = None
            feedback_before = None
            feedback_after = None
            reason = "Access execution rejected."
            error = None
            result_code = AccessResultCatalog.CAPABILITY_UNQUALIFIED

            blueprint = {
                "api_version": "1.0",
                "plan_id": plan_id,
                "action": capability_id,
                "target": {"object_id": object_id},
                "status": "validating",
                "confirmed": confirmed,
                "read_only": False,
                "executor_scope": "access_object",
            }

            try:
                house = self._require_house()
                opening = house.openings.get(object_id)

                if not confirmed:
                    reason = "Explicit confirmation is required."
                elif capability_id not in {
                    "access.lock",
                    "access.unlock",
                    "access.door_open",
                    "access.toggle",
                }:
                    result_code = (
                        AccessResultCatalog.CAPABILITY_NOT_PERMITTED
                    )
                    reason = (
                        "WP-4.3.2B.5.1 permits access.lock, access.unlock, "
                        "access.door_open and access.toggle."
                    )
                elif opening is None:
                    result_code = AccessResultCatalog.OBJECT_NOT_FOUND
                    reason = "Access object does not exist."
                elif not opening.enabled:
                    result_code = AccessResultCatalog.OBJECT_DISABLED
                    reason = "Access object is disabled."
                else:
                    runtime = self.access_object_snapshot(object_id)
                    resolved = ExecutionCapabilityAdapter.resolve(
                        opening,
                        capability_id,
                        runtime,
                    )
                    capability = resolved.as_dict()
                    command = dict(capability.get("command") or {})
                    feedback_before = runtime.as_dict()

                    if capability_id == "access.toggle":
                        capability_valid = (
                            resolved.supported
                            and resolved.available
                            and resolved.healthy
                            and resolved.strategy == "guarded_osc_pulse"
                            and resolved.command_domain == "button"
                            and resolved.command_service == "press"
                            and bool(resolved.command_entity_id)
                            and resolved.feedback_required
                            and len(resolved.feedback_entity_ids) == 2
                        )

                        stable_initial_states = {"open", "closed"}

                        if not capability_valid:
                            result_code = (
                                AccessResultCatalog.CAPABILITY_UNQUALIFIED
                            )
                            reason = (
                                "Resolved garage OSC capability is not "
                                "healthy and qualified for execution."
                            )
                        elif not runtime.available:
                            result_code = (
                                AccessResultCatalog.FEEDBACK_UNAVAILABLE
                            )
                            reason = (
                                "Garage end-position feedback is unavailable."
                            )
                        elif runtime.state == "error":
                            result_code = (
                                AccessResultCatalog.CONTRADICTORY_FEEDBACK
                            )
                            reason = (
                                "Contradictory garage end-position feedback "
                                "prevents execution."
                            )
                        elif runtime.state == "moving":
                            result_code = (
                                AccessResultCatalog.TRANSITION_IN_PROGRESS
                            )
                            reason = (
                                "Garage door is already moving; another OSC "
                                "pulse is not permitted."
                            )
                        elif runtime.state == "intermediate_open":
                            result_code = (
                                AccessResultCatalog.INTERMEDIATE_STATE
                            )
                            reason = (
                                "Garage door is in an intermediate position; "
                                "direction is ambiguous and toggle is not "
                                "permitted in this qualification stage."
                            )
                        elif runtime.state not in stable_initial_states:
                            result_code = (
                                AccessResultCatalog.INVALID_INITIAL_STATE
                            )
                            reason = (
                                "Garage door does not report a stable open "
                                "or closed end position."
                            )
                        else:
                            accepted = True
                            initial_state = runtime.state
                            expected_terminal_state = (
                                "open"
                                if initial_state == "closed"
                                else "closed"
                            )
                            blueprint["status"] = "ready"
                            blueprint["initial_state"] = initial_state
                            blueprint["expected_transition"] = (
                                f"{initial_state}->moving"
                            )
                            blueprint["expected_terminal_state"] = (
                                expected_terminal_state
                            )
                            blueprint["confirmation_policy"] = (
                                resolved.confirmation_policy.as_dict()
                            )

                            move(
                                RealStepState.READY,
                                (
                                    f"Garage door is stably {initial_state}; "
                                    "healthy OSC capability is ready."
                                ),
                            )
                            move(
                                RealStepState.DISPATCHING,
                                "Dispatching exactly one garage OSC pulse.",
                            )

                            command_outcome = (
                                await self.command_dispatcher.async_dispatch(
                                    resolved
                                )
                            )
                            command_sent = command_outcome.dispatched
                            executed = command_outcome.completed

                            if not command_outcome.completed:
                                state = RealStepState.FAILED
                                result_code = (
                                    AccessResultCatalog.COMMAND_DISPATCH_FAILED
                                )
                                reason = "Garage OSC command dispatch failed."
                                effect_outcome = EffectOutcome(
                                    status=EffectStatus.NOT_EXECUTED,
                                    required=True,
                                    expected="moving",
                                    observed=runtime.state,
                                    confirmed=False,
                                    wait_ms=0.0,
                                    message=reason,
                                )
                                transition_effect = effect_outcome
                                terminal_effect = EffectOutcome(
                                    status=EffectStatus.NOT_EXECUTED,
                                    required=True,
                                    expected=expected_terminal_state,
                                    observed=runtime.state,
                                    confirmed=False,
                                    wait_ms=0.0,
                                    message=(
                                        "Terminal effect was not evaluated "
                                        "because dispatch failed."
                                    ),
                                )
                                move(state, reason)
                            else:
                                move(
                                    RealStepState.OBSERVING_EFFECT,
                                    "Observing required garage movement start.",
                                )
                                (
                                    transition_effect,
                                    transition_snapshot,
                                ) = await self.effect_observer.async_observe(
                                    policy=resolved.confirmation_policy,
                                    expected="moving",
                                    snapshot_factory=lambda: (
                                        self.access_object_snapshot(object_id)
                                    ),
                                    predicate=lambda item: (
                                        item.available
                                        and item.state
                                        in {
                                            "moving",
                                            expected_terminal_state,
                                        }
                                    ),
                                    observed_factory=lambda item: item.state,
                                )

                                if not transition_effect.confirmed:
                                    effect_outcome = transition_effect
                                    feedback_after = (
                                        transition_snapshot.as_dict()
                                    )
                                    feedback_wait_ms = (
                                        transition_effect.wait_ms
                                    )
                                    feedback_confirmed = False
                                    state = RealStepState.FAILED
                                    result_code = (
                                        AccessResultCatalog.TRANSITION_TIMEOUT
                                    )
                                    reason = (
                                        "Garage OSC command was sent, but no "
                                        "movement or opposite end position "
                                        "was observed before timeout."
                                    )
                                    move(state, reason)
                                else:
                                    move(
                                        RealStepState.WAITING_TERMINAL_EFFECT,
                                        (
                                            "Movement start confirmed; "
                                            f"waiting for garage end position "
                                            f"{expected_terminal_state}."
                                        ),
                                    )

                                    terminal_policy = ConfirmationPolicy(
                                        required_before_dispatch=True,
                                        effect_confirmation=(
                                            EffectConfirmationMode.REQUIRED
                                        ),
                                        observe_timeout_ms=(
                                            GARAGE_TERMINAL_TIMEOUT_MS
                                        ),
                                        observe_interval_ms=(
                                            GARAGE_TERMINAL_INTERVAL_MS
                                        ),
                                    )
                                    (
                                        terminal_effect,
                                        terminal_snapshot,
                                    ) = (
                                        await self.effect_observer
                                        .async_observe(
                                            policy=terminal_policy,
                                            expected=(
                                                expected_terminal_state
                                            ),
                                            snapshot_factory=lambda: (
                                                self
                                                .access_object_snapshot(
                                                    object_id
                                                )
                                            ),
                                            predicate=lambda item: (
                                                item.available
                                                and item.state
                                                == expected_terminal_state
                                            ),
                                            observed_factory=lambda item: (
                                                item.state
                                            ),
                                        )
                                    )

                                    effect_outcome = terminal_effect
                                    feedback_after = (
                                        terminal_snapshot.as_dict()
                                    )
                                    feedback_wait_ms = round(
                                        transition_effect.wait_ms
                                        + terminal_effect.wait_ms,
                                        2,
                                    )
                                    feedback_confirmed = (
                                        terminal_effect.confirmed
                                    )

                                    if terminal_effect.confirmed:
                                        state = RealStepState.SUCCEEDED
                                        result_code = AccessResultCatalog.SUCCEEDED
                                        reason = (
                                            "Garage OSC command succeeded; "
                                            f"transition from {initial_state} "
                                            "to moving and terminal state "
                                            f"{expected_terminal_state} were "
                                            "confirmed."
                                        )
                                    else:
                                        state = RealStepState.FAILED
                                        result_code = (
                                            AccessResultCatalog
                                            .TERMINAL_STATE_TIMEOUT
                                        )
                                        reason = (
                                            "Garage movement started, but "
                                            f"terminal state "
                                            f"{expected_terminal_state} was "
                                            "not confirmed before timeout."
                                        )
                                    move(state, reason)

                    elif capability_id == "access.door_open":
                        capability_valid = (
                            resolved.supported
                            and resolved.available
                            and resolved.healthy
                            and resolved.strategy
                            == "observable_confirmed_momentary_pulse"
                            and resolved.command_domain == "button"
                            and resolved.command_service == "press"
                            and bool(resolved.command_entity_id)
                            and len(resolved.feedback_entity_ids) == 1
                        )

                        if not capability_valid:
                            result_code = (
                                AccessResultCatalog.CAPABILITY_UNQUALIFIED
                            )
                            reason = (
                                "Resolved door-opener capability is not "
                                "healthy and qualified for execution."
                            )
                        elif not runtime.available:
                            result_code = (
                                AccessResultCatalog.FEEDBACK_UNAVAILABLE
                            )
                            reason = (
                                "Door-contact feedback is unavailable."
                            )
                        elif runtime.is_open:
                            accepted = True
                            state = RealStepState.NO_ACTION
                            feedback_confirmed = True
                            feedback_after = feedback_before
                            result_code = (
                                AccessResultCatalog.ALREADY_SATISFIED
                            )
                            reason = (
                                "Door already reports open; no opener "
                                "command sent."
                            )
                            command_outcome = CommandOutcome(
                                status=CommandStatus.NOT_ATTEMPTED,
                                attempted=False,
                                dispatched=False,
                                completed=False,
                                domain=resolved.command_domain,
                                service=resolved.command_service,
                                entity_id=resolved.command_entity_id,
                                message=reason,
                            )
                            effect_outcome = EffectOutcome(
                                status=EffectStatus.CONFIRMED,
                                required=False,
                                expected="open",
                                observed="open",
                                confirmed=True,
                                wait_ms=0.0,
                                message=(
                                    "Desired optional effect was already "
                                    "present before dispatch."
                                ),
                            )
                            move(state, reason)
                        else:
                            accepted = True
                            blueprint["status"] = "ready"
                            blueprint["confirmation_policy"] = (
                                resolved.confirmation_policy.as_dict()
                            )
                            move(
                                RealStepState.READY,
                                "Closed door and healthy observable door-"
                                "opener capability are ready.",
                            )
                            move(
                                RealStepState.DISPATCHING,
                                "Dispatching exactly one door-opener pulse.",
                            )

                            command_outcome = (
                                await self.command_dispatcher.async_dispatch(
                                    resolved
                                )
                            )
                            command_sent = command_outcome.dispatched
                            executed = command_outcome.completed

                            if not command_outcome.completed:
                                state = RealStepState.FAILED
                                result_code = (
                                    AccessResultCatalog.COMMAND_DISPATCH_FAILED
                                )
                                reason = (
                                    "Door-opener command dispatch failed."
                                )
                                effect_outcome = EffectOutcome(
                                    status=EffectStatus.NOT_EXECUTED,
                                    required=False,
                                    expected="open",
                                    observed=runtime.state,
                                    confirmed=False,
                                    wait_ms=0.0,
                                    message=reason,
                                )
                                move(state, reason)
                            else:
                                move(
                                    RealStepState.OBSERVING_EFFECT,
                                    "Observing optional door-open effect.",
                                )
                                (
                                    effect_outcome,
                                    observed_snapshot,
                                ) = await self.effect_observer.async_observe(
                                    policy=resolved.confirmation_policy,
                                    expected="open",
                                    snapshot_factory=lambda: (
                                        self.access_object_snapshot(
                                            object_id
                                        )
                                    ),
                                    predicate=lambda item: item.is_open,
                                    observed_factory=lambda item: item.state,
                                )
                                feedback_after = (
                                    observed_snapshot.as_dict()
                                )
                                feedback_wait_ms = effect_outcome.wait_ms
                                feedback_confirmed = (
                                    effect_outcome.confirmed
                                )
                                state = RealStepState.SUCCEEDED
                                result_code = (
                                    AccessResultCatalog.SUCCEEDED
                                    if effect_outcome.confirmed
                                    else AccessResultCatalog
                                    .OPTIONAL_EFFECT_NOT_OBSERVED
                                )
                                reason = (
                                    "Door-opener command succeeded and "
                                    "door-open effect was confirmed."
                                    if effect_outcome.confirmed
                                    else
                                    "Door-opener command succeeded; optional "
                                    "door-open effect was not observed."
                                )
                                move(state, reason)

                    else:
                        capability_valid = (
                            resolved.supported
                            and resolved.available
                            and resolved.healthy
                            and resolved.strategy
                            == "guarded_button_with_lock_feedback"
                            and resolved.command_domain == "button"
                            and resolved.command_service == "press"
                            and bool(resolved.command_entity_id)
                            and resolved.feedback_required
                            and len(resolved.feedback_entity_ids) == 1
                        )

                        if not capability_valid:
                            result_code = (
                                AccessResultCatalog.CAPABILITY_UNQUALIFIED
                            )
                            reason = (
                                "Resolved Access capability is not healthy "
                                "and qualified for execution."
                            )
                        elif not runtime.available:
                            result_code = (
                                AccessResultCatalog.FEEDBACK_UNAVAILABLE
                            )
                            reason = (
                                "Required Access feedback is unavailable."
                            )
                        elif runtime.is_open:
                            result_code = (
                                AccessResultCatalog.OPEN_DOOR_LOCK_REJECTED
                            )
                            reason = (
                                "Door is open; lock command is not permitted."
                            )
                        else:
                            desired_lock_state = (
                                "locked"
                                if capability_id == "access.lock"
                                else "unlocked"
                            )
                            required_initial_state = (
                                "unlocked"
                                if capability_id == "access.lock"
                                else "locked"
                            )

                            if runtime.lock_state == desired_lock_state:
                                accepted = True
                                state = RealStepState.NO_ACTION
                                feedback_confirmed = True
                                feedback_after = feedback_before
                                result_code = (
                                    AccessResultCatalog.ALREADY_SATISFIED
                                )
                                reason = (
                                    f"Door already reports "
                                    f"{desired_lock_state}; no command sent."
                                )
                                command_outcome = CommandOutcome(
                                    status=CommandStatus.NOT_ATTEMPTED,
                                    attempted=False,
                                    dispatched=False,
                                    completed=False,
                                    domain=resolved.command_domain,
                                    service=resolved.command_service,
                                    entity_id=resolved.command_entity_id,
                                    message=reason,
                                )
                                effect_outcome = EffectOutcome(
                                    status=EffectStatus.CONFIRMED,
                                    required=True,
                                    expected=desired_lock_state,
                                    observed=runtime.lock_state,
                                    confirmed=True,
                                    wait_ms=0.0,
                                    message=(
                                        "Desired effect was already present "
                                        "before dispatch."
                                    ),
                                )
                                move(state, reason)

                            elif (
                                runtime.lock_state
                                != required_initial_state
                            ):
                                result_code = (
                                    AccessResultCatalog.INVALID_INITIAL_STATE
                                )
                                reason = (
                                    "Lock feedback is neither locked nor "
                                    "unlocked."
                                )

                            else:
                                accepted = True
                                blueprint["status"] = "ready"
                                blueprint["confirmation_policy"] = (
                                    resolved.confirmation_policy.as_dict()
                                )
                                move(
                                    RealStepState.READY,
                                    (
                                        f"Closed, {required_initial_state} "
                                        f"door and healthy {capability_id} "
                                        "capability are ready."
                                    ),
                                )
                                move(
                                    RealStepState.DISPATCHING,
                                    (
                                        f"Dispatching exactly one "
                                        f"{capability_id} command pulse."
                                    ),
                                )

                                command_outcome = (
                                    await self.command_dispatcher
                                    .async_dispatch(resolved)
                                )
                                command_sent = (
                                    command_outcome.dispatched
                                )
                                executed = command_outcome.completed

                                if not command_outcome.completed:
                                    state = RealStepState.FAILED
                                    result_code = (
                                        AccessResultCatalog
                                        .COMMAND_DISPATCH_FAILED
                                    )
                                    reason = (
                                        f"{capability_id} command dispatch "
                                        "failed."
                                    )
                                    effect_outcome = EffectOutcome(
                                        status=EffectStatus.NOT_EXECUTED,
                                        required=True,
                                        expected=desired_lock_state,
                                        observed=runtime.lock_state,
                                        confirmed=False,
                                        wait_ms=0.0,
                                        message=reason,
                                    )
                                    move(state, reason)
                                else:
                                    move(
                                        RealStepState.WAITING_FEEDBACK,
                                        (
                                            f"Waiting for "
                                            f"{desired_lock_state} feedback."
                                        ),
                                    )
                                    (
                                        effect_outcome,
                                        observed_snapshot,
                                    ) = (
                                        await self.effect_observer
                                        .async_observe(
                                            policy=(
                                                resolved
                                                .confirmation_policy
                                            ),
                                            expected=desired_lock_state,
                                            snapshot_factory=lambda: (
                                                self
                                                .access_object_snapshot(
                                                    object_id
                                                )
                                            ),
                                            predicate=lambda item: (
                                                item.available
                                                and item.lock_state
                                                == desired_lock_state
                                            ),
                                            observed_factory=lambda item: (
                                                item.lock_state
                                            ),
                                        )
                                    )
                                    feedback_after = (
                                        observed_snapshot.as_dict()
                                    )
                                    feedback_wait_ms = (
                                        effect_outcome.wait_ms
                                    )
                                    feedback_confirmed = (
                                        effect_outcome.confirmed
                                    )

                                    if effect_outcome.confirmed:
                                        state = RealStepState.SUCCEEDED
                                        result_code = (
                                            AccessResultCatalog.SUCCEEDED
                                        )
                                        reason = (
                                            f"{capability_id} command sent "
                                            f"and {desired_lock_state} "
                                            "feedback confirmed."
                                        )
                                    else:
                                        state = RealStepState.FAILED
                                        result_code = (
                                            AccessResultCatalog
                                            .REQUIRED_EFFECT_TIMEOUT
                                        )
                                        reason = (
                                            f"{capability_id} command was "
                                            f"sent, but "
                                            f"{desired_lock_state} feedback "
                                            "was not confirmed before "
                                            "timeout."
                                        )
                                    move(state, reason)

                if (
                    state == RealStepState.REJECTED
                    and transitions[-1].to_state
                    != RealStepState.REJECTED
                ):
                    move(RealStepState.REJECTED, reason)

            except Exception as err:  # noqa: BLE001
                state = RealStepState.FAILED
                result_code = AccessResultCatalog.EXECUTOR_EXCEPTION
                error = f"{type(err).__name__}: {err}"
                reason = "Access execution failed with an exception."
                command_outcome = CommandOutcome(
                    status=CommandStatus.FAILED,
                    attempted=True,
                    dispatched=command_sent,
                    completed=False,
                    domain=(command or {}).get("domain"),
                    service=(command or {}).get("service"),
                    entity_id=(command or {}).get("entity_id"),
                    message=error,
                )
                effect_outcome = EffectOutcome(
                    status=EffectStatus.NOT_EXECUTED,
                    required=bool(
                        (capability or {})
                        .get("feedback", {})
                        .get("required")
                    ),
                    expected=None,
                    observed=None,
                    confirmed=False,
                    wait_ms=feedback_wait_ms,
                    message=reason,
                )
                move(state, reason)
                _LOGGER.exception(
                    "Red Queen Access object execution failed: %s",
                    execution_id,
                )

            if state == RealStepState.REJECTED:
                command_outcome = CommandOutcome(
                    status=CommandStatus.REJECTED,
                    attempted=False,
                    dispatched=False,
                    completed=False,
                    domain=(command or {}).get("domain"),
                    service=(command or {}).get("service"),
                    entity_id=(command or {}).get("entity_id"),
                    message=reason,
                )
                effect_outcome = EffectOutcome(
                    status=EffectStatus.NOT_EXECUTED,
                    required=False,
                    expected=None,
                    observed=None,
                    confirmed=False,
                    wait_ms=0.0,
                    message="No effect evaluation because command was rejected.",
                )

            blueprint["status"] = state.value
            blueprint["accepted"] = accepted
            blueprint["executed"] = executed

            finished_at = datetime.now(UTC)
            result = RealStepResult(
                execution_id=execution_id,
                generated_at=generated_at,
                finished_at=finished_at,
                duration_ms=round(
                    (perf_counter() - started_perf) * 1000,
                    2,
                ),
                decision_id=f"direct.{capability_id}.{object_id}",
                plan_id=plan_id,
                confirmed=confirmed,
                accepted=accepted,
                state=state,
                dry_run=False,
                executed=executed,
                command_sent=command_sent,
                feedback_confirmed=feedback_confirmed,
                object_id=object_id,
                step_id=f"{plan_id}_step_001",
                capability=capability,
                command=command,
                feedback_before=feedback_before,
                feedback_after=feedback_after,
                feedback_wait_ms=feedback_wait_ms,
                reason=reason,
                error=error,
                transitions=tuple(transitions),
                blueprint=blueprint,
                executor_version="1.4.2-stage4.3.2B.5.2.2",
                command_outcome=command_outcome,
                effect_outcome=effect_outcome,
                transition_effect=transition_effect,
                terminal_effect=terminal_effect,
                result_code=result_code,
            )
            self.last_access_execution_result = result
            self.access_execution_audit.append(result)
            self.performance.record(
                ACTION_ACCESS_OBJECT_EXECUTE,
                result.duration_ms,
                finished_at,
            )
            return result

    async def async_real_step_execute(
        self,
        decision_id: str,
        confirmed: bool,
    ) -> RealStepResult:
        """Execute exactly one generic guarded step and verify feedback."""
        async with self._execution_lock:
            started_perf = perf_counter()
            generated_at = datetime.now(UTC)
            execution_id = (
                f"rse_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
                f"{uuid4().hex[:8]}"
            )
            blueprint = self.multi_step_plan(decision_id)
            transitions: list[RealStepTransition] = []
            transition_sequence = 0

            def move(to_state: RealStepState, reason: str) -> None:
                nonlocal transition_sequence
                transition_sequence += 1
                previous = (
                    transitions[-1].to_state.value
                    if transitions
                    else None
                )
                transitions.append(
                    RealStepTransition(
                        sequence=transition_sequence,
                        at=datetime.now(UTC),
                        from_state=previous,
                        to_state=to_state,
                        reason=reason,
                    )
                )

            move(RealStepState.CREATED, "Real-step transaction created.")
            move(
                RealStepState.VALIDATING,
                "Confirmation, blueprint and capability are being validated.",
            )

            accepted = False
            state = RealStepState.REJECTED
            command_sent = False
            executed = False
            feedback_confirmed = False
            feedback_wait_ms = 0.0
            object_id = None
            step_id = None
            capability = None
            command = None
            feedback_before = None
            feedback_after = None
            reason = "Real-step execution rejected."
            error = None

            try:
                if not confirmed:
                    reason = "Explicit confirmation is required."
                elif not blueprint.accepted_for_planning:
                    reason = "Blueprint is not accepted for planning."
                elif blueprint.status != "ready":
                    reason = f"Blueprint status is {blueprint.status!r}."
                elif blueprint.action != "lighting.room_off":
                    reason = (
                        "Stage 3.2 supports only lighting.room_off Decisions."
                    )
                elif len(blueprint.steps) == 0:
                    state = RealStepState.NO_ACTION
                    accepted = True
                    reason = "No active step requires execution."
                    move(state, reason)
                elif len(blueprint.steps) != 1:
                    reason = (
                        "Stage 3.2 requires exactly one active blueprint step."
                    )
                else:
                    step = blueprint.steps[0]
                    object_id = step.object_id
                    step_id = step.step_id
                    capability = dict(step.capability)
                    command = dict(capability.get("command") or {})
                    feedback_before = self.light_snapshot(
                        object_id
                    ).as_dict()

                    capability_valid = (
                        capability.get("capability_id")
                        == "lighting.turn_off"
                        and capability.get("supported") is True
                        and capability.get("available") is True
                        and capability.get("healthy") is True
                        and capability.get("strategy")
                        == "guarded_momentary_pulse"
                        and command.get("domain") == "button"
                        and command.get("service") == "press"
                        and command.get("entity_id")
                        == step.command_entity_id
                    )

                    if not capability_valid:
                        reason = (
                            "Step capability is not permitted by Stage 3.2."
                        )
                    elif feedback_before.get("available") is not True:
                        reason = "Runtime feedback is unavailable."
                    elif feedback_before.get("is_on") is not True:
                        state = RealStepState.NO_ACTION
                        accepted = True
                        reason = (
                            "Object already reports off; no command sent."
                        )
                        move(state, reason)
                    else:
                        accepted = True
                        move(
                            RealStepState.READY,
                            "Exactly one healthy guarded step is ready.",
                        )
                        move(
                            RealStepState.DISPATCHING,
                            "Dispatching exactly one capability command.",
                        )

                        await self.hass.services.async_call(
                            command["domain"],
                            command["service"],
                            {"entity_id": command["entity_id"]},
                            blocking=True,
                        )
                        command_sent = True
                        executed = True

                        move(
                            RealStepState.WAITING_FEEDBACK,
                            "Waiting for target feedback after command.",
                        )
                        feedback_started = perf_counter()
                        deadline = (
                            feedback_started
                            + REAL_STEP_FEEDBACK_TIMEOUT_SECONDS
                        )

                        while True:
                            snapshot = self.light_snapshot(object_id)
                            feedback_after = snapshot.as_dict()
                            if (
                                snapshot.available
                                and snapshot.is_off
                            ):
                                feedback_confirmed = True
                                break
                            if perf_counter() >= deadline:
                                break
                            await asyncio.sleep(
                                REAL_STEP_FEEDBACK_INTERVAL_SECONDS
                            )

                        feedback_wait_ms = round(
                            (perf_counter() - feedback_started) * 1000,
                            2,
                        )

                        if feedback_confirmed:
                            state = RealStepState.SUCCEEDED
                            reason = (
                                "Command sent and off feedback confirmed."
                            )
                        else:
                            state = RealStepState.FAILED
                            reason = (
                                "Command was sent, but off feedback was not "
                                "confirmed before timeout."
                            )
                        move(state, reason)

                if (
                    state == RealStepState.REJECTED
                    and transitions[-1].to_state
                    != RealStepState.REJECTED
                ):
                    move(RealStepState.REJECTED, reason)

            except Exception as err:  # noqa: BLE001
                state = RealStepState.FAILED
                error = f"{type(err).__name__}: {err}"
                reason = "Real-step execution failed with an exception."
                move(state, reason)
                _LOGGER.exception(
                    "Red Queen real-step execution failed: %s",
                    execution_id,
                )

            finished_at = datetime.now(UTC)
            result = RealStepResult(
                execution_id=execution_id,
                generated_at=generated_at,
                finished_at=finished_at,
                duration_ms=round(
                    (perf_counter() - started_perf) * 1000,
                    2,
                ),
                decision_id=decision_id,
                plan_id=blueprint.plan_id,
                confirmed=confirmed,
                accepted=accepted,
                state=state,
                dry_run=False,
                executed=executed,
                command_sent=command_sent,
                feedback_confirmed=feedback_confirmed,
                object_id=object_id,
                step_id=step_id,
                capability=capability,
                command=command,
                feedback_before=feedback_before,
                feedback_after=feedback_after,
                feedback_wait_ms=feedback_wait_ms,
                reason=reason,
                error=error,
                transitions=tuple(transitions),
                blueprint=blueprint.as_dict(),
                executor_version="1.0-stage3.2",
            )
            self.last_real_step_result = result
            self.real_step_audit.append(result)
            self.performance.record(
                ACTION_REAL_STEP_EXECUTE,
                result.duration_ms,
                finished_at,
            )
            return result

    def generic_transactions_snapshot(self) -> dict[str, Any]:
        started = perf_counter()
        records=[x.as_dict() for x in reversed(self.generic_transaction_audit)]
        self.performance.record(
            ACTION_GENERIC_TRANSACTIONS_SNAPSHOT,
            round((perf_counter()-started)*1000,2),
            datetime.now(UTC),
        )
        return {"count":len(records),"limit":GENERIC_TRANSACTION_AUDIT_LIMIT,"records":records}

    def generic_transaction_run(
        self,
        decision_id: str,
        confirmed: bool,
    ) -> GenericTransactionResult:
        started_perf=perf_counter()
        generated_at=datetime.now(UTC)
        transaction_id=(
            f"gtx_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
            f"{uuid4().hex[:8]}"
        )
        blueprint=self.multi_step_plan(decision_id)
        transitions=[]
        seq=0

        def move(to_state, reason, step_id=None):
            nonlocal seq
            seq += 1
            previous=transitions[-1].to_state.value if transitions else None
            transitions.append(GenericTransactionTransition(
                sequence=seq,
                at=datetime.now(UTC),
                from_state=previous,
                to_state=to_state,
                reason=reason,
                step_id=step_id,
            ))

        move(GenericTransactionState.CREATED,"Generic transaction created.")
        move(GenericTransactionState.VALIDATING,"Blueprint and confirmation are being validated.")

        processed=[]
        if not confirmed:
            move(GenericTransactionState.REJECTED,"Explicit confirmation is required.")
            state=GenericTransactionState.REJECTED
            accepted=False
            reason="Explicit confirmation is required."
        elif not blueprint.accepted_for_planning or blueprint.status!="ready":
            move(GenericTransactionState.REJECTED,"Blueprint is not ready.")
            state=GenericTransactionState.REJECTED
            accepted=False
            reason="Blueprint is not ready."
        elif not blueprint.steps:
            move(GenericTransactionState.NO_ACTION,"No active steps require execution.")
            state=GenericTransactionState.NO_ACTION
            accepted=True
            reason="No active steps require execution."
        else:
            accepted=True
            move(GenericTransactionState.READY,"Transaction passed validation.")
            move(GenericTransactionState.RUNNING,"Generic executor started dry-run processing.")
            failed=False
            for step in blueprint.steps:
                cap=step.capability
                ready=(
                    cap.get("supported") is True
                    and cap.get("available") is True
                    and cap.get("healthy") is True
                )
                if not ready:
                    processed.append({
                        "step_id":step.step_id,
                        "sequence":step.sequence,
                        "object_id":step.object_id,
                        "state":"failed",
                        "command_sent":False,
                        "executed":False,
                        "reason":"Capability is not executable.",
                    })
                    move(GenericTransactionState.FAILED,"Step capability validation failed.",step.step_id)
                    failed=True
                    break
                move(GenericTransactionState.WAITING_FEEDBACK,"Feedback would be checked before command.",step.step_id)
                processed.append({
                    "step_id":step.step_id,
                    "sequence":step.sequence,
                    "object_id":step.object_id,
                    "state":"simulated_success",
                    "command_sent":False,
                    "executed":False,
                    "reason":"Step passed generic dry-run state transitions.",
                    "capability":cap,
                })
                move(GenericTransactionState.RUNNING,"Step dry-run completed; continuing sequence.",step.step_id)
            if failed:
                state=GenericTransactionState.FAILED
                reason="Generic transaction failed during dry-run validation."
            else:
                move(GenericTransactionState.SUCCEEDED,"All steps passed the generic dry-run executor.")
                state=GenericTransactionState.SUCCEEDED
                reason="All steps passed the generic dry-run executor."

        finished_at=datetime.now(UTC)
        total=len(blueprint.steps)
        done=len(processed)
        result=GenericTransactionResult(
            transaction_id=transaction_id,
            generated_at=generated_at,
            finished_at=finished_at,
            duration_ms=round((perf_counter()-started_perf)*1000,2),
            decision_id=decision_id,
            plan_id=blueprint.plan_id,
            confirmed=confirmed,
            accepted=accepted,
            state=state,
            dry_run=True,
            executed=False,
            eligible_for_commit=False,
            total_steps=total,
            processed_steps=done,
            progress_percent=round((done/total)*100,1) if total else 100.0,
            reason=reason,
            transitions=tuple(transitions),
            steps=tuple(processed),
            blueprint=blueprint.as_dict(),
            executor_version="1.0-stage3.1",
        )
        self.last_generic_transaction=result
        self.generic_transaction_audit.append(result)
        self.performance.record(ACTION_GENERIC_TRANSACTION_RUN,result.duration_ms,finished_at)
        return result

    def multi_step_simulations_snapshot(self) -> dict[str, Any]:
        """Return the bounded in-memory multi-step simulation audit."""
        started = perf_counter()
        records = [
            item.as_dict()
            for item in reversed(self.multi_step_simulation_audit)
        ]
        self.performance.record(
            ACTION_MULTI_STEP_SIMULATIONS_SNAPSHOT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "count": len(records),
            "limit": MULTI_STEP_SIMULATION_AUDIT_LIMIT,
            "records": records,
        }

    def multi_step_simulate(
        self,
        decision_id: str,
        confirmed: bool,
    ) -> MultiStepSimulation:
        """Simulate a multi-step transaction without sending commands."""
        started_perf = perf_counter()
        generated_at = datetime.now(UTC)
        simulation_id = (
            f"sim_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
            f"{uuid4().hex[:8]}"
        )

        blueprint = self.multi_step_plan(decision_id)
        errors = list(blueprint.validation_errors)
        simulated_steps: list[MultiStepSimulationStep] = []

        accepted = (
            confirmed
            and blueprint.accepted_for_planning
            and blueprint.status == "ready"
            and not errors
        )

        if not confirmed:
            status = MultiStepSimulationStatus.REJECTED
            reason = "Explicit confirmation is required for commit simulation."
        elif not blueprint.accepted_for_planning:
            status = MultiStepSimulationStatus.REJECTED
            reason = "Blueprint is not accepted for planning."
        elif blueprint.status != "ready":
            status = MultiStepSimulationStatus.REJECTED
            reason = (
                f"Blueprint status is {blueprint.status!r}, not 'ready'."
            )
        elif errors:
            status = MultiStepSimulationStatus.FAILED
            reason = "Blueprint contains validation errors."
        elif not blueprint.steps:
            status = MultiStepSimulationStatus.NO_ACTION
            reason = "No active steps require execution."
        else:
            total = len(blueprint.steps)
            for index, step in enumerate(blueprint.steps, start=1):
                capability = step.capability
                capability_ready = (
                    capability.get("supported") is True
                    and capability.get("available") is True
                    and capability.get("healthy") is True
                    and capability.get("strategy")
                    == "guarded_momentary_pulse"
                )
                if capability_ready:
                    step_status = (
                        MultiStepSimulationStepStatus.WOULD_EXECUTE
                    )
                    step_reason = (
                        "Capability is healthy; the executor would send "
                        "one guarded momentary pulse."
                    )
                else:
                    step_status = MultiStepSimulationStepStatus.BLOCKED
                    step_reason = (
                        "Capability is not healthy or unsupported; "
                        "the step would be blocked."
                    )

                simulated_steps.append(
                    MultiStepSimulationStep(
                        step_id=step.step_id,
                        sequence=step.sequence,
                        object_id=step.object_id,
                        object_name=step.object_name,
                        room_id=step.room_id,
                        status=step_status,
                        progress_percent=round(
                            (index / total) * 100,
                            1,
                        ),
                        operation=step.operation,
                        capability=capability,
                        command_entity_id=step.command_entity_id,
                        feedback_before=step.feedback_before,
                        command_sent=False,
                        executed=False,
                        reason=step_reason,
                    )
                )

                if (
                    step_status
                    == MultiStepSimulationStepStatus.BLOCKED
                    and blueprint.stop_on_error
                ):
                    break

            blocked = sum(
                1 for item in simulated_steps
                if item.status
                == MultiStepSimulationStepStatus.BLOCKED
            )
            if blocked:
                status = MultiStepSimulationStatus.FAILED
                reason = (
                    "Simulation stopped because a step would be blocked."
                )
            else:
                status = MultiStepSimulationStatus.SIMULATED
                reason = (
                    "All steps passed the dry-run transaction state machine."
                )

        finished_at = datetime.now(UTC)
        completed_steps = len(simulated_steps)
        total_steps = len(blueprint.steps)
        progress_percent = (
            round((completed_steps / total_steps) * 100, 1)
            if total_steps
            else 100.0
        )
        simulation = MultiStepSimulation(
            simulation_id=simulation_id,
            generated_at=generated_at,
            finished_at=finished_at,
            duration_ms=round(
                (perf_counter() - started_perf) * 1000,
                2,
            ),
            decision_id=decision_id,
            plan_id=blueprint.plan_id,
            action=blueprint.action,
            target=dict(blueprint.target),
            context=blueprint.context,
            confirmed=confirmed,
            accepted=accepted,
            status=status,
            dry_run=True,
            executed=False,
            eligible_for_commit=False,
            sequence_mode=blueprint.sequence_mode,
            stop_on_error=blueprint.stop_on_error,
            rollback_ready=blueprint.rollback_ready,
            total_steps=total_steps,
            completed_steps=completed_steps,
            would_execute_steps=sum(
                1 for item in simulated_steps
                if item.status
                == MultiStepSimulationStepStatus.WOULD_EXECUTE
            ),
            skipped_steps=sum(
                1 for item in simulated_steps
                if item.status
                == MultiStepSimulationStepStatus.SKIPPED
            ),
            blocked_steps=sum(
                1 for item in simulated_steps
                if item.status
                == MultiStepSimulationStepStatus.BLOCKED
            ),
            progress_percent=progress_percent,
            reason=reason,
            errors=tuple(errors),
            steps=tuple(simulated_steps),
            blueprint=blueprint.as_dict(),
            simulator_version="1.0-stage2.2",
        )
        self.last_multi_step_simulation = simulation
        self.multi_step_simulation_audit.append(simulation)
        self.performance.record(
            ACTION_MULTI_STEP_SIMULATE,
            simulation.duration_ms,
            finished_at,
        )
        return simulation

    def execution_capabilities_snapshot(self) -> dict[str, Any]:
        """Resolve all currently qualified execution capabilities."""
        started = perf_counter()
        house = self._require_house()

        light_snapshots = {
            item.light.object_id: item for item in self.light_snapshots()
        }
        access_snapshots = {
            item.object_id: item for item in self.access_object_snapshots()
        }

        requested: list[tuple[Any, str, Any]] = []
        for light in house.lights.values():
            snapshot = light_snapshots.get(light.object_id)
            requested.append((
                light,
                "lighting.turn_on",
                snapshot,
            ))
            requested.append((
                light,
                "lighting.turn_off",
                snapshot,
            ))

        qualified_access_ids = {
            "access.lock",
            "access.unlock",
            "access.door_open",
            "access.toggle",
            "access.stop",
        }
        for opening in house.openings.values():
            snapshot = access_snapshots.get(opening.object_id)
            for capability_id in sorted(qualified_access_ids):
                if (
                    capability_id in opening.supported_capability_ids
                    or capability_id == "access.stop"
                    and opening.garage_door is not None
                ):
                    requested.append((opening, capability_id, snapshot))

        capabilities = [
            ExecutionCapabilityAdapter.resolve(
                semantic_object,
                capability_id,
                snapshot,
            )
            for semantic_object, capability_id, snapshot in requested
        ]
        capabilities.sort(key=lambda item: (item.capability_id, item.object_id))

        by_capability: dict[str, dict[str, int]] = {}
        for item in capabilities:
            stats = by_capability.setdefault(item.capability_id, {
                "objects": 0,
                "supported": 0,
                "available": 0,
                "healthy": 0,
            })
            stats["objects"] += 1
            stats["supported"] += int(item.supported)
            stats["available"] += int(item.available)
            stats["healthy"] += int(item.healthy)

        result = {
            "api_version": "1.0",
            "adapter_version": ExecutionCapabilityAdapter.VERSION,
            "read_only": True,
            "executed": False,
            "summary": {
                "objects": len({item.object_id for item in capabilities}),
                "capabilities": len(capabilities),
                "supported": sum(item.supported for item in capabilities),
                "available": sum(item.available for item in capabilities),
                "healthy": sum(item.healthy for item in capabilities),
                "unsupported": sum(not item.supported for item in capabilities),
            },
            "by_capability": dict(sorted(by_capability.items())),
            "strategies": sorted({item.strategy for item in capabilities}),
            "capabilities": [item.as_dict() for item in capabilities],
        }
        self.performance.record(
            ACTION_EXECUTION_CAPABILITIES_SNAPSHOT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def multi_step_plan(
        self,
        decision_id: str,
    ) -> MultiStepBlueprint:
        """Build a deterministic, non-executing multi-step blueprint."""
        started = perf_counter()
        generated_at = datetime.now(UTC)
        plan_id = (
            f"plan_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
            f"{uuid4().hex[:8]}"
        )

        decision = self.decision_evaluate(decision_id)
        plan = self.execution_plan(decision_id)

        supported_multi_actions = {
            "lighting.room_off",
            "lighting.all_off",
        }
        errors = list(plan.validation_errors)
        reasons = list(plan.reasons)

        if decision.action not in supported_multi_actions:
            errors.append(
                "Multi-Step Planner supports only lighting.room_off "
                "and lighting.all_off."
            )

        house = self._require_house()
        snapshots_by_id = {
            item.light.object_id: item
            for item in self.light_snapshots()
        }

        blueprint_steps: list[MultiStepBlueprintStep] = []
        for item in plan.steps:
            if not item.valid or item.command_entity_id is None:
                continue

            light = house.lights[item.object_id]
            snapshot = snapshots_by_id[item.object_id]
            capability = ExecutionCapabilityAdapter.resolve_light_turn_off(
                light,
                snapshot,
            )
            blueprint_steps.append(
                MultiStepBlueprintStep(
                    step_id=f"{plan_id}_step_{item.step:03d}",
                    sequence=item.step,
                    object_id=item.object_id,
                    object_name=item.object_name,
                    room_id=item.room_id,
                    operation=item.operation,
                    command_entity_id=item.command_entity_id,
                    feedback_before=snapshot.as_dict(),
                    capability=capability.as_dict(),
                    rollback_supported=capability.rollback_supported,
                    rollback_operation=None,
                    executable_in_current_stage=False,
                )
            )

        steps = tuple(blueprint_steps)

        accepted_for_planning = (
            decision.configured
            and decision.enabled
            and decision.action in supported_multi_actions
            and not errors
        )

        status = (
            "ready"
            if accepted_for_planning and decision.recommended
            and decision.policy_allowed
            else "not_recommended"
            if accepted_for_planning and not decision.recommended
            else "blocked"
            if accepted_for_planning and not decision.policy_allowed
            else "invalid"
        )

        blueprint = MultiStepBlueprint(
            generated_at=generated_at,
            plan_id=plan_id,
            decision_id=decision_id,
            action=decision.action,
            target=dict(decision.target),
            context=decision.context,
            status=status,
            accepted_for_planning=accepted_for_planning,
            eligible_for_commit=False,
            dry_run=True,
            executed=False,
            transaction_mode="multi_step_blueprint",
            sequence_mode="sequential",
            stop_on_error=True,
            rollback_ready=True,
            planner_version="2.0-stage2.1",
            optimizer_version="1.0",
            total_objects=plan.total_object_count,
            active_objects=plan.active_object_count,
            skipped_objects=plan.skipped_object_count,
            invalid_objects=plan.invalid_object_count,
            steps=steps,
            reasons=tuple(reasons),
            validation_errors=tuple(errors),
            decision=decision.as_dict(),
        )
        self.last_multi_step_blueprint = blueprint
        self.performance.record(
            ACTION_MULTI_STEP_PLAN,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return blueprint

    def provider_qualification_snapshot(self) -> dict[str, Any]:
        """Return installation-neutral provider qualification diagnostics."""
        started = perf_counter()
        result = self.provider_qualification_service.snapshot()
        self.performance.record(
            "provider_qualification",
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def release_info_snapshot(self) -> dict[str, Any]:
        """Return immutable release-preparation metadata."""
        started = perf_counter()
        result = ReleaseProfile.release_info()
        self.last_release_info = result
        self.performance.record(
            ACTION_RELEASE_INFO,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def public_api_snapshot(self) -> dict[str, Any]:
        """Return the current public API registry and release policy."""
        started = perf_counter()
        result = ReleaseProfile.public_api()
        self.last_public_api = result
        self.performance.record(
            ACTION_PUBLIC_API,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def upgrade_check_snapshot(self) -> dict[str, Any]:
        """Return compatibility and upgrade instructions."""
        started = perf_counter()
        result = ReleaseProfile.upgrade_check()
        self.last_upgrade_check = result
        self.performance.record(
            ACTION_UPGRADE_CHECK,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def qualification_snapshot(self) -> dict[str, Any]:
        """Return runtime and canonical evidence qualification."""
        started = perf_counter()
        system_status = await self.system_status_snapshot()
        execution_qualification = self.execution_qualification_snapshot()
        result = ReleaseProfile.qualification(
            system_status=system_status.as_dict(),
            execution_qualification=execution_qualification,
        )
        self.last_qualification = result
        self.performance.record(
            ACTION_QUALIFICATION,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def release_scope_snapshot(self) -> dict[str, Any]:
        """Return the immutable release scope profile."""
        started = perf_counter()
        result = ReleaseScopeManager.snapshot()
        result["framework_version"] = VERSION
        self.last_release_scope = result
        self.performance.record(
            ACTION_RELEASE_SCOPE,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def system_status_snapshot(
        self,
    ) -> SystemStatusSnapshot:
        """Build one stable, read-only runtime-readiness snapshot."""
        started = perf_counter()
        generated_at = datetime.now(UTC)

        diagnostics = self.diagnostics_snapshot()
        # System status is a current-health API. Revalidate the registry on
        # every explicit snapshot so transient startup entity states cannot
        # remain frozen in the release-health result for the rest of the
        # runtime. The validator is non-destructive and updates the canonical
        # validation report used by the validation/house diagnostics.
        validation = await self.async_validate_registry()
        locks = await self.transaction_lock_manager.async_snapshot()

        decision_registry = self.decision_registry
        policy_registry = self.policy_registry

        decision_count = (
            len(decision_registry.decisions)
            if decision_registry is not None
            else 0
        )
        decision_warnings = (
            list(decision_registry.warnings)
            if decision_registry is not None
            else ["Decision registry is not loaded."]
        )

        policy_count = (
            len(policy_registry.policies)
            if policy_registry is not None
            else 0
        )
        policy_warnings = (
            list(policy_registry.warnings)
            if policy_registry is not None
            else ["Policy registry is not loaded."]
        )

        validation_valid = bool(
            validation is not None
            and validation.valid
            and not validation.errors
        )
        validation_errors = (
            [item.as_dict() for item in validation.errors]
            if validation is not None
            else []
        )
        raw_validation_warnings = (
            [item.as_dict() for item in validation.warnings]
            if validation is not None
            else []
        )
        validation_warnings = []
        out_of_scope_diagnostics = []
        for warning in raw_validation_warnings:
            classification = (
                ReleaseScopeManager.classify_validation_item(warning)
            )
            classified = {
                **warning,
                **classification.as_dict(),
            }
            if classification.in_release_scope:
                validation_warnings.append(classified)
            else:
                out_of_scope_diagnostics.append(classified)

        required_capabilities = (
            "house_model",
            "house_engine",
            "decision_engine",
            "policy_engine",
            "execution_engine",
            "lighting",
            "validation",
        )
        missing_capabilities = [
            capability_id
            for capability_id in required_capabilities
            if not diagnostics.capabilities.get(capability_id, False)
        ]

        active_lock_count = locks["active_lock_count"]
        queue_count = locks["queue_count"]

        checks = [
            SystemCheck(
                check_id="runtime",
                status=(
                    "passed"
                    if diagnostics.runtime_status == "running"
                    else "failed"
                ),
                required=True,
                message=(
                    "Red Queen runtime is running."
                    if diagnostics.runtime_status == "running"
                    else "Red Queen runtime is not running normally."
                ),
                details={
                    "runtime_status": diagnostics.runtime_status,
                    "health_status": diagnostics.health_status,
                },
            ),
            SystemCheck(
                check_id="registry",
                status=(
                    "passed"
                    if diagnostics.registry_status in {"valid", "warning"}
                    else "failed"
                ),
                required=True,
                message=(
                    "House registry is loaded."
                    if diagnostics.registry_status in {"valid", "warning"}
                    else "House registry is not available."
                ),
                details={
                    "registry_status": diagnostics.registry_status,
                    "rooms": diagnostics.room_count,
                    "lights": diagnostics.light_count,
                    "covers": diagnostics.cover_count,
                    "openings": diagnostics.opening_count,
                    "warnings": list(diagnostics.warnings),
                },
            ),
            SystemCheck(
                check_id="validation",
                status=(
                    "passed"
                    if validation_valid
                    else "failed"
                ),
                required=True,
                message=(
                    "Registry validation passed."
                    if validation_valid
                    else "Registry validation has errors or is unavailable."
                ),
                details={
                    "valid": validation_valid,
                    "errors": validation_errors,
                    "warnings": validation_warnings,
                    "out_of_scope_diagnostics": (
                        out_of_scope_diagnostics
                    ),
                    "raw_warning_count": len(
                        raw_validation_warnings
                    ),
                    "in_scope_warning_count": len(
                        validation_warnings
                    ),
                    "out_of_scope_count": len(
                        out_of_scope_diagnostics
                    ),
                    "quality_score": (
                        validation.quality_score
                        if validation is not None
                        else 0
                    ),
                },
            ),
            SystemCheck(
                check_id="decisions",
                status=(
                    "passed"
                    if decision_registry is not None
                    and not decision_warnings
                    and decision_count > 0
                    else (
                        "warning"
                        if decision_registry is not None
                        and decision_count > 0
                        else "failed"
                    )
                ),
                required=True,
                message=(
                    f"{decision_count} Decisions are loaded."
                    if decision_count > 0
                    else "No Decisions are loaded."
                ),
                details={
                    "count": decision_count,
                    "warnings": decision_warnings,
                },
            ),
            SystemCheck(
                check_id="policies",
                status=(
                    "passed"
                    if policy_registry is not None
                    and not policy_warnings
                    and policy_count > 0
                    else (
                        "warning"
                        if policy_registry is not None
                        and policy_count > 0
                        else "failed"
                    )
                ),
                required=True,
                message=(
                    f"{policy_count} Policies are loaded."
                    if policy_count > 0
                    else "No Policies are loaded."
                ),
                details={
                    "count": policy_count,
                    "warnings": policy_warnings,
                },
            ),
            SystemCheck(
                check_id="capabilities",
                status=(
                    "passed"
                    if not missing_capabilities
                    else "failed"
                ),
                required=True,
                message=(
                    "All required runtime capabilities are available."
                    if not missing_capabilities
                    else "Required capabilities are missing."
                ),
                details={
                    "required": list(required_capabilities),
                    "missing": missing_capabilities,
                },
            ),
            SystemCheck(
                check_id="release_scope",
                status="passed",
                required=True,
                message="Release scope profile is loaded.",
                details={
                    **ReleaseScopeManager.snapshot(),
                    "out_of_scope_diagnostic_count": len(
                        out_of_scope_diagnostics
                    ),
                },
            ),
            SystemCheck(
                check_id="scheduler",
                status="passed",
                required=True,
                message=(
                    "Execution scheduler state is consistent."
                ),
                details={
                    "active_lock_count": active_lock_count,
                    "queue_count": queue_count,
                    "house_locked": locks["house_locked"],
                    "room_locks": locks["room_locks"],
                },
            ),
            SystemCheck(
                check_id="last_execution",
                status=(
                    "informational"
                    if self.last_canonical_execution is None
                    else (
                        "passed"
                        if self.last_canonical_execution.get("state")
                        in {"succeeded", "no_action"}
                        else "warning"
                    )
                ),
                required=False,
                message=(
                    "No canonical public execution has run since startup; runtime "
                    "health is unaffected."
                    if self.last_canonical_execution is None
                    else (
                        "Latest canonical public execution completed acceptably."
                        if self.last_canonical_execution.get("state")
                        in {"succeeded", "no_action"}
                        else (
                            "Latest canonical public execution ended with state "
                            f"{self.last_canonical_execution.get('state')!r}."
                        )
                    )
                ),
                details=(
                    {}
                    if self.last_canonical_execution is None
                    else {
                        "entry": "wnhf.execution_execute",
                        "execution_id": self.last_canonical_execution.get("execution_id"),
                        "action_id": (self.last_canonical_execution.get("request") or {}).get("action_id"),
                        "state": self.last_canonical_execution.get("state"),
                        "result_code": (self.last_canonical_execution.get("result_code") or {}).get("code"),
                        "executed": self.last_canonical_execution.get("executed"),
                        "command_sent": self.last_canonical_execution.get("command_sent"),
                        "feedback_confirmed": self.last_canonical_execution.get("feedback_confirmed"),
                        "reason": self.last_canonical_execution.get("reason"),
                    }
                ),
            ),
        ]

        required_failures = [
            item for item in checks
            if item.required and item.status == "failed"
        ]
        warning_checks = [
            item for item in checks
            if item.status == "warning"
        ]

        runtime_ready = not required_failures
        if required_failures:
            status = "error"
        elif warning_checks or diagnostics.warning_count or validation_warnings:
            status = "warning"
        else:
            status = "healthy"

        error_count = len(required_failures)
        registry_warning_count = diagnostics.warning_count
        warning_count = (
            len(warning_checks)
            + registry_warning_count
            + len(validation_warnings)
        )
        # Health Score 2.0 is based only on the active release-preparation
        # scope. Planned domains remain visible but do not reduce the score.
        health_score = max(
            0,
            min(
                100,
                100
                - (error_count * 25)
                - (len(validation_warnings) * 2)
                - (registry_warning_count * 2)
                - len(warning_checks),
            ),
        )

        result = SystemStatusSnapshot(
            api_version=SYSTEM_STATUS_API_VERSION,
            generated_at=generated_at,
            framework_version=VERSION,
            status=status,
            runtime_ready=runtime_ready,
            health_score=health_score,
            error_count=error_count,
            warning_count=warning_count,
            active_transaction_count=active_lock_count,
            queued_transaction_count=queue_count,
            summary={
                "house_id": diagnostics.house_id,
                "house_name": diagnostics.house_name,
                "rooms": diagnostics.room_count,
                "lights": diagnostics.light_count,
                "enabled_lights": diagnostics.enabled_light_count,
                "controllable_lights": (
                    diagnostics.controllable_light_count
                ),
                "covers": diagnostics.cover_count,
                "openings": diagnostics.opening_count,
                "decisions": decision_count,
                "policies": policy_count,
                "registry_status": diagnostics.registry_status,
                "validation_valid": validation_valid,
                "release_channel": ReleaseScopeManager.CHANNEL,
                "release_phase": ReleaseScopeManager.PHASE,
                "release_candidate": ReleaseProfile.CANDIDATE,
                "health_score_model": "release-scope-2.1",
                "in_scope_warning_count": len(validation_warnings),
                "out_of_scope_diagnostic_count": len(
                    out_of_scope_diagnostics
                ),
                "planned_domains": [
                    item["domain_id"]
                    for item in ReleaseScopeManager.snapshot()["planned_domains"]
                ],
            },
            checks=tuple(checks),
            last_public_execution=(
                dict(self.last_canonical_execution)
                if self.last_canonical_execution is not None
                else None
            ),
        )
        self.last_system_status = result
        self.performance.record(
            ACTION_SYSTEM_STATUS,
            round((perf_counter() - started) * 1000, 2),
            generated_at,
        )
        return result

    async def transaction_locks_snapshot(
        self,
    ) -> dict[str, Any]:
        """Return active lock and scheduler state."""
        started = perf_counter()
        result = await self.transaction_lock_manager.async_snapshot()
        result["count"] = result["active_lock_count"]
        if self.last_lock_decision is not None:
            result["last_decision"] = self.last_lock_decision.as_dict()
        else:
            result["last_decision"] = None
        self.performance.record(
            ACTION_TRANSACTION_LOCKS,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    async def transaction_queue_snapshot(
        self,
    ) -> dict[str, Any]:
        """Return the public scheduler queue snapshot."""
        started = perf_counter()
        result = await self.transaction_lock_manager.async_snapshot()
        response = {
            "manager_version": result["manager_version"],
            "queue_count": result["queue_count"],
            "active_lock_count": result["active_lock_count"],
            "queue": result["queue"],
            "locks": result["locks"],
            "last_decision": (
                self.last_lock_decision.as_dict()
                if self.last_lock_decision is not None
                else None
            ),
        }
        self.performance.record(
            ACTION_TRANSACTION_QUEUE,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return response

    async def async_public_execute(
        self,
        requested_id: str,
        confirmed: bool,
        conflict_policy: str = "reject",
        queue_timeout: float = 15.0,
    ) -> PublicExecutionResult:
        """Execute a semantic Decision through manager and scope lock."""
        started = perf_counter()
        request_id = (
            f"req_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S_%fZ')}_"
            f"{uuid4().hex[:8]}"
        )

        decision = self.decision_evaluate(requested_id)
        route = LegacyExecutionManager.resolve(decision.action)

        if route is None:
            result = PublicExecutionResult(
                api_version="1.3",
                request_id=request_id,
                requested_id=requested_id,
                action=decision.action,
                executor=None,
                accepted=False,
                status="rejected",
                executed=False,
                reason=(
                    "No qualified executor is registered for action "
                    f"{decision.action!r}."
                ),
                transaction={
                    "decision": decision.as_dict(),
                    "manager_version": LegacyExecutionManager.VERSION,
                    "lock_manager_version": (
                        TransactionLockManager.VERSION
                    ),
                },
            )
        else:
            room_id = None
            if route.executor in {"object", "room"}:
                room_id = decision.target.get("room_id")
                if (
                    room_id is None
                    and route.executor == "object"
                ):
                    light_id = decision.target.get("light_id")
                    if light_id:
                        house = self._require_house()
                        light = house.lights.get(light_id)
                        if light is not None:
                            room_id = light.room_id

            lock_decision = (
                await self.transaction_lock_manager.async_acquire(
                    request_id=request_id,
                    requested_id=requested_id,
                    executor=route.executor,
                    scope=route.executor,
                    room_id=room_id,
                    wait=conflict_policy == "wait",
                    timeout_seconds=queue_timeout,
                )
            )
            self.last_lock_decision = lock_decision

            if not lock_decision.acquired:
                public_status = (
                    "queue_timeout"
                    if lock_decision.status == "queue_timeout"
                    else "locked"
                )
                result = PublicExecutionResult(
                    api_version="1.3",
                    request_id=request_id,
                    requested_id=requested_id,
                    action=route.action,
                    executor=route.executor,
                    accepted=False,
                    status=public_status,
                    executed=False,
                    reason=lock_decision.reason,
                    transaction={
                        "manager": {
                            "version": LegacyExecutionManager.VERSION,
                            "executor": route.executor,
                            "action": route.action,
                        },
                        "lock_manager": {
                            "version": TransactionLockManager.VERSION,
                            "conflict_policy": conflict_policy,
                            "queue_timeout": queue_timeout,
                            **lock_decision.as_dict(),
                        },
                    },
                )
            else:
                try:
                    if route.executor == "object":
                        transaction = await self.async_execution_commit(
                            requested_id,
                            confirmed,
                        )
                        transaction_data = transaction.as_dict()
                        accepted = transaction.status.value in {
                            "succeeded",
                            "no_action",
                        }
                        status = transaction.status.value
                        executed = transaction.executed
                        reason = transaction.reason

                    elif route.executor == "room":
                        transaction = (
                            await self.async_sequential_room_execute(
                                requested_id,
                                confirmed,
                            )
                        )
                        transaction_data = transaction.as_dict()
                        accepted = transaction.accepted
                        status = transaction.state.value
                        executed = transaction.executed
                        reason = transaction.reason

                    elif route.executor == "house":
                        transaction = await self.async_house_execute(
                            requested_id,
                            confirmed,
                        )
                        transaction_data = transaction.as_dict()
                        accepted = transaction.accepted
                        status = transaction.state.value
                        executed = transaction.executed
                        reason = transaction.reason

                    else:
                        raise RuntimeError(
                            "Unsupported Execution Manager route: "
                            f"{route.executor}"
                        )

                    transaction_data["manager"] = {
                        "version": LegacyExecutionManager.VERSION,
                        "executor": route.executor,
                        "action": route.action,
                    }
                    transaction_data["lock_manager"] = {
                        "version": TransactionLockManager.VERSION,
                        **lock_decision.as_dict(),
                        "released": True,
                    }
                    result = PublicExecutionResult(
                        api_version="1.3",
                        request_id=request_id,
                        requested_id=requested_id,
                        action=route.action,
                        executor=route.executor,
                        accepted=accepted,
                        status=status,
                        executed=executed,
                        reason=reason,
                        transaction=transaction_data,
                    )
                finally:
                    await self.transaction_lock_manager.async_release(
                        request_id
                    )

        self.last_legacy_public_execution = result
        self.last_public_execution = result
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        self.performance.record(
            ACTION_EXECUTION_MANAGER,
            elapsed_ms,
            datetime.now(UTC),
        )
        self.performance.record(
            ACTION_PUBLIC_EXECUTE,
            elapsed_ms,
            datetime.now(UTC),
        )
        return result

    def execution_audit_snapshot(self) -> dict[str, Any]:
        """Return the bounded in-memory execution audit."""
        started = perf_counter()
        records = [item.as_dict() for item in reversed(self.execution_audit)]
        self.performance.record(
            ACTION_EXECUTION_AUDIT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "count": len(records),
            "limit": EXECUTION_AUDIT_LIMIT,
            "records": records,
        }

    async def async_execution_commit(
        self,
        decision_id: str,
        confirmed: bool,
    ) -> ExecutionTransaction:
        """Execute one explicitly confirmed single-object off transaction."""
        async with self._execution_lock:
            started_perf = perf_counter()
            started_at = datetime.now(UTC)
            execution_id = (
                f"exec_{started_at.strftime('%Y%m%dT%H%M%S_%fZ')}_"
                f"{uuid4().hex[:8]}"
            )

            decision = self.decision_evaluate(decision_id)
            action = decision.action
            target = dict(decision.target)
            policy_id = (
                decision.policy.get("policy_id")
                if decision.policy is not None
                else None
            )
            light_id = target.get("light_id")
            command_entity_id = None
            command_sent = False
            feedback_before = None
            feedback_after = None
            status = ExecutionTransactionStatus.REJECTED
            reason = "Execution rejected."
            error = None

            try:
                if not confirmed:
                    reason = "Explicit confirmation is required."
                elif not decision.configured:
                    reason = "Decision is not configured."
                elif not decision.enabled:
                    reason = "Decision is disabled."
                elif action != "lighting.object_off":
                    reason = "Stage 1 supports only lighting.object_off."
                elif not decision.recommended:
                    reason = "Decision does not recommend execution."
                elif not decision.policy_allowed:
                    reason = "Policy blocks execution."
                elif not isinstance(light_id, str):
                    reason = "Decision target needs exactly one light_id."
                else:
                    house = self._require_house()
                    light = house.lights.get(light_id)

                    if light is None:
                        reason = f"Unknown WNHF light id: {light_id}"
                    elif not light.controllable:
                        reason = (
                            f"Red Queen light is not safely controllable: {light_id}"
                        )
                    else:
                        snapshot = self.light_snapshot(light_id)
                        command_entity_id = light.command_entity_id
                        feedback_before = snapshot.as_dict()

                        if not snapshot.available:
                            reason = (
                                "Light feedback or command entity is unavailable."
                            )
                        elif not snapshot.is_on:
                            status = ExecutionTransactionStatus.NO_ACTION
                            reason = "Light already reports off; no command sent."
                        else:
                            result = await self.async_light_turn_off(light_id)
                            command_sent = bool(
                                result.get("command_sent", False)
                            )
                            await asyncio.sleep(0.35)
                            feedback_after = self.light_snapshot(
                                light_id
                            ).as_dict()

                            if command_sent:
                                status = ExecutionTransactionStatus.SUCCEEDED
                                reason = "One momentary off command was sent."
                            else:
                                status = ExecutionTransactionStatus.NO_ACTION
                                reason = str(
                                    result.get(
                                        "reason",
                                        "No command was sent.",
                                    )
                                )
            except Exception as err:  # noqa: BLE001
                status = ExecutionTransactionStatus.FAILED
                error = f"{type(err).__name__}: {err}"
                reason = "Execution failed with an exception."
                _LOGGER.exception(
                    "Red Queen execution transaction failed: %s",
                    execution_id,
                )

            finished_at = datetime.now(UTC)
            duration_ms = round((perf_counter() - started_perf) * 1000, 2)
            transaction = ExecutionTransaction(
                execution_id=execution_id,
                decision_id=decision_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                status=status,
                confirmed=confirmed,
                action=action,
                target=target,
                context=decision.context,
                decision_status=decision.status.value,
                recommended=decision.recommended,
                policy_allowed=decision.policy_allowed,
                policy_id=policy_id,
                light_id=light_id if isinstance(light_id, str) else None,
                command_entity_id=command_entity_id,
                command_sent=command_sent,
                feedback_before=feedback_before,
                feedback_after=feedback_after,
                reason=reason,
                error=error,
                planner_version="1.0",
                optimizer_version="1.0",
                executor_version="1.0-stage1",
            )
            self.last_execution_transaction = transaction
            self.execution_audit.append(transaction)
            self.performance.record(
                ACTION_EXECUTION_COMMIT,
                duration_ms,
                finished_at,
            )
            _LOGGER.info(
                "Red Queen execution %s: status=%s decision=%s "
                "light=%s sent=%s duration=%.2fms",
                execution_id,
                status.value,
                decision_id,
                light_id,
                command_sent,
                duration_ms,
            )
            return transaction


    async def async_load_decisions(self) -> DecisionRegistry:
        """Load optional decision definitions."""
        started = perf_counter()
        registry = await self.hass.async_add_executor_job(
            load_decision_registry,
            self.decisions_dir,
        )
        self.decision_registry = registry
        self.last_decision_result = None
        self.performance.record(
            ACTION_RELOAD_DECISIONS,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return registry

    def decision_evaluate(self, decision_id: str):
        """Evaluate one read-only decision."""
        started = perf_counter()
        context = self.context_snapshot()
        definition = self.decision_registry.get(decision_id)

        policy_result = None
        if definition is not None and definition.policy_id:
            policy_result = self.policy_check(
                definition.policy_id
            ).as_dict()

        result = DecisionEvaluator.evaluate(
            self.decision_registry,
            decision_id,
            context.state,
            policy_result,
        )
        self.last_decision_result = result
        self.performance.record(
            ACTION_DECISION_EVALUATE,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return result

    def decisions_snapshot(self) -> dict[str, Any]:
        """Return every configured decision for the current context."""
        started = perf_counter()
        results = {
            item.decision_id: self.decision_evaluate(
                item.decision_id
            ).as_dict()
            for item in self.decision_registry.decisions
        }
        self.performance.record(
            ACTION_DECISIONS_SNAPSHOT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "decisions_dir": str(self.decisions_dir),
            "context": self.context_snapshot().state,
            "read_only": True,
            "registry": self.decision_registry.as_dict(),
            "results": results,
        }

    async def async_load_policies(self) -> PolicyRegistry:
        """Load optional policies without requiring any configuration."""
        started = perf_counter()
        registry = await self.hass.async_add_executor_job(
            load_policy_registry,
            self.policies_dir,
        )
        self.policy_registry = registry
        self.last_policy_decision = None
        self.performance.record(
            ACTION_RELOAD_POLICIES,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return registry

    def policy_check(self, policy_id: str):
        """Evaluate one permission question against current context."""
        started = perf_counter()
        context = self.context_snapshot()
        decision = PolicyEvaluator.evaluate(
            self.policy_registry,
            policy_id,
            context.state,
            self.capabilities_snapshot(),
        )
        self.last_policy_decision = decision
        self.performance.record(
            ACTION_POLICY_CHECK,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return decision

    def policies_snapshot(self) -> dict[str, Any]:
        """Return policy configuration and current example decisions."""
        started = perf_counter()
        context = self.context_snapshot()
        decisions = {
            policy.policy_id: PolicyEvaluator.evaluate(
                self.policy_registry,
                policy.policy_id,
                context.state,
                self.capabilities_snapshot(),
            ).as_dict()
            for policy in self.policy_registry.policies
        }
        self.performance.record(
            ACTION_POLICIES_SNAPSHOT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return {
            "policies_dir": str(self.policies_dir),
            "mode": self.policy_registry.mode.value,
            "context": context.state,
            "registry": self.policy_registry.as_dict(),
            "decisions": decisions,
            "fallback": {
                "unconfigured_policy": "allow",
                "monitor_effective_decision": "allow",
            },
        }

    async def async_load_rules(self) -> RuleRegistry:
        """Load declarative context rules without requiring the directory."""
        started = perf_counter()
        registry = await self.hass.async_add_executor_job(
            load_rule_registry,
            self.rules_dir,
        )
        self.rule_registry = registry
        self.rule_snapshot = None
        self.context_snapshot_cache = None
        self.performance.record(
            ACTION_RELOAD_RULES,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return registry

    @staticmethod
    def _flatten_facts(
        value: Any,
        prefix: str = "",
    ) -> dict[str, Any]:
        """Flatten nested mappings into stable dotted fact paths."""
        result: dict[str, Any] = {}
        if isinstance(value, dict):
            for key, child in value.items():
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                result.update(
                    WNHFEngine._flatten_facts(child, child_prefix)
                )
        else:
            result[prefix] = value
        return result

    def context_scores(self) -> ContextScores:
        """Calculate transparent, deterministic context scores."""
        house = self.house_snapshot()

        activity = (
            house.lights_on_count
            + house.covers_moving_count * 2
        )
        attention = (
            house.openings_open_count * 3
            + house.covers_error_count * 5
        )
        security = max(
            0,
            100 - house.openings_open_count * 20,
        )
        health = max(0, min(100, house.quality_score))

        return ContextScores(
            activity=activity,
            attention=attention,
            security=security,
            health=health,
        )

    def rule_facts(self) -> dict[str, Any]:
        """Build technology-independent facts for rule evaluation."""
        house = self.house_snapshot().as_dict()
        capabilities = self.capabilities_snapshot()
        scores = self.context_scores().as_dict()

        facts = {}
        facts.update(self._flatten_facts({"house": house}))
        facts.update(
            self._flatten_facts({"capabilities": capabilities})
        )
        facts.update(self._flatten_facts({"scores": scores}))
        return facts

    def evaluate_rules(self) -> RuleSnapshot:
        """Evaluate every enabled rule and retain the latest snapshot."""
        started = perf_counter()
        snapshot = RuleEvaluator.evaluate(
            self.rule_registry,
            self.rule_facts(),
        )
        self.rule_snapshot = snapshot
        self.performance.record(
            ACTION_EVALUATE_RULES,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return snapshot

    def evaluate_context_rules(self) -> RuleSnapshot:
        """Evaluate protected core contexts plus building-specific rules."""
        registry = combined_context_registry(self.rule_registry)
        return RuleEvaluator.evaluate(
            registry,
            self.rule_facts(),
        )

    def _context_reasons(
        self,
        state: str,
        house: HouseSnapshot,
    ) -> tuple[str, ...]:
        """Return concrete building reasons for the selected context."""
        if state == "error":
            reasons: list[str] = []
            if house.validation_status == "error":
                reasons.append("Framework-Validierung meldet Fehler")
            if house.covers_error_count:
                reasons.append(
                    f"{house.covers_error_count} Raffstore mit Statusfehler"
                )
            return tuple(reasons) or ("Technischer Fehler erkannt",)

        if state == "attention":
            return tuple(
                f"Offen: {name}"
                for name in house.opening_names_open
            ) or ("Haus ist nicht vollständig gesichert",)

        if state == "activity":
            reasons = [
                f"Licht an: {name}"
                for name in house.light_names_on
            ]
            reasons.extend(
                f"Raffstore fährt: {name}"
                for name in house.cover_names_moving
            )
            return tuple(reasons) or ("Aktivität erkannt",)

        if state == "ready":
            return (
                "Alle Öffnungen geschlossen",
                "Keine sichtbare Aktivität",
                "Framework ohne Fehler",
            )

        return ("Gebäudespezifische Regel erfüllt",)

    def context_snapshot(self) -> ContextSnapshot:
        """Return the current semantic interpretation of the house."""
        started = perf_counter()
        rule_snapshot = self.evaluate_context_rules()
        winner = rule_snapshot.winner

        if winner is None:
            state = "unknown"
            message = "Kein Context konnte bestimmt werden."
            confidence = 0.0
            priority = -1
            rule_id = ""
            rule_name = ""
            source = "none"
        else:
            result = winner.rule.result
            state = str(result.get("state", "unknown"))
            message = str(
                result.get(
                    "message",
                    f"Context '{state}' wurde erkannt.",
                )
            )
            confidence = winner.rule.confidence
            priority = winner.rule.priority
            rule_id = winner.rule.rule_id
            rule_name = winner.rule.name
            source = str(result.get("source", "custom"))

        house = self.house_snapshot()
        snapshot = ContextSnapshot(
            generated_at=datetime.now(UTC),
            state=state,
            message=message,
            confidence=confidence,
            priority=priority,
            rule_id=rule_id,
            rule_name=rule_name,
            source=source,
            scores=self.context_scores(),
            reasons=self._context_reasons(state, house),
            rule_snapshot=rule_snapshot,
        )
        self.context_snapshot_cache = snapshot
        self.performance.record(
            ACTION_CONTEXT_SNAPSHOT,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return snapshot

    def rules_snapshot(self) -> dict[str, Any]:
        """Return registry metadata and the latest/current evaluation."""
        snapshot = self.evaluate_rules()
        self.performance.record(
            ACTION_RULES_SNAPSHOT,
            0.0,
            datetime.now(UTC),
        )
        return {
            "rules_dir": str(self.rules_dir),
            "registry": self.rule_registry.as_dict(),
            "evaluation": snapshot.as_dict(),
        }

    async def async_validate_registry(self) -> ValidationReport:
        """Run the full non-destructive framework validation."""
        started = perf_counter()
        house = self._require_house()
        validator = WNHFValidator(self.hass, self)
        report = validator.validate(house)
        self.validation_report = report
        self.performance.record(
            ACTION_VALIDATE_REGISTRY,
            round((perf_counter() - started) * 1000, 2),
            datetime.now(UTC),
        )
        return report

    def validation_snapshot(self) -> ValidationReport | None:
        """Return the latest validation report."""
        return self.validation_report

    def _require_house(self) -> House:
        if self.house is None:
            raise RuntimeError("Red Queen house model is not loaded")
        return self.house

    def light_snapshot(self, light_id: str) -> LightSnapshot:
        """Return the current normalized runtime state of one light."""
        light = self._require_house().light(light_id)

        feedback_states: dict[str, str | None] = {}
        available = bool(light.state_entity_ids)
        is_on = False

        for entity_id in light.state_entity_ids:
            state = self.hass.states.get(entity_id)
            state_value = state.state if state is not None else None
            feedback_states[entity_id] = state_value

            if state_value in {None, "unknown", "unavailable"}:
                available = False
            elif state_value == "on":
                is_on = True

        if light.command_entity_id is not None:
            command_state = self.hass.states.get(light.command_entity_id)
            if (
                command_state is None
                or command_state.state == "unavailable"
            ):
                available = False

        return LightSnapshot(
            light=light,
            is_on=is_on,
            available=available,
            feedback_states=feedback_states,
        )

    def light_snapshots(self) -> list[LightSnapshot]:
        """Return snapshots for all enabled WNHF lights."""
        return [
            self.light_snapshot(light.object_id)
            for light in self._require_house().enabled_lights
        ]

    def _is_on(self, light: Light) -> bool:
        """Compatibility helper for existing aggregate lighting logic."""
        return self.light_snapshot(light.object_id).is_on

    async def _async_press_light_command(self, light: Light) -> None:
        """Send one momentary command impulse through the HA button adapter."""
        if light.command_entity_id is None:
            raise ValueError(
                f"Red Queen light has no command entity: {light.object_id}"
            )

        await self.hass.services.async_call(
            "button",
            "press",
            {"entity_id": light.command_entity_id},
            blocking=True,
        )

    async def async_light_turn_on(self, light_id: str) -> dict[str, Any]:
        """Send an impulse only if feedback currently reports off."""
        light = self._require_house().light(light_id)
        if not light.controllable:
            raise ValueError(f"Red Queen light is not controllable: {light_id}")

        snapshot = self.light_snapshot(light_id)
        if not snapshot.available:
            return {
                "light_id": light_id,
                "command_sent": False,
                "reason": "unavailable",
            }
        if snapshot.is_on:
            return {
                "light_id": light_id,
                "command_sent": False,
                "reason": "already_on",
            }

        await self._async_press_light_command(light)
        return {
            "light_id": light_id,
            "command_sent": True,
            "command": "pulse",
            "target_state": "on",
        }

    async def async_light_turn_off(self, light_id: str) -> dict[str, Any]:
        """Send an impulse only if feedback currently reports on."""
        light = self._require_house().light(light_id)
        if not light.controllable:
            raise ValueError(f"Red Queen light is not controllable: {light_id}")

        snapshot = self.light_snapshot(light_id)
        if not snapshot.available:
            return {
                "light_id": light_id,
                "command_sent": False,
                "reason": "unavailable",
            }
        if not snapshot.is_on:
            return {
                "light_id": light_id,
                "command_sent": False,
                "reason": "already_off",
            }

        await self._async_press_light_command(light)
        return {
            "light_id": light_id,
            "command_sent": True,
            "command": "pulse",
            "target_state": "off",
        }

    async def _async_toggle_off(self, light: Light) -> bool:
        """Compatibility adapter for existing aggregate off actions."""
        result = await self.async_light_turn_off(light.object_id)
        if result.get("command_sent"):
            await asyncio.sleep(0.15)
            return True
        return False

    @staticmethod
    def _runtime_entity_available(state) -> bool:
        """Return whether one Home Assistant state can be evaluated."""
        return (
            state is not None
            and state.state not in {"unknown", "unavailable"}
        )

    def access_object_snapshot(
        self,
        opening_id: str,
    ) -> AccessObjectSnapshot:
        """Return the normalized runtime state of one Access object."""
        opening = self._require_house().opening(opening_id)

        if opening.garage_door is not None:
            garage = opening.garage_door
            open_state = self.hass.states.get(
                garage.open_feedback_entity_id
            )
            closed_state = self.hass.states.get(
                garage.closed_feedback_entity_id
            )
            feedback = {
                garage.open_feedback_entity_id: (
                    open_state.state if open_state is not None else "missing"
                ),
                garage.closed_feedback_entity_id: (
                    closed_state.state
                    if closed_state is not None
                    else "missing"
                ),
            }
            available = (
                self._runtime_entity_available(open_state)
                and self._runtime_entity_available(closed_state)
            )

            elapsed_seconds: float | None = None
            if not available:
                state = GarageDoorRuntimeState.UNAVAILABLE
            else:
                open_active = open_state.state == "on"
                closed_active = closed_state.state == "on"

                if open_active and closed_active:
                    state = GarageDoorRuntimeState.ERROR
                elif open_active:
                    state = GarageDoorRuntimeState.OPEN
                elif closed_active:
                    state = GarageDoorRuntimeState.CLOSED
                else:
                    changed_at = max(
                        open_state.last_changed,
                        closed_state.last_changed,
                    )
                    elapsed_seconds = max(
                        0.0,
                        (datetime.now(UTC) - changed_at).total_seconds(),
                    )
                    state = (
                        GarageDoorRuntimeState.MOVING
                        if elapsed_seconds
                        <= garage.movement_timeout_seconds
                        else GarageDoorRuntimeState.INTERMEDIATE_OPEN
                    )

            is_closed = state == GarageDoorRuntimeState.CLOSED
            is_open = state in {
                GarageDoorRuntimeState.OPEN,
                GarageDoorRuntimeState.MOVING,
                GarageDoorRuntimeState.INTERMEDIATE_OPEN,
                GarageDoorRuntimeState.ERROR,
            }

            return AccessObjectSnapshot(
                object_id=opening.object_id,
                name=opening.name,
                room_id=opening.room_id,
                opening_type=opening.opening_type,
                enabled=opening.enabled,
                available=available,
                state=state.value,
                is_open=is_open,
                is_closed=is_closed,
                secure=available and is_closed,
                has_lock=False,
                has_door_opener=False,
                garage_elapsed_seconds=(
                    round(elapsed_seconds, 2)
                    if elapsed_seconds is not None
                    else None
                ),
                feedback_states=feedback,
            )

        entity_id = opening.state_entity_id
        platform_state = (
            self.hass.states.get(entity_id)
            if entity_id is not None
            else None
        )
        available = self._runtime_entity_available(platform_state)

        if not available:
            state = OpeningRuntimeState.UNAVAILABLE
            is_open = False
            is_closed = False
        else:
            is_open = opening.state_is_open(platform_state.state)
            is_closed = not is_open
            state = (
                OpeningRuntimeState.OPEN
                if is_open
                else OpeningRuntimeState.CLOSED
            )

        lock_state: LockRuntimeState | None = None
        lock_available = True
        locked = False
        feedback = {}
        if entity_id is not None:
            feedback[entity_id] = (
                platform_state.state
                if platform_state is not None
                else "missing"
            )

        if opening.lock is not None:
            lock_feedback = self.hass.states.get(
                opening.lock.feedback_entity_id
            )
            feedback[opening.lock.feedback_entity_id] = (
                lock_feedback.state
                if lock_feedback is not None
                else "missing"
            )
            lock_available = self._runtime_entity_available(lock_feedback)
            if not lock_available:
                lock_state = LockRuntimeState.UNAVAILABLE
            else:
                locked = opening.lock.state_is_locked(lock_feedback.state)
                lock_state = (
                    LockRuntimeState.LOCKED
                    if locked
                    else LockRuntimeState.UNLOCKED
                )

        object_available = available and lock_available
        secure = (
            object_available
            and is_closed
            and (opening.lock is None or locked)
        )

        return AccessObjectSnapshot(
            object_id=opening.object_id,
            name=opening.name,
            room_id=opening.room_id,
            opening_type=opening.opening_type,
            enabled=opening.enabled,
            available=object_available,
            state=state.value,
            is_open=is_open,
            is_closed=is_closed,
            secure=secure,
            lock_state=(
                lock_state.value if lock_state is not None else None
            ),
            has_lock=opening.lock is not None,
            has_door_opener=opening.door_opener is not None,
            feedback_states=feedback,
        )

    def access_object_snapshots(self) -> list[AccessObjectSnapshot]:
        """Return runtime snapshots of all enabled Access objects."""
        house = self._require_house()
        return [
            self.access_object_snapshot(opening.object_id)
            for opening in house.enabled_openings
        ]

    def access_snapshot(self) -> AccessSnapshot:
        """Return the aggregate read-only Access runtime snapshot."""
        started = perf_counter()
        generated_at = datetime.now(UTC)
        house = self._require_house()
        objects = tuple(self.access_object_snapshots())

        result = AccessSnapshot(
            generated_at=generated_at.isoformat(),
            total=len(house.openings),
            enabled=len(house.enabled_openings),
            available=sum(1 for item in objects if item.available),
            secure=sum(1 for item in objects if item.secure),
            open_count=sum(1 for item in objects if item.is_open),
            unavailable_count=sum(
                1 for item in objects if not item.available
            ),
            windows=sum(
                1 for item in objects if item.opening_type == "window"
            ),
            sliding_doors=sum(
                1
                for item in objects
                if item.opening_type == "sliding_door"
            ),
            doors=sum(
                1 for item in objects if item.opening_type == "door"
            ),
            garage_doors=sum(
                1
                for item in objects
                if item.opening_type == "garage_door"
            ),
            locked_doors=sum(
                1 for item in objects if item.lock_state == "locked"
            ),
            unlocked_doors=sum(
                1 for item in objects if item.lock_state == "unlocked"
            ),
            garage_open=sum(
                1
                for item in objects
                if item.opening_type == "garage_door"
                and item.state == "open"
            ),
            garage_closed=sum(
                1
                for item in objects
                if item.opening_type == "garage_door"
                and item.state == "closed"
            ),
            garage_moving=sum(
                1
                for item in objects
                if item.opening_type == "garage_door"
                and item.state == "moving"
            ),
            garage_intermediate_open=sum(
                1
                for item in objects
                if item.opening_type == "garage_door"
                and item.state == "intermediate_open"
            ),
            garage_error=sum(
                1
                for item in objects
                if item.opening_type == "garage_door"
                and item.state == "error"
            ),
            objects=objects,
        )
        self.performance.record(
            ACTION_ACCESS_SNAPSHOT,
            round((perf_counter() - started) * 1000, 2),
            generated_at,
        )
        return result

    def opening_is_open(self, opening_id: str) -> bool:
        """Return whether one opening is open or not safely closed."""
        return self.access_object_snapshot(opening_id).is_open

    def openings_open(self) -> list:
        """Return enabled opening objects currently reporting open."""
        house = self._require_house()
        return [
            opening
            for opening in house.enabled_openings
            if self.opening_is_open(opening.object_id)
        ]

    def opening_count_open(self) -> int:
        """Return number of currently open WNHF opening objects."""
        return len(self.openings_open())

    def opening_names_open(self) -> list[str]:
        """Return names of currently open WNHF opening objects."""
        return [opening.name for opening in self.openings_open()]

    def opening_ids_open(self) -> list[str]:
        """Return stable IDs of currently open WNHF opening objects."""
        return [opening.object_id for opening in self.openings_open()]

    def opening_feedback_entities(self) -> set[str]:
        """Return every configured Access feedback entity ID."""
        house = self._require_house()
        entity_ids: set[str] = set()

        for opening in house.enabled_openings:
            if opening.state_entity_id:
                entity_ids.add(opening.state_entity_id)

            if opening.lock is not None:
                entity_ids.add(opening.lock.feedback_entity_id)

            if opening.garage_door is not None:
                entity_ids.add(
                    opening.garage_door.open_feedback_entity_id
                )
                entity_ids.add(
                    opening.garage_door.closed_feedback_entity_id
                )

        return entity_ids

    def _entity_is_on(self, entity_id: str) -> bool:
        """Return whether one Home Assistant entity currently reports on."""
        state = self.hass.states.get(entity_id)
        return state is not None and state.state == "on"

    def cover_snapshot(self, cover_id: str) -> CoverSnapshot:
        """Return the normalized runtime state and optional position of one cover."""
        cover = self._require_house().cover(cover_id)
        feedback_states = {
            entity_id: self.hass.states.get(entity_id)
            for entity_id in cover.direction_feedback_entity_ids
        }
        available = all(
            state is not None
            and state.state not in {"unknown", "unavailable"}
            for state in feedback_states.values()
        )

        def is_on(entity_id: str) -> bool:
            state = feedback_states[entity_id]
            return state is not None and state.state == "on"

        closed_percent: float | None = None
        position_available = False
        position_entity_id = cover.closed_percent_feedback_entity_id
        if position_entity_id:
            position_state = self.hass.states.get(position_entity_id)
            if (
                position_state is not None
                and position_state.state not in {"unknown", "unavailable"}
            ):
                try:
                    closed_percent = float(position_state.state)
                    position_available = True
                except (TypeError, ValueError):
                    closed_percent = None

        return CoverStateMachine.evaluate(
            cover,
            available=available,
            feedback_open=is_on(cover.open_feedback_entity_id),
            feedback_closed=is_on(cover.closed_feedback_entity_id),
            feedback_opening=is_on(cover.opening_feedback_entity_id),
            feedback_closing=is_on(cover.closing_feedback_entity_id),
            closed_percent=closed_percent,
            position_available=position_available,
        )

    def cover_snapshots(self) -> list[CoverSnapshot]:
        """Return snapshots for all enabled covers."""
        return [
            self.cover_snapshot(cover.object_id)
            for cover in self._require_house().enabled_covers
        ]

    def covers_by_state(self, state: CoverState) -> list[CoverSnapshot]:
        return [
            snapshot
            for snapshot in self.cover_snapshots()
            if snapshot.state is state
        ]

    def covers_open(self) -> list[CoverSnapshot]:
        return self.covers_by_state(CoverState.OPEN)

    def covers_closed(self) -> list[CoverSnapshot]:
        return self.covers_by_state(CoverState.CLOSED)

    def covers_opening(self) -> list[CoverSnapshot]:
        return self.covers_by_state(CoverState.OPENING)

    def covers_closing(self) -> list[CoverSnapshot]:
        return self.covers_by_state(CoverState.CLOSING)

    def covers_moving(self) -> list[CoverSnapshot]:
        return [item for item in self.cover_snapshots() if item.is_moving]

    def covers_intermediate(self) -> list[CoverSnapshot]:
        return self.covers_by_state(CoverState.INTERMEDIATE)

    def covers_error(self) -> list[CoverSnapshot]:
        return self.covers_by_state(CoverState.ERROR)

    def cover_state_summary(self) -> dict[str, int]:
        snapshots = self.cover_snapshots()
        return {
            state.value: sum(
                1 for snapshot in snapshots if snapshot.state is state
            )
            for state in CoverState
        }

    def cover_feedback_entities(self) -> set[str]:
        entities: set[str] = set()
        for cover in self._require_house().enabled_covers:
            entities.update(cover.feedback_entity_ids)
        return entities

    async def async_cover_open(self, cover_id: str) -> dict[str, Any]:
        """Send an open command unless the cover is already open/opening."""
        cover = self._require_house().cover(cover_id)
        snapshot = self.cover_snapshot(cover_id)

        if snapshot.is_open or snapshot.is_opening:
            return {
                "cover_id": cover_id,
                "command_sent": False,
                "reason": snapshot.state.value,
            }

        await self.hass.services.async_call(
            "button",
            "press",
            {"entity_id": cover.open_command_entity_id},
            blocking=True,
        )
        return {
            "cover_id": cover_id,
            "command_sent": True,
            "command": "open",
        }

    async def async_cover_close(self, cover_id: str) -> dict[str, Any]:
        """Send a close command unless the cover is already closed/closing."""
        cover = self._require_house().cover(cover_id)
        snapshot = self.cover_snapshot(cover_id)

        if snapshot.is_closed or snapshot.is_closing:
            return {
                "cover_id": cover_id,
                "command_sent": False,
                "reason": snapshot.state.value,
            }

        await self.hass.services.async_call(
            "button",
            "press",
            {"entity_id": cover.close_command_entity_id},
            blocking=True,
        )
        return {
            "cover_id": cover_id,
            "command_sent": True,
            "command": "close",
        }

    async def async_cover_blades_open(
        self, cover_id: str
    ) -> dict[str, Any]:
        """Send the PLC command for opening the slats."""
        cover = self._require_house().cover(cover_id)
        await self.hass.services.async_call(
            "button",
            "press",
            {"entity_id": cover.blades_open_command_entity_id},
            blocking=True,
        )
        return {
            "cover_id": cover_id,
            "command_sent": True,
            "command": "blades_open",
        }

    async def async_cover_blades_close(
        self, cover_id: str
    ) -> dict[str, Any]:
        """Send the PLC command for closing the slats."""
        cover = self._require_house().cover(cover_id)
        await self.hass.services.async_call(
            "button",
            "press",
            {"entity_id": cover.blades_close_command_entity_id},
            blocking=True,
        )
        return {
            "cover_id": cover_id,
            "command_sent": True,
            "command": "blades_close",
        }

    def security_snapshot(self) -> SecuritySnapshot:
        """Return semantic security derived from the Access runtime."""
        return SecurityEngine.evaluate(self.access_snapshot())

    def lighting_objects_on(self) -> list[Light]:
        """Return enabled light objects whose feedback currently reports on."""
        house = self._require_house()
        return [
            light
            for light in house.lights.values()
            if light.enabled and light.state_entity_ids and self._is_on(light)
        ]

    def lighting_count_on(self) -> int:
        """Return the number of WNHF light objects currently reporting on."""
        return len(self.lighting_objects_on())

    def lighting_names_on(self) -> list[str]:
        """Return human-readable names of WNHF light objects reporting on."""
        return [light.name for light in self.lighting_objects_on()]

    def lighting_ids_on(self) -> list[str]:
        """Return stable WNHF IDs of light objects currently reporting on."""
        return [light.object_id for light in self.lighting_objects_on()]

    def lighting_feedback_entities(self) -> set[str]:
        """Return all currently configured light feedback entity IDs."""
        house = self._require_house()
        return {
            entity_id
            for light in house.lights.values()
            if light.enabled
            for entity_id in light.state_entity_ids
        }

    def house_snapshot(self) -> HouseSnapshot:
        """Build the current aggregate state of the complete house."""
        house = self._require_house()
        access = self.access_snapshot()
        security = SecurityEngine.evaluate(access)
        validation = self.validation_snapshot()

        lights_on = self.lighting_objects_on()
        covers_moving = self.covers_moving()
        covers_error = self.covers_error()

        validation_status = (
            validation.status if validation is not None else "pending"
        )
        quality_score = (
            validation.quality_score if validation is not None else 0
        )

        if (
            validation_status == "error"
            or covers_error
            or not security.all_access_available
        ):
            state = HouseState.ERROR
        elif security.alert or security.access_attention_required:
            state = HouseState.ATTENTION
        elif lights_on or covers_moving:
            state = HouseState.ACTIVITY
        else:
            state = HouseState.READY

        return HouseSnapshot(
            house_id=house.object_id,
            house_name=house.name,
            state=state,
            secure=security.secure,
            all_access_available=security.all_access_available,
            access_attention_required=(
                security.access_attention_required
            ),
            access_insecure_count=security.insecure_count,
            access_unavailable_count=security.unavailable_count,
            access_attention_count=security.attention_count,
            access_insecure_ids=security.insecure_ids,
            access_insecure_names=security.insecure_names,
            access_unavailable_ids=security.unavailable_ids,
            access_unavailable_names=security.unavailable_names,
            access_attention_ids=security.attention_ids,
            access_attention_names=security.attention_names,
            validation_status=validation_status,
            quality_score=quality_score,
            lights_on_count=len(lights_on),
            light_ids_on=tuple(light.object_id for light in lights_on),
            light_names_on=tuple(light.name for light in lights_on),
            openings_open_count=security.open_count,
            opening_ids_open=security.opening_ids,
            opening_names_open=security.opening_names,
            covers_opening_count=len(self.covers_opening()),
            covers_closing_count=len(self.covers_closing()),
            covers_moving_count=len(covers_moving),
            covers_error_count=len(covers_error),
            cover_ids_moving=tuple(
                snapshot.cover.object_id for snapshot in covers_moving
            ),
            cover_names_moving=tuple(
                snapshot.cover.name for snapshot in covers_moving
            ),
            cover_ids_error=tuple(
                snapshot.cover.object_id for snapshot in covers_error
            ),
        )

    def house_feedback_entities(self) -> set[str]:
        """Return every source entity that can change the House Snapshot."""
        return {
            *self.lighting_feedback_entities(),
            *self.opening_feedback_entities(),
            *self.cover_feedback_entities(),
        }

    def diagnostics_snapshot(self) -> DiagnosticsSnapshot:
        """Build the current WNHF diagnostics snapshot."""
        house = self.house
        registry_loaded = house is not None

        room_count = len(house.rooms) if house is not None else 0
        light_count = len(house.lights) if house is not None else 0
        opening_count = len(house.openings) if house is not None else 0
        cover_count = len(house.covers) if house is not None else 0
        enabled_light_count = (
            len(house.enabled_lights) if house is not None else 0
        )
        controllable_light_count = (
            len(house.controllable_lights) if house is not None else 0
        )

        warning_count = len(self.registry_warnings)
        health_score = max(0, 100 - (warning_count * 2))

        if not registry_loaded:
            runtime_status = "error"
            registry_status = "error"
            health_status = "error"
            health_score = 0
        elif warning_count:
            runtime_status = "running"
            registry_status = "warning"
            health_status = "warning"
        else:
            runtime_status = "running"
            registry_status = "valid"
            health_status = "healthy"

        capabilities = {
            CAPABILITY_HOUSE_MODEL: registry_loaded,
            CAPABILITY_HOUSE_ENGINE: registry_loaded,
            CAPABILITY_PROVIDER_MODEL: True,
            CAPABILITY_RULE_ENGINE: True,
            CAPABILITY_CONTEXT_ENGINE: True,
            CAPABILITY_POLICY_ENGINE: True,
            CAPABILITY_DECISION_ENGINE: True,
            CAPABILITY_EXECUTION_ENGINE: True,
            CAPABILITY_LIGHTING: registry_loaded,
            CAPABILITY_OPENINGS: registry_loaded,
            CAPABILITY_SECURITY: registry_loaded,
            CAPABILITY_COVERS: registry_loaded,
            CAPABILITY_DIAGNOSTICS: True,
            CAPABILITY_VALIDATION: registry_loaded,
        }

        modules = {
            MODULE_EXECUTIONS: ModuleDiagnostic(
                module_id=MODULE_EXECUTIONS,
                version=VERSION,
                status="dry_run",
                objects=(
                    len(self.last_execution_plan.steps)
                    if self.last_execution_plan is not None
                    else 0
                ),
                services=(
                    "execution_plan",
                    "executions_snapshot",
                ),
                entities=(
                    "sensor.wnhf_execution_last_status",
                    "sensor.wnhf_execution_last_steps",
                ),
            ),
            MODULE_DECISIONS: ModuleDiagnostic(
                module_id=MODULE_DECISIONS,
                version=VERSION,
                status="read_only",
                objects=len(self.decision_registry.decisions),
                services=(
                    "decisions_snapshot",
                    "decision_evaluate",
                    "reload_decisions",
                ),
                entities=(
                    "sensor.wnhf_decisions_loaded",
                    "sensor.wnhf_decision_last_status",
                    "sensor.wnhf_decision_last_action",
                ),
            ),
            MODULE_POLICIES: ModuleDiagnostic(
                module_id=MODULE_POLICIES,
                version=VERSION,
                status=self.policy_registry.mode.value,
                objects=len(self.policy_registry.policies),
                services=(
                    "policies_snapshot",
                    "policy_check",
                    "reload_policies",
                ),
                entities=(
                    "sensor.wnhf_policy_mode",
                    "sensor.wnhf_policies_loaded",
                    "sensor.wnhf_policy_last_decision",
                ),
            ),
            MODULE_CONTEXT: ModuleDiagnostic(
                module_id=MODULE_CONTEXT,
                version=VERSION,
                status=self.context_snapshot().state,
                objects=4 + len(self.rule_registry.rules),
                services=("context_snapshot",),
                entities=(
                    "sensor.wnhf_context",
                    "sensor.wnhf_context_message",
                    "sensor.wnhf_context_confidence",
                    "sensor.wnhf_activity_score",
                    "sensor.wnhf_attention_score",
                ),
            ),
            MODULE_RULES: ModuleDiagnostic(
                module_id=MODULE_RULES,
                version=VERSION,
                status=(
                    self.rule_snapshot.status
                    if self.rule_snapshot is not None
                    else (
                        "degraded"
                        if self.rule_registry.warnings
                        else "ready"
                    )
                ),
                objects=len(self.rule_registry.rules),
                services=(
                    "rules_snapshot",
                    "evaluate_rules",
                    "reload_rules",
                ),
                entities=(
                    "sensor.wnhf_rule_engine_status",
                    "sensor.wnhf_rules_loaded",
                    "sensor.wnhf_rules_matched",
                ),
            ),
            MODULE_CAPABILITIES: ModuleDiagnostic(
                module_id=MODULE_CAPABILITIES,
                version=VERSION,
                status="running",
                objects=len(self.providers.provider_ids()),
                services=("capabilities_snapshot",),
                entities=(
                    "sensor.wnhf_capabilities_status",
                    "sensor.wnhf_capabilities_supported",
                ),
            ),
            MODULE_HOUSE: ModuleDiagnostic(
                module_id=MODULE_HOUSE,
                version=VERSION,
                status=(
                    self.house_snapshot().state.value
                    if registry_loaded
                    else "error"
                ),
                objects=1,
                services=("house_snapshot",),
                entities=(
                    "binary_sensor.wnhf_house_ready",
                    "sensor.wnhf_house_status",
                    "sensor.wnhf_house_message",
                    "sensor.wnhf_house_activity",
                ),
            ),
            MODULE_CORE: ModuleDiagnostic(
                module_id=MODULE_CORE,
                version=VERSION,
                status="running" if registry_loaded else "error",
                objects=room_count + light_count + opening_count + cover_count,
                services=("reload_registry", "list_registry", "get_object"),
                entities=(),
            ),
            MODULE_LIGHTING: ModuleDiagnostic(
                module_id=MODULE_LIGHTING,
                version=VERSION,
                status="running" if registry_loaded else "error",
                objects=light_count,
                services=(
                    "lighting_all_off",
                    "lighting_room_off",
                    "lighting_object_off",
                ),
                entities=(
                    "binary_sensor.wnhf_lighting_any_on",
                    "binary_sensor.wnhf_lighting_all_off",
                    "sensor.wnhf_lighting_count_on",
                    "sensor.wnhf_lighting_status",
                    "sensor.wnhf_lighting_message",
                    *(
                        f"light.wnhf_{light.object_id.removeprefix('light.').replace('.', '_')}"
                        for light in house.enabled_lights
                        if light.controllable
                    ),
                ) if house is not None else (),
            ),
            MODULE_OPENINGS: ModuleDiagnostic(
                module_id=MODULE_OPENINGS,
                version=VERSION,
                status="running" if registry_loaded else "error",
                objects=opening_count,
                services=(),
                entities=(
                    "binary_sensor.wnhf_openings_any_open",
                    "binary_sensor.wnhf_openings_all_closed",
                    "sensor.wnhf_openings_count_open",
                    "sensor.wnhf_openings_status",
                    "sensor.wnhf_openings_message",
                ),
            ),
            MODULE_SECURITY: ModuleDiagnostic(
                module_id=MODULE_SECURITY,
                version=VERSION,
                status="running" if registry_loaded else "error",
                objects=opening_count,
                services=(),
                entities=(
                    "binary_sensor.wnhf_security_secure",
                    "binary_sensor.wnhf_security_alert",
                    "sensor.wnhf_security_level",
                    "sensor.wnhf_security_message",
                    "sensor.wnhf_security_openings",
                ),
            ),
            MODULE_COVERS: ModuleDiagnostic(
                module_id=MODULE_COVERS,
                version=VERSION,
                status="running" if registry_loaded else "error",
                objects=cover_count,
                services=(),
                entities=tuple(
                    f"cover.wnhf_{cover.object_id.removeprefix('cover.').replace('.', '_')}"
                    for cover in house.enabled_covers
                ) if house is not None else (),
            ),
            MODULE_VALIDATOR: ModuleDiagnostic(
                module_id=MODULE_VALIDATOR,
                version=VERSION,
                status=(
                    self.validation_report.status
                    if self.validation_report is not None
                    else "pending"
                ),
                objects=(
                    len(self.validation_report.issues)
                    if self.validation_report is not None
                    else 0
                ),
                services=("validate_registry",),
                entities=(
                    "binary_sensor.wnhf_registry_valid",
                    "sensor.wnhf_registry_validation_status",
                    "sensor.wnhf_registry_validation_issues",
                    "sensor.wnhf_quality_score",
                ),
            ),
            MODULE_DIAGNOSTICS: ModuleDiagnostic(
                module_id=MODULE_DIAGNOSTICS,
                version=VERSION,
                status="running",
                objects=0,
                services=(),
                entities=(
                    "binary_sensor.wnhf_framework_healthy",
                    "sensor.wnhf_framework_version",
                    "sensor.wnhf_runtime_status",
                    "sensor.wnhf_health_score",
                    "sensor.wnhf_registry_status",
                    "sensor.wnhf_module_status",
                    "sensor.wnhf_capabilities",
                    "sensor.wnhf_registry_load_time",
                    "sensor.wnhf_last_action",
                    "sensor.wnhf_last_action_time",
                    "sensor.wnhf_performance_summary",
                ),
            ),
        }

        return DiagnosticsSnapshot(
            framework_version=VERSION,
            runtime_status=runtime_status,
            health_status=health_status,
            health_score=health_score,
            registry_status=registry_status,
            registry_loaded_at=self.registry_loaded_at,
            registry_load_ms=self.registry_load_ms,
            house_id=house.object_id if house is not None else None,
            house_name=house.name if house is not None else None,
            room_count=room_count,
            light_count=light_count,
            opening_count=opening_count,
            cover_count=cover_count,
            enabled_light_count=enabled_light_count,
            controllable_light_count=controllable_light_count,
            warning_count=warning_count,
            warnings=self.registry_warnings,
            capabilities=capabilities,
            modules=modules,
        )

    def list_registry(self, registry_type: str) -> dict[str, Any]:
        """Return one supported registry collection."""
        house = self._require_house()

        if registry_type == REGISTRY_TYPE_ROOMS:
            objects = house.list_rooms()
        elif registry_type == REGISTRY_TYPE_LIGHTS:
            objects = house.list_lights()
        elif registry_type == REGISTRY_TYPE_OPENINGS:
            objects = house.list_openings()
        elif registry_type == REGISTRY_TYPE_COVERS:
            objects = house.list_covers()
        else:
            raise ValueError(f"Unsupported registry type: {registry_type}")

        return {
            "type": registry_type,
            "count": len(objects),
            "objects": objects,
        }

    def get_object(self, object_id: str) -> dict[str, Any]:
        """Return one registry object by stable WNHF ID."""
        house = self._require_house()
        try:
            obj = house.object(object_id)
        except KeyError as err:
            raise ValueError(str(err)) from err
        result = obj.as_dict()
        if result.get("object_type") == "cover":
            result["runtime"] = self.cover_snapshot(object_id).as_dict()
        elif result.get("object_type") == "light":
            result["runtime"] = self.light_snapshot(object_id).as_dict()
        return result

    async def async_lighting_all_off(self) -> dict[str, Any]:
        """Switch off all controllable lights that currently report on."""
        started = perf_counter()
        house = self._require_house()
        switched: list[str] = []

        for light in house.controllable_lights:
            if await self._async_toggle_off(light):
                switched.append(light.object_id)

        duration_ms = round((perf_counter() - started) * 1000, 2)
        self.performance.record(
            ACTION_LIGHTING_ALL_OFF,
            duration_ms,
            datetime.now(UTC),
        )

        result = {
            "switched_count": len(switched),
            "light_ids": switched,
            "duration_ms": duration_ms,
        }
        _LOGGER.info(
            "Red Queen Lighting All Off: %s object(s) switched in %.2f ms",
            len(switched),
            duration_ms,
        )
        return result

    async def async_lighting_room_off(self, room_id: str) -> dict[str, Any]:
        """Switch off controllable lights in one WNHF room."""
        started = perf_counter()
        house = self._require_house()
        if room_id not in house.rooms:
            raise ValueError(f"Unknown WNHF room id: {room_id}")

        switched: list[str] = []
        for light in house.room(room_id).lights:
            if light.room_id != room_id:
                continue
            if await self._async_toggle_off(light):
                switched.append(light.object_id)

        duration_ms = round((perf_counter() - started) * 1000, 2)
        self.performance.record(
            ACTION_LIGHTING_ROOM_OFF,
            duration_ms,
            datetime.now(UTC),
        )

        result = {
            "room_id": room_id,
            "switched_count": len(switched),
            "light_ids": switched,
            "duration_ms": duration_ms,
        }
        _LOGGER.info(
            "Red Queen Lighting Room Off (%s): %s object(s) switched in %.2f ms",
            room_id,
            len(switched),
            duration_ms,
        )
        return result

    async def async_lighting_object_off(self, light_id: str) -> dict[str, Any]:
        """Switch off one WNHF light object."""
        started = perf_counter()
        house = self._require_house()
        light = house.lights.get(light_id)
        if light is None:
            raise ValueError(f"Unknown WNHF light id: {light_id}")
        if not light.controllable:
            raise ValueError(f"Red Queen light is not controllable: {light_id}")

        switched = await self._async_toggle_off(light)
        duration_ms = round((perf_counter() - started) * 1000, 2)
        self.performance.record(
            ACTION_LIGHTING_OBJECT_OFF,
            duration_ms,
            datetime.now(UTC),
        )

        result = {
            "light_id": light_id,
            "switched": switched,
            "duration_ms": duration_ms,
        }
        _LOGGER.info(
            "Red Queen Lighting Object Off (%s): switched=%s in %.2f ms",
            light_id,
            switched,
            duration_ms,
        )
        return result
