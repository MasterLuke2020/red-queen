"""Canonical semantic execution dry-run planner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .action_contracts import get_canonical_action_contract
from .generic_contract import (
    GenericExecutionDryRunResult,
    GenericExecutionPlan,
    GenericExecutionRequest,
    GenericExecutionResultCode,
    GenericExecutionState,
    new_plan_id,
)


class GenericExecutionPlanner:
    """Validate and plan canonical real-execution requests without dispatch."""

    API_VERSION = "1.1"
    CONTRACT_VERSION = "1.9-rc8"

    def __init__(self, execution_manager: Any, provider_registry: Any) -> None:
        self._execution_manager = execution_manager
        self._provider_registry = provider_registry

    async def async_dry_run(
        self,
        *,
        action_id: str,
        target: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        confirmed: bool = False,
    ) -> GenericExecutionDryRunResult:
        """Validate one canonical execution request without dispatch."""
        request = GenericExecutionRequest(
            action_id=action_id,
            target=dict(target or {}),
            parameters=dict(parameters or {}),
            confirmed=bool(confirmed),
            dry_run=True,
        )

        resolution_obj = await self._execution_manager.async_resolve_action(action_id)
        resolution = resolution_obj.as_dict()

        if not resolution_obj.declared:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.ACTION_NOT_FOUND,
                reason=resolution["reason"],
            )

        if not resolution_obj.semantically_ready or not resolution_obj.execution_enabled:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.ACTION_NOT_READY,
                reason=resolution["reason"],
            )

        action_contract = get_canonical_action_contract(action_id)
        if action_contract is None:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.ACTION_NOT_READY,
                reason="No canonical real-execution contract exists for this action.",
            )

        target_errors = action_contract.validate_target(request.target)
        if target_errors:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.INVALID_TARGET,
                reason="Execution target violates the canonical action contract.",
                errors=target_errors,
            )

        parameter_errors = action_contract.validate_parameters(request.parameters)
        if parameter_errors:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.INVALID_PARAMETERS,
                reason="Execution parameters violate the canonical action contract.",
                errors=parameter_errors,
            )

        confirmation_required = bool(resolution_obj.confirmation_required)
        if confirmation_required and not request.confirmed:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.CONFIRMATION_REQUIRED,
                reason=(
                    "Explicit confirmation is required before this semantic "
                    "action may be dispatched."
                ),
            )

        provider_ids = tuple(resolution_obj.selected_provider_ids)
        if len(provider_ids) != 1:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.ACTION_NOT_READY,
                reason="Canonical execution currently requires exactly one selected provider.",
            )

        provider = self._provider_registry.get(provider_ids[0])
        if provider is None:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.ACTION_NOT_READY,
                reason="The selected provider is no longer registered.",
            )

        provider_validation = await provider.async_validate_execution(
            action_id=action_id,
            target=request.target,
            parameters=request.parameters,
            confirmed=request.confirmed,
        )
        resolution["provider_validation"] = provider_validation.as_dict()
        if not provider_validation.valid:
            return self._reject(
                request=request,
                resolution=resolution,
                code=GenericExecutionResultCode.INVALID_TARGET,
                reason=provider_validation.reason,
                errors=provider_validation.errors,
            )

        capability_payload = resolution.get("capability") or {}
        capability_resolution = capability_payload.get("resolution") or {}
        provider_bindings = tuple(capability_resolution.get("provider_bindings", []))

        plan = GenericExecutionPlan(
            plan_id=new_plan_id(),
            request_id=request.request_id,
            action_id=request.action_id,
            capability_id=str(resolution_obj.capability_id),
            mutating=bool(resolution_obj.mutating),
            confirmation_required=confirmation_required,
            confirmed=request.confirmed,
            target=request.target,
            parameters=request.parameters,
            selected_provider_ids=provider_ids,
            provider_bindings=provider_bindings,
            executable=True,
            # False is intentional: this is the immutable validation plan.
            # promote_execution_plan() is the only path that enables dispatch.
            execution_enabled=False,
            dry_run=True,
        )

        return GenericExecutionDryRunResult(
            api_version=self.API_VERSION,
            execution_contract=self.CONTRACT_VERSION,
            generated_at=datetime.now(UTC).isoformat(),
            state=GenericExecutionState.DRY_RUN_READY,
            result_code=GenericExecutionResultCode.DRY_RUN_READY,
            accepted=True,
            executable=True,
            execution_enabled=False,
            executed=False,
            command_sent=False,
            request=request,
            plan=plan,
            action_resolution=resolution,
            reason=(
                "Canonical execution request, target and provider preflight are "
                "valid. No hardware command was dispatched."
            ),
            errors=(),
        )

    def _reject(
        self,
        *,
        request: GenericExecutionRequest,
        resolution: dict[str, Any],
        code: GenericExecutionResultCode,
        reason: str,
        errors: tuple[str, ...] = (),
    ) -> GenericExecutionDryRunResult:
        return GenericExecutionDryRunResult(
            api_version=self.API_VERSION,
            execution_contract=self.CONTRACT_VERSION,
            generated_at=datetime.now(UTC).isoformat(),
            state=GenericExecutionState.REJECTED,
            result_code=code,
            accepted=False,
            executable=False,
            execution_enabled=False,
            executed=False,
            command_sent=False,
            request=request,
            plan=None,
            action_resolution=resolution,
            reason=reason,
            errors=errors,
        )
