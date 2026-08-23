"""Service registration for WNHF."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_LIGHT_ID,
    ATTR_OBJECT_ID,
    ATTR_REGISTRY_TYPE,
    ATTR_ROOM_ID,
    ATTR_POLICY_ID,
    ATTR_DECISION_ID,
    ATTR_EXECUTION_DECISION_ID,
    ATTR_EXECUTION_CONFIRM,
    ATTR_PUBLIC_EXECUTION_ID,
    ATTR_CONFLICT_POLICY,
    ATTR_QUEUE_TIMEOUT,
    DOMAIN,
    SERVICE_GET_OBJECT,
    SERVICE_LIGHTING_ALL_OFF,
    SERVICE_LIGHTING_OBJECT_OFF,
    SERVICE_LIGHTING_ROOM_OFF,
    SERVICE_LIST_REGISTRY,
    SERVICE_RELOAD_REGISTRY,
    SERVICE_PLANTS_SNAPSHOT,
    SERVICE_VALIDATE_REGISTRY,
    SERVICE_CONFIGURATION_SNAPSHOT,
    SERVICE_HOUSE_SNAPSHOT,
    SERVICE_ACCESS_SNAPSHOT,
    SERVICE_CAPABILITIES_SNAPSHOT,
    SERVICE_OBJECT_CAPABILITIES_SNAPSHOT,
    SERVICE_RULES_SNAPSHOT,
    SERVICE_EVALUATE_RULES,
    SERVICE_RELOAD_RULES,
    SERVICE_CONTEXT_SNAPSHOT,
    SERVICE_POLICIES_SNAPSHOT,
    SERVICE_POLICY_CHECK,
    SERVICE_RELOAD_POLICIES,
    SERVICE_DECISIONS_SNAPSHOT,
    SERVICE_DECISION_EVALUATE,
    SERVICE_RELOAD_DECISIONS,
    SERVICE_REGISTRY_RECOVERY_REPORT,
    SERVICE_EXECUTION_PLAN,
    SERVICE_EXECUTIONS_SNAPSHOT,
    SERVICE_EXECUTION_COMMIT,
    SERVICE_EXECUTION_AUDIT,
    SERVICE_EXECUTE,
    SERVICE_MULTI_STEP_PLAN,
    SERVICE_EXECUTION_CAPABILITIES_SNAPSHOT,
    SERVICE_ACCESS_OBJECT_EXECUTE,
    SERVICE_ACCESS_EXECUTION_AUDIT,
    SERVICE_ACCESS_RESULT_CATALOG,
    SERVICE_PROVIDER_QUALIFICATION,
    SERVICE_PROVIDER_CONTRACT,
    SERVICE_PROVIDER_REGISTRY,
    SERVICE_PROVIDER_DISCOVERY,
    SERVICE_PROVIDER_DIAGNOSTICS,
    SERVICE_CAPABILITY_REGISTRY,
    SERVICE_CAPABILITY_RESOLVER,
    SERVICE_CAPABILITY_MANAGER,
    SERVICE_EXECUTION_MANAGER,
    SERVICE_EXECUTION_ACTION,
    SERVICE_EXECUTION_DRY_RUN,
    SERVICE_EXECUTION_EXECUTE,
    SERVICE_EXECUTION_QUALIFICATION,
    SERVICE_EXECUTION_RUNTIME_HEALTH,
    SIGNAL_EXECUTION_RUNTIME_HEALTH_UPDATED,
    SIGNAL_EXECUTION_QUALIFICATION_UPDATED,
    SIGNAL_EXECUTION_EXECUTE_UPDATED,
    SIGNAL_EXECUTION_DRY_RUN_UPDATED,
    SIGNAL_EXECUTION_MANAGER_UPDATED,
    SERVICE_CAPABILITY_LIST,
    SERVICE_CAPABILITY_INFO,
    SIGNAL_CAPABILITY_MANAGER_UPDATED,
    SIGNAL_CAPABILITY_RESOLVER_UPDATED,
    SIGNAL_CAPABILITY_REGISTRY_UPDATED,
    SIGNAL_PROVIDER_DIAGNOSTICS_UPDATED,
    SIGNAL_PROVIDER_DISCOVERY_UPDATED,
    SIGNAL_PROVIDER_REGISTRY_UPDATED,
    SIGNAL_PROVIDER_CONTRACT_UPDATED,
    SIGNAL_PROVIDER_QUALIFICATION_UPDATED,
    SIGNAL_ACCESS_RESULT_CATALOG_UPDATED,
    ATTR_ACCESS_OBJECT_ID,
    ATTR_ACCESS_CAPABILITY_ID,
    SIGNAL_ACCESS_EXECUTION_UPDATED,
    SERVICE_MULTI_STEP_SIMULATE,
    SERVICE_GENERIC_TRANSACTION_RUN,
    SERVICE_REAL_STEP_EXECUTE,
    SERVICE_SEQUENTIAL_ROOM_EXECUTE,
    SERVICE_HOUSE_EXECUTE,
    SERVICE_HOUSE_EXECUTION_AUDIT,
    SERVICE_TRANSACTION_LOCKS,
    SERVICE_TRANSACTION_QUEUE,
    SERVICE_SYSTEM_STATUS,
    SERVICE_RELEASE_SCOPE,
    SERVICE_RELEASE_INFO,
    SERVICE_PUBLIC_API,
    SERVICE_QUALIFICATION,
    SERVICE_UPGRADE_CHECK,
    SERVICE_SEQUENTIAL_ROOM_AUDIT,
    SERVICE_REAL_STEP_AUDIT,
    SERVICE_GENERIC_TRANSACTIONS_SNAPSHOT,
    SERVICE_MULTI_STEP_SIMULATIONS_SNAPSHOT,
    SIGNAL_PERFORMANCE_UPDATED,
    SIGNAL_REGISTRY_RELOADED,
    SIGNAL_VALIDATION_UPDATED,
    SIGNAL_HOUSE_UPDATED,
    SIGNAL_ACCESS_UPDATED,
    SIGNAL_CAPABILITIES_UPDATED,
    SIGNAL_OBJECT_CAPABILITIES_UPDATED,
    SIGNAL_RULES_UPDATED,
    SIGNAL_CONTEXT_UPDATED,
    SIGNAL_POLICIES_UPDATED,
    SIGNAL_DECISIONS_UPDATED,
    SIGNAL_EXECUTIONS_UPDATED,
    SIGNAL_EXECUTION_AUDIT_UPDATED,
    SIGNAL_PUBLIC_EXECUTION_UPDATED,
    SIGNAL_EXECUTION_MANAGER_UPDATED,
    SIGNAL_TRANSACTION_LOCKS_UPDATED,
    SIGNAL_TRANSACTION_QUEUE_UPDATED,
    SIGNAL_SYSTEM_STATUS_UPDATED,
    SIGNAL_RELEASE_SCOPE_UPDATED,
    SIGNAL_RELEASE_INFO_UPDATED,
    SIGNAL_PUBLIC_API_UPDATED,
    SIGNAL_QUALIFICATION_UPDATED,
    SIGNAL_UPGRADE_CHECK_UPDATED,
    SIGNAL_MULTI_STEP_PLAN_UPDATED,
    SIGNAL_EXECUTION_CAPABILITIES_UPDATED,
    SIGNAL_MULTI_STEP_SIMULATION_UPDATED,
    SIGNAL_PLANTS_UPDATED,
    SIGNAL_GENERIC_TRANSACTION_UPDATED,
    SIGNAL_REAL_STEP_UPDATED,
    SIGNAL_SEQUENTIAL_ROOM_UPDATED,
    SIGNAL_HOUSE_EXECUTION_UPDATED,
    SUPPORTED_REGISTRY_TYPES,
    CONFLICT_POLICY_REJECT,
    CONFLICT_POLICY_WAIT,
    DEFAULT_CONFLICT_POLICY,
    DEFAULT_QUEUE_TIMEOUT_SECONDS,
    MAX_QUEUE_TIMEOUT_SECONDS,
)
from .engine import WNHFEngine
from .configuration import RegistryConfigurationManager
from .executions import AccessResultCatalog

_LOGGER = logging.getLogger(__name__)


def async_unregister_services(hass: HomeAssistant) -> tuple[str, ...]:
    """Remove all currently registered WNHF services.

    WNHF owns the complete Home Assistant service domain ``wnhf``.  Discovering
    the active service names at unload time deliberately avoids a second,
    manually maintained service list that could drift when services are added
    or removed in future work packages.
    """
    domain_services = hass.services.async_services().get(DOMAIN, {})
    service_names = tuple(sorted(domain_services))

    for service_name in service_names:
        hass.services.async_remove(DOMAIN, service_name)

    return service_names


ROOM_SCHEMA = vol.Schema({vol.Required(ATTR_ROOM_ID): cv.string})
LIGHT_SCHEMA = vol.Schema({vol.Required(ATTR_LIGHT_ID): cv.string})
LIST_REGISTRY_SCHEMA = vol.Schema(
    {vol.Required(ATTR_REGISTRY_TYPE): vol.In(SUPPORTED_REGISTRY_TYPES)}
)
GET_OBJECT_SCHEMA = vol.Schema(
    {vol.Required(ATTR_OBJECT_ID): cv.string}
)
POLICY_CHECK_SCHEMA = vol.Schema(
    {vol.Required(ATTR_POLICY_ID): cv.string}
)
DECISION_EVALUATE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_DECISION_ID): cv.string}
)
EXECUTION_PLAN_SCHEMA = vol.Schema(
    {vol.Required(ATTR_EXECUTION_DECISION_ID): cv.string}
)
EXECUTION_COMMIT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EXECUTION_DECISION_ID): cv.string,
        vol.Required(ATTR_EXECUTION_CONFIRM): cv.boolean,
    }
)
PUBLIC_EXECUTE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PUBLIC_EXECUTION_ID): cv.string,
        vol.Required(ATTR_EXECUTION_CONFIRM): cv.boolean,
        vol.Optional(
            ATTR_CONFLICT_POLICY,
            default=DEFAULT_CONFLICT_POLICY,
        ): vol.In({
            CONFLICT_POLICY_REJECT,
            CONFLICT_POLICY_WAIT,
        }),
        vol.Optional(
            ATTR_QUEUE_TIMEOUT,
            default=DEFAULT_QUEUE_TIMEOUT_SECONDS,
        ): vol.All(
            vol.Coerce(float),
            vol.Range(min=0.1, max=MAX_QUEUE_TIMEOUT_SECONDS),
        ),
    }
)


ACCESS_OBJECT_EXECUTE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ACCESS_OBJECT_ID): cv.string,
        vol.Required(ATTR_ACCESS_CAPABILITY_ID): vol.In(
            [
                "access.lock",
                "access.unlock",
                "access.door_open",
                "access.toggle",
            ]
        ),
        vol.Required(ATTR_EXECUTION_CONFIRM): cv.boolean,
    }
)


async def async_register_services(
    hass: HomeAssistant, engine: WNHFEngine
) -> None:
    """Register WNHF service actions."""

    async def handle_list_registry(call: ServiceCall) -> dict:
        return engine.list_registry(call.data[ATTR_REGISTRY_TYPE])

    async def handle_get_object(call: ServiceCall) -> dict:
        return engine.get_object(call.data[ATTR_OBJECT_ID])

    async def handle_plants_snapshot(call: ServiceCall) -> dict:
        result = engine.plants_snapshot()
        async_dispatcher_send(hass, SIGNAL_PLANTS_UPDATED)
        return result

    async def handle_all_off(call: ServiceCall) -> dict:
        result = await engine.async_lighting_all_off()
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_room_off(call: ServiceCall) -> dict:
        result = await engine.async_lighting_room_off(call.data[ATTR_ROOM_ID])
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_object_off(call: ServiceCall) -> dict:
        result = await engine.async_lighting_object_off(call.data[ATTR_LIGHT_ID])
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result


    async def handle_release_info(
        call: ServiceCall,
    ) -> dict:
        result = engine.release_info_snapshot()
        async_dispatcher_send(hass, SIGNAL_RELEASE_INFO_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_public_api(
        call: ServiceCall,
    ) -> dict:
        result = engine.public_api_snapshot()
        async_dispatcher_send(hass, SIGNAL_PUBLIC_API_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_qualification(
        call: ServiceCall,
    ) -> dict:
        result = await engine.qualification_snapshot()
        async_dispatcher_send(hass, SIGNAL_QUALIFICATION_UPDATED)
        async_dispatcher_send(hass, SIGNAL_SYSTEM_STATUS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_upgrade_check(
        call: ServiceCall,
    ) -> dict:
        result = engine.upgrade_check_snapshot()
        async_dispatcher_send(hass, SIGNAL_UPGRADE_CHECK_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_release_scope(
        call: ServiceCall,
    ) -> dict:
        result = engine.release_scope_snapshot()
        async_dispatcher_send(hass, SIGNAL_RELEASE_SCOPE_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_system_status(
        call: ServiceCall,
    ) -> dict:
        result = await engine.system_status_snapshot()
        # system_status_snapshot performs a fresh non-destructive registry
        # validation. Publish that refreshed canonical report to the existing
        # validation/house entities in the same service transaction.
        async_dispatcher_send(hass, SIGNAL_VALIDATION_UPDATED)
        async_dispatcher_send(hass, SIGNAL_HOUSE_UPDATED)
        async_dispatcher_send(hass, SIGNAL_SYSTEM_STATUS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_transaction_queue(
        call: ServiceCall,
    ) -> dict:
        result = await engine.transaction_queue_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_TRANSACTION_QUEUE_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_transaction_locks(
        call: ServiceCall,
    ) -> dict:
        result = await engine.transaction_locks_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_TRANSACTION_LOCKS_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_house_execute(
        call: ServiceCall,
    ) -> dict:
        result = await engine.async_house_execute(
            call.data[ATTR_EXECUTION_DECISION_ID],
            call.data[ATTR_EXECUTION_CONFIRM],
        )
        async_dispatcher_send(hass, SIGNAL_HOUSE_EXECUTION_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_house_execution_audit(
        call: ServiceCall,
    ) -> dict:
        result = engine.house_execution_audit_snapshot()
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_sequential_room_execute(
        call: ServiceCall,
    ) -> dict:
        result = await engine.async_sequential_room_execute(
            call.data[ATTR_EXECUTION_DECISION_ID],
            call.data[ATTR_EXECUTION_CONFIRM],
        )
        async_dispatcher_send(hass, SIGNAL_SEQUENTIAL_ROOM_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_sequential_room_audit(
        call: ServiceCall,
    ) -> dict:
        result = engine.sequential_room_audit_snapshot()
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_real_step_execute(
        call: ServiceCall,
    ) -> dict:
        result = await engine.async_real_step_execute(
            call.data[ATTR_EXECUTION_DECISION_ID],
            call.data[ATTR_EXECUTION_CONFIRM],
        )
        async_dispatcher_send(hass, SIGNAL_REAL_STEP_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_real_step_audit(
        call: ServiceCall,
    ) -> dict:
        result = engine.real_step_audit_snapshot()
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_generic_transaction_run(call: ServiceCall) -> dict:
        result=engine.generic_transaction_run(
            call.data[ATTR_EXECUTION_DECISION_ID],
            call.data[ATTR_EXECUTION_CONFIRM],
        )
        async_dispatcher_send(hass,SIGNAL_GENERIC_TRANSACTION_UPDATED)
        async_dispatcher_send(hass,SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_generic_transactions_snapshot(call: ServiceCall) -> dict:
        result=engine.generic_transactions_snapshot()
        async_dispatcher_send(hass,SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_multi_step_simulate(
        call: ServiceCall,
    ) -> dict:
        result = engine.multi_step_simulate(
            call.data[ATTR_EXECUTION_DECISION_ID],
            call.data[ATTR_EXECUTION_CONFIRM],
        )
        async_dispatcher_send(
            hass,
            SIGNAL_MULTI_STEP_SIMULATION_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_multi_step_simulations_snapshot(
        call: ServiceCall,
    ) -> dict:
        result = engine.multi_step_simulations_snapshot()
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_access_object_execute(
        call: ServiceCall,
    ) -> dict:
        result = await engine.async_access_object_execute(
            call.data[ATTR_ACCESS_OBJECT_ID],
            call.data[ATTR_ACCESS_CAPABILITY_ID],
            call.data[ATTR_EXECUTION_CONFIRM],
        )
        async_dispatcher_send(
            hass,
            SIGNAL_ACCESS_EXECUTION_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_EXECUTION_AUDIT_UPDATED)
        async_dispatcher_send(hass, SIGNAL_HOUSE_UPDATED)
        async_dispatcher_send(hass, SIGNAL_CAPABILITIES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_execution_runtime_health(
        call: ServiceCall,
    ) -> dict:
        result = await engine.execution_runtime_health()
        async_dispatcher_send(
            hass,
            SIGNAL_EXECUTION_RUNTIME_HEALTH_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_execution_qualification(
        call: ServiceCall,
    ) -> dict:
        result = engine.execution_qualification_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_EXECUTION_QUALIFICATION_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_execution_execute(
        call: ServiceCall,
    ) -> dict | None:
        result = await engine.execution_execute(
            action_id=str(call.data["action_id"]),
            target=dict(call.data.get("target", {})),
            parameters=dict(call.data.get("parameters", {})),
            confirmed=bool(call.data.get("confirmed", False)),
        )
        async_dispatcher_send(
            hass,
            SIGNAL_EXECUTION_EXECUTE_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result if call.return_response else None

    async def handle_execution_dry_run(
        call: ServiceCall,
    ) -> dict:
        result = await engine.execution_dry_run(
            action_id=str(call.data["action_id"]),
            target=dict(call.data.get("target", {})),
            parameters=dict(call.data.get("parameters", {})),
            confirmed=bool(call.data.get("confirmed", False)),
        )
        async_dispatcher_send(
            hass,
            SIGNAL_EXECUTION_DRY_RUN_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_execution_manager(
        call: ServiceCall,
    ) -> dict:
        result = await engine.execution_manager_status()
        async_dispatcher_send(
            hass,
            SIGNAL_EXECUTION_MANAGER_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_execution_action(
        call: ServiceCall,
    ) -> dict:
        result = await engine.execution_action_resolution(
            str(call.data["action_id"])
        )
        async_dispatcher_send(
            hass,
            SIGNAL_EXECUTION_MANAGER_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_capability_manager(
        call: ServiceCall,
    ) -> dict:
        result = await engine.capability_manager_status()
        async_dispatcher_send(
            hass,
            SIGNAL_CAPABILITY_MANAGER_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_capability_list(
        call: ServiceCall,
    ) -> dict:
        result = await engine.capability_manager_list()
        async_dispatcher_send(
            hass,
            SIGNAL_CAPABILITY_MANAGER_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_capability_info(
        call: ServiceCall,
    ) -> dict:
        result = await engine.capability_manager_info(
            str(call.data["capability_id"])
        )
        async_dispatcher_send(
            hass,
            SIGNAL_CAPABILITY_MANAGER_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_capability_resolver(
        call: ServiceCall,
    ) -> dict:
        result = engine.capability_resolver_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_CAPABILITY_RESOLVER_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_capability_registry(
        call: ServiceCall,
    ) -> dict:
        result = engine.capability_registry_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_CAPABILITY_REGISTRY_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_provider_diagnostics(
        call: ServiceCall,
    ) -> dict:
        result = engine.provider_diagnostics_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_PROVIDER_DIAGNOSTICS_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_provider_discovery(
        call: ServiceCall,
    ) -> dict:
        result = engine.provider_discovery_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_PROVIDER_DISCOVERY_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_provider_registry(
        call: ServiceCall,
    ) -> dict:
        result = engine.provider_registry_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_PROVIDER_REGISTRY_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_provider_contract(
        call: ServiceCall,
    ) -> dict:
        result = engine.provider_contract_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_PROVIDER_CONTRACT_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_provider_qualification(
        call: ServiceCall,
    ) -> dict:
        result = engine.provider_qualification_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_PROVIDER_QUALIFICATION_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_access_result_catalog(
        call: ServiceCall,
    ) -> dict:
        result = AccessResultCatalog.as_dict()
        async_dispatcher_send(
            hass,
            SIGNAL_ACCESS_RESULT_CATALOG_UPDATED,
        )
        return result

    async def handle_access_execution_audit(
        call: ServiceCall,
    ) -> dict:
        result = engine.access_execution_audit_snapshot()
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_execution_capabilities_snapshot(
        call: ServiceCall,
    ) -> dict:
        result = engine.execution_capabilities_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_EXECUTION_CAPABILITIES_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_multi_step_plan(
        call: ServiceCall,
    ) -> dict:
        result = engine.multi_step_plan(
            call.data[ATTR_EXECUTION_DECISION_ID],
        )
        async_dispatcher_send(hass, SIGNAL_MULTI_STEP_PLAN_UPDATED)
        async_dispatcher_send(hass, SIGNAL_EXECUTIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_public_execute(
        call: ServiceCall,
    ) -> dict:
        result = await engine.async_public_execute(
            call.data[ATTR_PUBLIC_EXECUTION_ID],
            call.data[ATTR_EXECUTION_CONFIRM],
            call.data[ATTR_CONFLICT_POLICY],
            call.data[ATTR_QUEUE_TIMEOUT],
        )
        async_dispatcher_send(hass, SIGNAL_PUBLIC_EXECUTION_UPDATED)
        async_dispatcher_send(hass, SIGNAL_EXECUTION_MANAGER_UPDATED)
        async_dispatcher_send(hass, SIGNAL_TRANSACTION_LOCKS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_TRANSACTION_QUEUE_UPDATED)
        async_dispatcher_send(hass, SIGNAL_EXECUTION_AUDIT_UPDATED)
        async_dispatcher_send(hass, SIGNAL_EXECUTIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_execution_commit(
        call: ServiceCall,
    ) -> dict:
        transaction = await engine.async_execution_commit(
            call.data[ATTR_EXECUTION_DECISION_ID],
            call.data[ATTR_EXECUTION_CONFIRM],
        )
        async_dispatcher_send(hass, SIGNAL_EXECUTION_AUDIT_UPDATED)
        async_dispatcher_send(hass, SIGNAL_EXECUTIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return transaction.as_dict()

    async def handle_execution_audit(
        call: ServiceCall,
    ) -> dict:
        result = engine.execution_audit_snapshot()
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_execution_plan(call: ServiceCall) -> dict:
        plan = engine.execution_plan(
            call.data[ATTR_EXECUTION_DECISION_ID]
        )
        async_dispatcher_send(hass, SIGNAL_EXECUTIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return plan.as_dict()

    async def handle_executions_snapshot(
        call: ServiceCall,
    ) -> dict:
        result = engine.executions_snapshot()
        async_dispatcher_send(hass, SIGNAL_EXECUTIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_registry_recovery_report(
        call: ServiceCall,
    ) -> dict:
        return engine.registry_recovery_report()

    async def handle_decisions_snapshot(
        call: ServiceCall,
    ) -> dict:
        result = engine.decisions_snapshot()
        async_dispatcher_send(hass, SIGNAL_DECISIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_decision_evaluate(call: ServiceCall) -> dict:
        result = engine.decision_evaluate(
            call.data[ATTR_DECISION_ID]
        )
        async_dispatcher_send(hass, SIGNAL_DECISIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result.as_dict()

    async def handle_reload_decisions(call: ServiceCall) -> dict:
        registry = await engine.async_load_decisions()
        async_dispatcher_send(hass, SIGNAL_DECISIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return {
            "registry": registry.as_dict(),
            "snapshot": engine.decisions_snapshot(),
        }

    async def handle_policies_snapshot(
        call: ServiceCall,
    ) -> dict:
        result = engine.policies_snapshot()
        async_dispatcher_send(hass, SIGNAL_POLICIES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_policy_check(call: ServiceCall) -> dict:
        decision = engine.policy_check(call.data[ATTR_POLICY_ID])
        async_dispatcher_send(hass, SIGNAL_POLICIES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return decision.as_dict()

    async def handle_reload_policies(call: ServiceCall) -> dict:
        registry = await engine.async_load_policies()
        async_dispatcher_send(hass, SIGNAL_POLICIES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return {
            "registry": registry.as_dict(),
            "snapshot": engine.policies_snapshot(),
        }

    async def handle_context_snapshot(
        call: ServiceCall,
    ) -> dict:
        snapshot = engine.context_snapshot()
        async_dispatcher_send(hass, SIGNAL_CONTEXT_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return snapshot.as_dict()

    async def handle_rules_snapshot(call: ServiceCall) -> dict:
        result = engine.rules_snapshot()
        async_dispatcher_send(hass, SIGNAL_RULES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return result

    async def handle_evaluate_rules(call: ServiceCall) -> dict:
        snapshot = engine.evaluate_rules()
        async_dispatcher_send(hass, SIGNAL_RULES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return snapshot.as_dict()

    async def handle_reload_rules(call: ServiceCall) -> dict:
        registry = await engine.async_load_rules()
        snapshot = engine.evaluate_rules()
        async_dispatcher_send(hass, SIGNAL_RULES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return {
            "registry": registry.as_dict(),
            "evaluation": snapshot.as_dict(),
        }

    async def handle_capabilities_snapshot(
        call: ServiceCall,
    ) -> dict:
        snapshot = engine.capabilities_snapshot()
        async_dispatcher_send(hass, SIGNAL_CAPABILITIES_UPDATED)
        return {
            "capabilities": snapshot,
            "providers": list(engine.providers.provider_ids()),
        }

    async def handle_object_capabilities_snapshot(
        call: ServiceCall,
    ) -> dict:
        snapshot = engine.object_capabilities_snapshot()
        async_dispatcher_send(
            hass,
            SIGNAL_OBJECT_CAPABILITIES_UPDATED,
        )
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return snapshot

    async def handle_access_snapshot(call: ServiceCall) -> dict:
        snapshot = engine.access_snapshot()
        async_dispatcher_send(hass, SIGNAL_ACCESS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_CAPABILITIES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return snapshot.as_dict()

    async def handle_house_snapshot(call: ServiceCall) -> dict:
        snapshot = engine.house_snapshot()
        async_dispatcher_send(hass, SIGNAL_HOUSE_UPDATED)
        return snapshot.as_dict()

    async def handle_validate(call: ServiceCall) -> dict:
        report = await engine.async_validate_registry()
        async_dispatcher_send(hass, SIGNAL_VALIDATION_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        _LOGGER.info(
            "Red Queen validation: status=%s, errors=%s, warnings=%s, score=%s",
            report.status,
            len(report.errors),
            len(report.warnings),
            report.quality_score,
        )
        return report.as_dict()

    async def handle_configuration_snapshot(call: ServiceCall) -> dict:
        """Inspect the on-disk registry even while Red Queen is in recovery."""
        manager = RegistryConfigurationManager(engine.registry_dir)
        return await hass.async_add_executor_job(manager.snapshot)

    async def handle_reload(call: ServiceCall) -> dict:
        house = await engine.async_load_registry()
        report = await engine.async_validate_registry()
        _LOGGER.info(
            "Red Queen registry reloaded: %s rooms, %s lights | "
            "validation=%s, errors=%s, warnings=%s",
            len(house.rooms),
            len(house.lights),
            report.status,
            len(report.errors),
            len(report.warnings),
        )
        async_dispatcher_send(hass, SIGNAL_REGISTRY_RELOADED)
        async_dispatcher_send(hass, SIGNAL_VALIDATION_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        return {
            "house_id": house.object_id,
            "house_name": house.name,
            "rooms": len(house.rooms),
            "lights": len(house.lights),
            "covers": len(house.covers),
            "openings": len(house.openings),
            "plants": len(house.plants),
            "warnings": list(engine.registry_warnings),
            "validation": report.as_dict(),
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_REGISTRY,
        handle_list_registry,
        schema=LIST_REGISTRY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_OBJECT,
        handle_get_object,
        schema=GET_OBJECT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PLANTS_SNAPSHOT,
        handle_plants_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIGHTING_ALL_OFF,
        handle_all_off,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIGHTING_ROOM_OFF,
        handle_room_off,
        schema=ROOM_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIGHTING_OBJECT_OFF,
        handle_object_off,
        schema=LIGHT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RELEASE_INFO,
        handle_release_info,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PUBLIC_API,
        handle_public_api,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_QUALIFICATION,
        handle_qualification,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPGRADE_CHECK,
        handle_upgrade_check,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RELEASE_SCOPE,
        handle_release_scope,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SYSTEM_STATUS,
        handle_system_status,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TRANSACTION_QUEUE,
        handle_transaction_queue,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TRANSACTION_LOCKS,
        handle_transaction_locks,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_HOUSE_EXECUTE,
        handle_house_execute,
        schema=EXECUTION_COMMIT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_HOUSE_EXECUTION_AUDIT,
        handle_house_execution_audit,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEQUENTIAL_ROOM_EXECUTE,
        handle_sequential_room_execute,
        schema=EXECUTION_COMMIT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEQUENTIAL_ROOM_AUDIT,
        handle_sequential_room_audit,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REAL_STEP_EXECUTE,
        handle_real_step_execute,
        schema=EXECUTION_COMMIT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REAL_STEP_AUDIT,
        handle_real_step_audit,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERIC_TRANSACTION_RUN,
        handle_generic_transaction_run,
        schema=EXECUTION_COMMIT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERIC_TRANSACTIONS_SNAPSHOT,
        handle_generic_transactions_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MULTI_STEP_SIMULATE,
        handle_multi_step_simulate,
        schema=EXECUTION_COMMIT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MULTI_STEP_SIMULATIONS_SNAPSHOT,
        handle_multi_step_simulations_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACCESS_OBJECT_EXECUTE,
        handle_access_object_execute,
        schema=ACCESS_OBJECT_EXECUTE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_RUNTIME_HEALTH,
        handle_execution_runtime_health,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_QUALIFICATION,
        handle_execution_qualification,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_EXECUTE,
        handle_execution_execute,
        schema=vol.Schema(
            {
                vol.Required("action_id"): cv.string,
                vol.Required("target"): dict,
                vol.Optional("parameters", default={}): dict,
                vol.Optional("confirmed", default=False): cv.boolean,
            }
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_DRY_RUN,
        handle_execution_dry_run,
        schema=vol.Schema(
            {
                vol.Required("action_id"): cv.string,
                vol.Required("target"): dict,
                vol.Optional("parameters", default={}): dict,
                vol.Optional("confirmed", default=False): cv.boolean,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_MANAGER,
        handle_execution_manager,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_ACTION,
        handle_execution_action,
        schema=vol.Schema(
            {
                vol.Required("action_id"): cv.string,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CAPABILITY_MANAGER,
        handle_capability_manager,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CAPABILITY_LIST,
        handle_capability_list,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CAPABILITY_INFO,
        handle_capability_info,
        schema=vol.Schema(
            {
                vol.Required("capability_id"): cv.string,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CAPABILITY_RESOLVER,
        handle_capability_resolver,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CAPABILITY_REGISTRY,
        handle_capability_registry,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PROVIDER_DIAGNOSTICS,
        handle_provider_diagnostics,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PROVIDER_DISCOVERY,
        handle_provider_discovery,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PROVIDER_REGISTRY,
        handle_provider_registry,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PROVIDER_CONTRACT,
        handle_provider_contract,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PROVIDER_QUALIFICATION,
        handle_provider_qualification,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACCESS_RESULT_CATALOG,
        handle_access_result_catalog,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACCESS_EXECUTION_AUDIT,
        handle_access_execution_audit,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_CAPABILITIES_SNAPSHOT,
        handle_execution_capabilities_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MULTI_STEP_PLAN,
        handle_multi_step_plan,
        schema=EXECUTION_PLAN_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTE,
        handle_public_execute,
        schema=PUBLIC_EXECUTE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_COMMIT,
        handle_execution_commit,
        schema=EXECUTION_COMMIT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_AUDIT,
        handle_execution_audit,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTION_PLAN,
        handle_execution_plan,
        schema=EXECUTION_PLAN_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTIONS_SNAPSHOT,
        handle_executions_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REGISTRY_RECOVERY_REPORT,
        handle_registry_recovery_report,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DECISIONS_SNAPSHOT,
        handle_decisions_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DECISION_EVALUATE,
        handle_decision_evaluate,
        schema=DECISION_EVALUATE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RELOAD_DECISIONS,
        handle_reload_decisions,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_POLICIES_SNAPSHOT,
        handle_policies_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_POLICY_CHECK,
        handle_policy_check,
        schema=POLICY_CHECK_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RELOAD_POLICIES,
        handle_reload_policies,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CONTEXT_SNAPSHOT,
        handle_context_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RULES_SNAPSHOT,
        handle_rules_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EVALUATE_RULES,
        handle_evaluate_rules,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RELOAD_RULES,
        handle_reload_rules,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CAPABILITIES_SNAPSHOT,
        handle_capabilities_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_OBJECT_CAPABILITIES_SNAPSHOT,
        handle_object_capabilities_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACCESS_SNAPSHOT,
        handle_access_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_HOUSE_SNAPSHOT,
        handle_house_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_VALIDATE_REGISTRY,
        handle_validate,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CONFIGURATION_SNAPSHOT,
        handle_configuration_snapshot,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RELOAD_REGISTRY,
        handle_reload,
        supports_response=SupportsResponse.OPTIONAL,
    )
