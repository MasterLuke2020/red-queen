"""House execution result models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class HouseExecutionState(StrEnum):
    CREATED = "created"
    VALIDATING = "validating"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    NO_ACTION = "no_action"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class HouseExecutionTransition:
    sequence: int
    at: datetime
    from_state: str | None
    to_state: HouseExecutionState
    reason: str
    room_id: str | None = None
    step_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "at": self.at.isoformat(),
            "from_state": self.from_state,
            "to_state": self.to_state.value,
            "reason": self.reason,
            "room_id": self.room_id,
            "step_id": self.step_id,
        }


@dataclass(frozen=True, slots=True)
class HouseRoomResult:
    room_id: str
    room_name: str
    sequence: int
    state: str
    total_steps: int
    completed_steps: int
    skipped_steps: int
    failed_steps: int
    command_count: int
    progress_percent: float
    failed_step_id: str | None
    reason: str
    steps: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "sequence": self.sequence,
            "state": self.state,
            "summary": {
                "total_steps": self.total_steps,
                "completed_steps": self.completed_steps,
                "skipped_steps": self.skipped_steps,
                "failed_steps": self.failed_steps,
                "command_count": self.command_count,
                "progress_percent": self.progress_percent,
                "failed_step_id": self.failed_step_id,
            },
            "reason": self.reason,
            "steps": list(self.steps),
        }


@dataclass(frozen=True, slots=True)
class HouseExecutionResult:
    transaction_id: str
    generated_at: datetime
    finished_at: datetime
    duration_ms: float
    decision_id: str
    plan_id: str
    confirmed: bool
    accepted: bool
    state: HouseExecutionState
    dry_run: bool
    executed: bool
    command_count: int
    total_rooms: int
    completed_rooms: int
    failed_rooms: int
    total_steps: int
    completed_steps: int
    skipped_steps: int
    failed_steps: int
    progress_percent: float
    failed_room_id: str | None
    failed_step_id: str | None
    reason: str
    error: str | None
    transitions: tuple[HouseExecutionTransition, ...]
    rooms: tuple[HouseRoomResult, ...]
    blueprint: dict[str, Any]
    executor_version: str
    pipeline_version: str

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
                "total_rooms": self.total_rooms,
                "completed_rooms": self.completed_rooms,
                "failed_rooms": self.failed_rooms,
                "total_steps": self.total_steps,
                "completed_steps": self.completed_steps,
                "skipped_steps": self.skipped_steps,
                "failed_steps": self.failed_steps,
                "progress_percent": self.progress_percent,
                "failed_room_id": self.failed_room_id,
                "failed_step_id": self.failed_step_id,
            },
            "reason": self.reason,
            "error": self.error,
            "transitions": [item.as_dict() for item in self.transitions],
            "rooms": [item.as_dict() for item in self.rooms],
            "blueprint": self.blueprint,
            "versions": {
                "house_executor": self.executor_version,
                "execution_pipeline": self.pipeline_version,
            },
        }
