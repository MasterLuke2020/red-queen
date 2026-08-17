"""Canonical semantic execution-manager diagnostics and resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .action_contracts import get_canonical_action_contract


class ExecutionReadinessStatus(StrEnum):
    READY = "ready"
    SEMANTIC_READY_ONLY = "semantic_ready_only"
    ACTION_NOT_FOUND = "action_not_found"
    CAPABILITY_NOT_FOUND = "capability_not_found"
    CAPABILITY_DISABLED = "capability_disabled"
    CAPABILITY_UNRESOLVED = "capability_unresolved"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    CAPABILITY_UNHEALTHY = "capability_unhealthy"


@dataclass(frozen=True, slots=True)
class ExecutionActionResolution:
    action_id: str
    capability_id: str | None
    status: ExecutionReadinessStatus
    declared: bool
    resolved: bool
    semantically_ready: bool
    execution_enabled: bool
    executable: bool
    mutating: bool | None
    confirmation_required: bool | None
    selected_provider_ids: tuple[str, ...]
    capability: dict[str, Any] | None
    action_contract: dict[str, Any] | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "capability_id": self.capability_id,
            "status": self.status.value,
            "declared": self.declared,
            "resolved": self.resolved,
            "semantically_ready": self.semantically_ready,
            "execution_enabled": self.execution_enabled,
            "executable": self.executable,
            "mutating": self.mutating,
            "confirmation_required": self.confirmation_required,
            "selected_provider_ids": list(self.selected_provider_ids),
            "capability": self.capability,
            "action_contract": self.action_contract,
            "reason": self.reason,
        }


class SemanticExecutionManager:
    """Resolve semantic actions and expose the canonical execution surface."""

    API_VERSION = "1.1"
    VERSION = "1.6-rc6"
    EXECUTION_ENABLED = True
    READ_ONLY = False

    def __init__(self, capability_manager: Any, capability_registry: Any) -> None:
        self._capability_manager = capability_manager
        self._capability_registry = capability_registry

    async def async_status(self) -> dict[str, Any]:
        capability_status = await self._capability_manager.async_status()
        catalog = self._action_catalog()
        actions: list[dict[str, Any]] = []
        semantically_ready = 0
        real_execution_enabled = 0
        executable_now = 0

        for item in catalog:
            result = await self.async_resolve_action(item["action_id"])
            semantically_ready += int(result.semantically_ready)
            real_execution_enabled += int(result.execution_enabled)
            executable_now += int(result.executable)
            actions.append({
                **item,
                "status": result.status.value,
                "resolved": result.resolved,
                "semantically_ready": result.semantically_ready,
                "execution_enabled": result.execution_enabled,
                "executable_now": result.executable,
            })

        declared = len(actions)
        semantic_not_ready = declared - semantically_ready
        return {
            "api_version": self.API_VERSION,
            "manager_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "execution_enabled": self.EXECUTION_ENABLED,
            "read_only": self.READ_ONLY,
            "readiness_semantics": {
                "declared": "Action exists in the semantic capability registry.",
                "semantically_ready": (
                    "Capability is enabled and resolves to available, healthy providers."
                ),
                "real_execution_enabled": (
                    "Action has a canonical real-execution request contract."
                ),
                "executable_now": (
                    "Action is semantically ready and real execution is enabled."
                ),
            },
            "summary": {
                "capabilities": capability_status["summary"]["registered"],
                "declared_actions": declared,
                "semantically_ready": semantically_ready,
                "semantic_not_ready": semantic_not_ready,
                "real_execution_enabled": real_execution_enabled,
                "executable_now": executable_now,
                "all_semantically_ready": semantically_ready == declared,
                "all_enabled_executable": executable_now == real_execution_enabled,
                # Backward-compatible aliases. In the RC contract, ready means
                # semantic/provider readiness, not real-execution enablement.
                "actions": declared,
                "ready": semantically_ready,
                "not_ready": semantic_not_ready,
                "all_ready": semantically_ready == declared,
            },
            "supported_actions": actions,
            "capability_manager": {
                "manager_version": capability_status["manager_version"],
                "all_resolved": capability_status["summary"]["all_resolved"],
                "all_available": capability_status["summary"]["all_available"],
                "all_healthy": capability_status["summary"]["all_healthy"],
            },
        }

    async def async_resolve_action(self, action_id: str) -> ExecutionActionResolution:
        action_match = self._find_action(action_id)
        contract = get_canonical_action_contract(action_id)
        execution_enabled = contract is not None
        contract_payload = contract.as_dict() if contract is not None else None

        if action_match is None:
            return ExecutionActionResolution(
                action_id=action_id,
                capability_id=None,
                status=ExecutionReadinessStatus.ACTION_NOT_FOUND,
                declared=False,
                resolved=False,
                semantically_ready=False,
                execution_enabled=False,
                executable=False,
                mutating=None,
                confirmation_required=None,
                selected_provider_ids=(),
                capability=None,
                action_contract=None,
                reason="No registered semantic capability declares this action ID.",
            )

        capability_id, action = action_match
        capability = await self._capability_manager.async_get_capability(capability_id)

        if not capability.get("found"):
            return ExecutionActionResolution(
                action_id=action_id,
                capability_id=capability_id,
                status=ExecutionReadinessStatus.CAPABILITY_NOT_FOUND,
                declared=True,
                resolved=False,
                semantically_ready=False,
                execution_enabled=execution_enabled,
                executable=False,
                mutating=action.mutating,
                confirmation_required=action.confirmation_required,
                selected_provider_ids=(),
                capability=capability,
                action_contract=contract_payload,
                reason="Capability Manager did not find the capability.",
            )

        definition = capability["definition"]
        resolution = capability["resolution"]

        if not definition["enabled"]:
            status = ExecutionReadinessStatus.CAPABILITY_DISABLED
            reason = "Semantic capability is intentionally disabled."
            semantic_ready = False
        elif not resolution["resolved"]:
            status = ExecutionReadinessStatus.CAPABILITY_UNRESOLVED
            reason = "Capability provider bindings are unresolved."
            semantic_ready = False
        elif not resolution["available"]:
            status = ExecutionReadinessStatus.CAPABILITY_UNAVAILABLE
            reason = "Capability is resolved but currently unavailable."
            semantic_ready = False
        elif not resolution["healthy"]:
            status = ExecutionReadinessStatus.CAPABILITY_UNHEALTHY
            reason = "Capability is available but currently unhealthy."
            semantic_ready = False
        else:
            semantic_ready = True
            if execution_enabled:
                status = ExecutionReadinessStatus.READY
                reason = (
                    "Action is semantically ready and enabled through the "
                    "canonical real-execution surface."
                )
            else:
                status = ExecutionReadinessStatus.SEMANTIC_READY_ONLY
                reason = (
                    "Action is semantically ready, but canonical real execution "
                    "is not enabled for this action."
                )

        return ExecutionActionResolution(
            action_id=action_id,
            capability_id=capability_id,
            status=status,
            declared=True,
            resolved=resolution["resolved"],
            semantically_ready=semantic_ready,
            execution_enabled=execution_enabled,
            executable=semantic_ready and execution_enabled,
            mutating=action.mutating,
            confirmation_required=action.confirmation_required,
            selected_provider_ids=tuple(resolution["selected_provider_ids"]),
            capability=capability,
            action_contract=contract_payload,
            reason=reason,
        )

    def _find_action(self, action_id: str) -> tuple[str, Any] | None:
        matches: list[tuple[str, Any]] = []
        for definition in self._capability_registry.definitions():
            for action in definition.actions:
                if action.action_id == action_id:
                    matches.append((definition.capability_id, action))
        if not matches:
            return None
        return sorted(matches, key=lambda item: item[0])[0]

    def _action_catalog(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for definition in self._capability_registry.definitions():
            for action in definition.actions:
                contract = get_canonical_action_contract(action.action_id)
                items.append({
                    "action_id": action.action_id,
                    "capability_id": definition.capability_id,
                    "name": action.name,
                    "mutating": action.mutating,
                    "confirmation_required": action.confirmation_required,
                    "real_execution_enabled": contract is not None,
                    "action_contract": contract.as_dict() if contract else None,
                })
        return sorted(items, key=lambda item: item["action_id"])
