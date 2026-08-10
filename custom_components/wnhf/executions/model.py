"""Immutable dry-run execution models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class ExecutionStatus(StrEnum):
    READY = "ready"
    BLOCKED = "blocked"
    NOT_RECOMMENDED = "not_recommended"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ExecutionStep:
    step: int
    object_id: str
    object_name: str
    room_id: str
    operation: str
    command_entity_id: str | None
    currently_active: bool
    valid: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "object_id": self.object_id,
            "object_name": self.object_name,
            "room_id": self.room_id,
            "operation": self.operation,
            "command_entity_id": self.command_entity_id,
            "currently_active": self.currently_active,
            "valid": self.valid,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    generated_at: datetime
    decision_id: str
    status: ExecutionStatus
    dry_run: bool
    executed: bool
    executable: bool
    action: str | None
    target: dict[str, Any]
    context: str
    recommended: bool
    policy_allowed: bool
    decision_status: str
    validation_errors: tuple[str, ...]
    reasons: tuple[str, ...]
    total_object_count: int
    active_object_count: int
    skipped_object_count: int
    invalid_object_count: int
    optimization_ratio: float
    optimizer_version: str
    steps: tuple[ExecutionStep, ...]
    decision: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "decision_id": self.decision_id,
            "status": self.status.value,
            "dry_run": self.dry_run,
            "executed": self.executed,
            "executable": self.executable,
            "action": self.action,
            "target": self.target,
            "context": self.context,
            "recommended": self.recommended,
            "policy_allowed": self.policy_allowed,
            "decision_status": self.decision_status,
            "validation_errors": list(self.validation_errors),
            "reasons": list(self.reasons),
            "summary": {
                "total_objects": self.total_object_count,
                "active_objects": self.active_object_count,
                "planned_steps": len(self.steps),
                "skipped_objects": self.skipped_object_count,
                "invalid_objects": self.invalid_object_count,
            },
            "optimization": {
                "removed_steps": self.skipped_object_count,
                "ratio_percent": self.optimization_ratio,
                "optimizer_version": self.optimizer_version,
            },
            "step_count": len(self.steps),
            "valid_step_count": sum(1 for item in self.steps if item.valid),
            "active_step_count": sum(
                1 for item in self.steps if item.valid and item.currently_active
            ),
            "steps": [item.as_dict() for item in self.steps],
            "decision": self.decision,
        }
