"""Sequential real room execution models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class SequentialRoomState(StrEnum):
    CREATED = "created"
    VALIDATING = "validating"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    NO_ACTION = "no_action"
    REJECTED = "rejected"
    FAILED = "failed"


class SequentialStepState(StrEnum):
    PENDING = "pending"
    VALIDATING = "validating"
    DISPATCHING = "dispatching"
    WAITING_FEEDBACK = "waiting_feedback"
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SequentialRoomTransition:
    sequence: int
    at: datetime
    from_state: str | None
    to_state: SequentialRoomState
    reason: str
    step_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "at": self.at.isoformat(),
            "from_state": self.from_state,
            "to_state": self.to_state.value,
            "reason": self.reason,
            "step_id": self.step_id,
        }


@dataclass(frozen=True, slots=True)
class SequentialStepResult:
    step_id: str
    sequence: int
    object_id: str
    object_name: str
    room_id: str
    state: SequentialStepState
    progress_percent: float
    command_entity_id: str
    capability: dict[str, Any]
    command: dict[str, Any]
    command_sent: bool
    executed: bool
    feedback_confirmed: bool
    feedback_before: dict[str, Any] | None
    feedback_after: dict[str, Any] | None
    feedback_wait_ms: float
    reason: str
    error: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "sequence": self.sequence,
            "object_id": self.object_id,
            "object_name": self.object_name,
            "room_id": self.room_id,
            "state": self.state.value,
            "progress_percent": self.progress_percent,
            "command_entity_id": self.command_entity_id,
            "capability": self.capability,
            "command": self.command,
            "command_sent": self.command_sent,
            "executed": self.executed,
            "feedback_confirmed": self.feedback_confirmed,
            "feedback_before": self.feedback_before,
            "feedback_after": self.feedback_after,
            "feedback_wait_ms": self.feedback_wait_ms,
            "reason": self.reason,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class SequentialRoomResult:
    transaction_id: str
    generated_at: datetime
    finished_at: datetime
    duration_ms: float
    decision_id: str
    plan_id: str
    confirmed: bool
    accepted: bool
    state: SequentialRoomState
    dry_run: bool
    executed: bool
    command_count: int
    total_steps: int
    completed_steps: int
    skipped_steps: int
    failed_steps: int
    progress_percent: float
    failed_step_id: str | None
    reason: str
    error: str | None
    transitions: tuple[SequentialRoomTransition, ...]
    steps: tuple[SequentialStepResult, ...]
    blueprint: dict[str, Any]
    executor_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "generated_at": self.generated_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration_ms": self.duration_ms,
            "decision_id": self.decision_id,
            "plan_id": self.plan_id,
            "confirmed": self.confirmed,
            "accepted": self.accepted,
            "state": self.state.value,
            "dry_run": self.dry_run,
            "executed": self.executed,
            "command_count": self.command_count,
            "summary": {
                "total_steps": self.total_steps,
                "completed_steps": self.completed_steps,
                "skipped_steps": self.skipped_steps,
                "failed_steps": self.failed_steps,
                "progress_percent": self.progress_percent,
                "failed_step_id": self.failed_step_id,
            },
            "reason": self.reason,
            "error": self.error,
            "transitions": [item.as_dict() for item in self.transitions],
            "steps": [item.as_dict() for item in self.steps],
            "blueprint": self.blueprint,
            "versions": {
                "sequential_executor": self.executor_version,
            },
        }
