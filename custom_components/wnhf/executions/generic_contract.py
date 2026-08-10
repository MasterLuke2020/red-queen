"""Generic semantic execution request and plan contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class GenericExecutionState(StrEnum):
    """Stable public generic execution states."""

    CREATED = "created"
    REJECTED = "rejected"
    DRY_RUN_READY = "dry_run_ready"


class GenericExecutionResultCode(StrEnum):
    """Stable result codes for read-only generic execution planning."""

    DRY_RUN_READY = "EXE-100"
    ACTION_NOT_FOUND = "EXE-200"
    ACTION_NOT_READY = "EXE-201"
    CONFIRMATION_REQUIRED = "EXE-202"
    INVALID_TARGET = "EXE-203"
    INVALID_PARAMETERS = "EXE-204"


@dataclass(frozen=True, slots=True)
class GenericExecutionRequest:
    """Immutable generic semantic execution request."""

    action_id: str
    target: dict[str, Any]
    parameters: dict[str, Any]
    confirmed: bool
    dry_run: bool = True
    request_id: str = field(
        default_factory=lambda: (
            "exr_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ_")
            + uuid4().hex[:8]
        )
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "action_id": self.action_id,
            "target": self.target,
            "parameters": self.parameters,
            "confirmed": self.confirmed,
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True, slots=True)
class GenericExecutionPlan:
    """Immutable dry-run execution plan."""

    plan_id: str
    request_id: str
    action_id: str
    capability_id: str
    mutating: bool
    confirmation_required: bool
    confirmed: bool
    target: dict[str, Any]
    parameters: dict[str, Any]
    selected_provider_ids: tuple[str, ...]
    provider_bindings: tuple[dict[str, Any], ...]
    executable: bool
    execution_enabled: bool
    dry_run: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "request_id": self.request_id,
            "action_id": self.action_id,
            "capability_id": self.capability_id,
            "mutating": self.mutating,
            "confirmation_required": self.confirmation_required,
            "confirmed": self.confirmed,
            "target": self.target,
            "parameters": self.parameters,
            "selected_provider_ids": list(self.selected_provider_ids),
            "provider_bindings": list(self.provider_bindings),
            "executable": self.executable,
            "execution_enabled": self.execution_enabled,
            "dry_run": self.dry_run,
        }



@dataclass(frozen=True, slots=True)
class GenericPromotedExecutionPlan:
    """Execution-enabled plan promoted from a validated dry-run plan."""

    plan_id: str
    validation_plan_id: str
    request_id: str
    action_id: str
    capability_id: str
    mutating: bool
    confirmation_required: bool
    confirmed: bool
    target: dict[str, Any]
    parameters: dict[str, Any]
    selected_provider_ids: tuple[str, ...]
    provider_bindings: tuple[dict[str, Any], ...]
    executable: bool
    execution_enabled: bool = True
    dry_run: bool = False
    planning_mode: str = "execution"
    promoted_from_validation: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "validation_plan_id": self.validation_plan_id,
            "request_id": self.request_id,
            "action_id": self.action_id,
            "capability_id": self.capability_id,
            "mutating": self.mutating,
            "confirmation_required": self.confirmation_required,
            "confirmed": self.confirmed,
            "target": self.target,
            "parameters": self.parameters,
            "selected_provider_ids": list(self.selected_provider_ids),
            "provider_bindings": list(self.provider_bindings),
            "executable": self.executable,
            "execution_enabled": self.execution_enabled,
            "dry_run": self.dry_run,
            "planning_mode": self.planning_mode,
            "promoted_from_validation": self.promoted_from_validation,
        }


@dataclass(frozen=True, slots=True)
class GenericExecutionDryRunResult:
    """Complete generic dry-run result contract."""

    api_version: str
    execution_contract: str
    generated_at: str
    state: GenericExecutionState
    result_code: GenericExecutionResultCode
    accepted: bool
    executable: bool
    execution_enabled: bool
    executed: bool
    command_sent: bool
    request: GenericExecutionRequest
    plan: GenericExecutionPlan | None
    action_resolution: dict[str, Any]
    reason: str
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "api_version": self.api_version,
            "execution_contract": self.execution_contract,
            "generated_at": self.generated_at,
            "state": self.state.value,
            "result_code": {
                "code": self.result_code.value,
                "key": self.result_code.name.lower(),
            },
            "accepted": self.accepted,
            "executable": self.executable,
            "execution_enabled": self.execution_enabled,
            "executed": self.executed,
            "command_sent": self.command_sent,
            "request": self.request.as_dict(),
            "plan": self.plan.as_dict() if self.plan else None,
            "action_resolution": self.action_resolution,
            "reason": self.reason,
            "errors": list(self.errors),
        }


def new_plan_id() -> str:
    """Create one opaque plan ID."""
    return (
        "exp_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ_")
        + uuid4().hex[:8]
    )



def new_execution_plan_id() -> str:
    """Create one opaque promoted execution plan ID."""
    return (
        "xpl_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ_")
        + uuid4().hex[:8]
    )


def promote_execution_plan(
    validation_plan: GenericExecutionPlan,
) -> GenericPromotedExecutionPlan:
    """Promote one validated dry-run plan into an execution-enabled plan."""
    if not validation_plan.executable:
        raise ValueError("Only executable validation plans may be promoted.")
    if not validation_plan.dry_run:
        raise ValueError("Validation plan must originate from dry-run planning.")
    if validation_plan.execution_enabled:
        raise ValueError("Validation plan is already execution-enabled.")

    return GenericPromotedExecutionPlan(
        plan_id=new_execution_plan_id(),
        validation_plan_id=validation_plan.plan_id,
        request_id=validation_plan.request_id,
        action_id=validation_plan.action_id,
        capability_id=validation_plan.capability_id,
        mutating=validation_plan.mutating,
        confirmation_required=validation_plan.confirmation_required,
        confirmed=validation_plan.confirmed,
        target=dict(validation_plan.target),
        parameters=dict(validation_plan.parameters),
        selected_provider_ids=tuple(
            validation_plan.selected_provider_ids
        ),
        provider_bindings=tuple(
            dict(binding)
            for binding in validation_plan.provider_bindings
        ),
        executable=True,
    )
