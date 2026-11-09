"""Real single-step generic executor models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from .access_codes import AccessResultCatalog, AccessResultCode


PUBLIC_ACCESS_EXECUTION_API_CONTRACT = "1.0"
REAL_STEP_RESULT_CONTRACT = "2.1-multi-effect"


class RealStepState(StrEnum):
    """State of one tightly constrained real-step transaction."""

    CREATED = "created"
    VALIDATING = "validating"
    READY = "ready"
    DISPATCHING = "dispatching"
    WAITING_FEEDBACK = "waiting_feedback"
    OBSERVING_EFFECT = "observing_effect"
    WAITING_TERMINAL_EFFECT = "waiting_terminal_effect"
    SUCCEEDED = "succeeded"
    NO_ACTION = "no_action"
    REJECTED = "rejected"
    FAILED = "failed"


class CommandStatus(StrEnum):
    """Normalized result of the technical command layer."""

    NOT_ATTEMPTED = "not_attempted"
    REJECTED = "rejected"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class EffectStatus(StrEnum):
    """Normalized result of the physical or semantic effect layer."""

    NOT_EXECUTED = "not_executed"
    NOT_REQUIRED = "not_required"
    NOT_OBSERVED = "not_observed"
    CONFIRMED = "confirmed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    """Technical outcome of dispatching one command."""

    status: CommandStatus
    attempted: bool
    dispatched: bool
    completed: bool
    domain: str | None = None
    service: str | None = None
    entity_id: str | None = None
    message: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "status": self.status.value,
            "attempted": self.attempted,
            "dispatched": self.dispatched,
            "completed": self.completed,
            "domain": self.domain,
            "service": self.service,
            "entity_id": self.entity_id,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class EffectOutcome:
    """Observed physical or semantic effect of one command."""

    status: EffectStatus
    required: bool
    expected: str | None
    observed: str | None
    confirmed: bool
    wait_ms: float
    message: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "status": self.status.value,
            "required": self.required,
            "expected": self.expected,
            "observed": self.observed,
            "confirmed": self.confirmed,
            "wait_ms": self.wait_ms,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class RealStepTransition:
    """One state transition in a real-step transaction."""

    sequence: int
    at: datetime
    from_state: str | None
    to_state: RealStepState
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "at": self.at.isoformat(),
            "from_state": self.from_state,
            "to_state": self.to_state.value,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class RealStepResult:
    """Immutable audit result of one real-step attempt.

    ``command_outcome`` and ``effect_outcome`` are the canonical execution
    contract. The legacy booleans remain available for API compatibility.
    """

    execution_id: str
    generated_at: datetime
    finished_at: datetime
    duration_ms: float
    decision_id: str
    plan_id: str
    confirmed: bool
    accepted: bool
    state: RealStepState
    dry_run: bool
    executed: bool
    command_sent: bool
    feedback_confirmed: bool
    object_id: str | None
    step_id: str | None
    capability: dict[str, Any] | None
    command: dict[str, Any] | None
    feedback_before: dict[str, Any] | None
    feedback_after: dict[str, Any] | None
    feedback_wait_ms: float
    reason: str
    error: str | None
    transitions: tuple[RealStepTransition, ...]
    blueprint: dict[str, Any]
    executor_version: str
    command_outcome: CommandOutcome | None = None
    effect_outcome: EffectOutcome | None = None
    transition_effect: EffectOutcome | None = None
    terminal_effect: EffectOutcome | None = None
    result_code: AccessResultCode | None = None

    def _derived_command_outcome(self) -> CommandOutcome:
        """Derive the new command contract from legacy fields."""
        command = self.command or {}

        if self.command_sent:
            status = (
                CommandStatus.SUCCEEDED
                if self.error is None
                else CommandStatus.FAILED
            )
            return CommandOutcome(
                status=status,
                attempted=True,
                dispatched=True,
                completed=self.error is None,
                domain=command.get("domain"),
                service=command.get("service"),
                entity_id=command.get("entity_id"),
                message=(
                    "Command dispatched successfully."
                    if self.error is None
                    else self.error
                ),
            )

        if self.state == RealStepState.REJECTED:
            return CommandOutcome(
                status=CommandStatus.REJECTED,
                attempted=False,
                dispatched=False,
                completed=False,
                domain=command.get("domain"),
                service=command.get("service"),
                entity_id=command.get("entity_id"),
                message=self.reason,
            )

        return CommandOutcome(
            status=CommandStatus.NOT_ATTEMPTED,
            attempted=False,
            dispatched=False,
            completed=False,
            domain=command.get("domain"),
            service=command.get("service"),
            entity_id=command.get("entity_id"),
            message=self.reason,
        )

    def _derived_effect_outcome(self) -> EffectOutcome:
        """Derive the new effect contract from legacy fields."""
        feedback_required = bool(
            (self.capability or {}).get("feedback", {}).get("required")
        )

        if not self.command_sent:
            return EffectOutcome(
                status=EffectStatus.NOT_EXECUTED,
                required=feedback_required,
                expected=None,
                observed=None,
                confirmed=self.feedback_confirmed,
                wait_ms=self.feedback_wait_ms,
                message=self.reason,
            )

        if not feedback_required:
            return EffectOutcome(
                status=EffectStatus.NOT_REQUIRED,
                required=False,
                expected=None,
                observed=None,
                confirmed=False,
                wait_ms=self.feedback_wait_ms,
                message="No effect confirmation is required.",
            )

        if self.feedback_confirmed:
            return EffectOutcome(
                status=EffectStatus.CONFIRMED,
                required=True,
                expected=None,
                observed=None,
                confirmed=True,
                wait_ms=self.feedback_wait_ms,
                message="Required effect feedback was confirmed.",
            )

        return EffectOutcome(
            status=EffectStatus.FAILED,
            required=True,
            expected=None,
            observed=None,
            confirmed=False,
            wait_ms=self.feedback_wait_ms,
            message="Required effect feedback was not confirmed.",
        )

    def _derived_result_code(self) -> AccessResultCode:
        """Derive a conservative result code for legacy executors."""
        if self.state == RealStepState.SUCCEEDED:
            if (
                self.effect_outcome is not None
                and self.effect_outcome.status == EffectStatus.NOT_OBSERVED
            ):
                return AccessResultCatalog.OPTIONAL_EFFECT_NOT_OBSERVED
            return AccessResultCatalog.SUCCEEDED

        if self.state == RealStepState.NO_ACTION:
            return AccessResultCatalog.ALREADY_SATISFIED

        if self.state == RealStepState.REJECTED:
            return AccessResultCatalog.CAPABILITY_UNQUALIFIED

        if self.state == RealStepState.FAILED:
            return (
                AccessResultCatalog.EXECUTOR_EXCEPTION
                if self.error
                else AccessResultCatalog.REQUIRED_EFFECT_TIMEOUT
            )

        return AccessResultCatalog.EXECUTOR_EXCEPTION

    def _capability_snapshot(self) -> dict[str, Any] | None:
        """Return the immutable capability view used for this execution."""
        if self.capability is None:
            return None

        provider_id = self.capability.get("provider_id")
        confirmation_policy = self.capability.get("confirmation_policy")
        command = self.capability.get("command") or {}
        feedback = self.capability.get("feedback") or {}

        return {
            "capability_id": self.capability.get("capability_id"),
            "object_id": self.capability.get("object_id"),
            "provider": {
                "id": provider_id,
                "strategy": self.capability.get("strategy"),
            },
            "supported": self.capability.get("supported"),
            "available": self.capability.get("available"),
            "healthy": self.capability.get("healthy"),
            "confirmation_policy": confirmation_policy,
            "command": {
                "domain": command.get("domain"),
                "service": command.get("service"),
                "entity_id": command.get("entity_id"),
            },
            "feedback": {
                "required": feedback.get("required"),
                "entity_ids": list(feedback.get("entity_ids") or []),
            },
            "idempotency": self.capability.get("idempotency"),
            "rollback_supported": self.capability.get(
                "rollback_supported"
            ),
        }

    def as_dict(self) -> dict[str, Any]:
        command_outcome = (
            self.command_outcome or self._derived_command_outcome()
        )
        effect_outcome = (
            self.effect_outcome or self._derived_effect_outcome()
        )

        capability_snapshot = self._capability_snapshot()
        result_code = self.result_code or self._derived_result_code()

        return {
            "api_contract": PUBLIC_ACCESS_EXECUTION_API_CONTRACT,
            "result_code": result_code.as_dict(),
            "error_code": (
                result_code.code if result_code.is_error else None
            ),
            "execution_id": self.execution_id,
            "generated_at": self.generated_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration_ms": self.duration_ms,
            "decision_id": self.decision_id,
            "plan_id": self.plan_id,
            "confirmed": self.confirmed,
            "accepted": self.accepted,
            "state": self.state.value,
            "dry_run": self.dry_run,

            # Legacy compatibility fields
            "executed": self.executed,
            "command_sent": self.command_sent,
            "feedback_confirmed": self.feedback_confirmed,

            # Canonical command/effect contract
            "command_outcome": command_outcome.as_dict(),
            "effect_outcome": effect_outcome.as_dict(),
            "transition_effect": (
                self.transition_effect.as_dict()
                if self.transition_effect is not None
                else None
            ),
            "terminal_effect": (
                self.terminal_effect.as_dict()
                if self.terminal_effect is not None
                else None
            ),

            "object_id": self.object_id,
            "step_id": self.step_id,

            # Canonical immutable capability view.
            "capability_snapshot": capability_snapshot,

            # Legacy-compatible detailed fields.
            "capability": self.capability,
            "command": self.command,
            "feedback_before": self.feedback_before,
            "feedback_after": self.feedback_after,
            "feedback_wait_ms": self.feedback_wait_ms,
            "reason": self.reason,
            "error": self.error,
            "transitions": [item.as_dict() for item in self.transitions],
            "blueprint": self.blueprint,
            "versions": {
                "api_contract": PUBLIC_ACCESS_EXECUTION_API_CONTRACT,
                "result_contract": REAL_STEP_RESULT_CONTRACT,
                "result_catalog": AccessResultCatalog.VERSION,
                "real_step_executor": self.executor_version,
            },
        }
