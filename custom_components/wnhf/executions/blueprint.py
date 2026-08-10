"""Multi-step dry-run transaction blueprint models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class MultiStepBlueprintStep:
    """One deterministic step in a future multi-object transaction."""

    step_id: str
    sequence: int
    object_id: str
    object_name: str
    room_id: str
    operation: str
    command_entity_id: str
    feedback_before: dict[str, Any]
    capability: dict[str, Any]
    rollback_supported: bool
    rollback_operation: str | None
    executable_in_current_stage: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "sequence": self.sequence,
            "object_id": self.object_id,
            "object_name": self.object_name,
            "room_id": self.room_id,
            "operation": self.operation,
            "command_entity_id": self.command_entity_id,
            "feedback_before": self.feedback_before,
            "capability": self.capability,
            "rollback": {
                "supported": self.rollback_supported,
                "operation": self.rollback_operation,
            },
            "executable_in_current_stage": self.executable_in_current_stage,
        }


@dataclass(frozen=True, slots=True)
class MultiStepBlueprint:
    """Read-only transaction blueprint for one Decision."""

    generated_at: datetime
    plan_id: str
    decision_id: str
    action: str | None
    target: dict[str, Any]
    context: str
    status: str
    accepted_for_planning: bool
    eligible_for_commit: bool
    dry_run: bool
    executed: bool
    transaction_mode: str
    sequence_mode: str
    stop_on_error: bool
    rollback_ready: bool
    planner_version: str
    optimizer_version: str
    total_objects: int
    active_objects: int
    skipped_objects: int
    invalid_objects: int
    steps: tuple[MultiStepBlueprintStep, ...]
    reasons: tuple[str, ...]
    validation_errors: tuple[str, ...]
    decision: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "plan_id": self.plan_id,
            "decision_id": self.decision_id,
            "action": self.action,
            "target": self.target,
            "context": self.context,
            "status": self.status,
            "accepted_for_planning": self.accepted_for_planning,
            "eligible_for_commit": self.eligible_for_commit,
            "dry_run": self.dry_run,
            "executed": self.executed,
            "transaction": {
                "mode": self.transaction_mode,
                "sequence_mode": self.sequence_mode,
                "stop_on_error": self.stop_on_error,
                "rollback_ready": self.rollback_ready,
            },
            "versions": {
                "planner": self.planner_version,
                "optimizer": self.optimizer_version,
            },
            "summary": {
                "total_objects": self.total_objects,
                "active_objects": self.active_objects,
                "planned_steps": len(self.steps),
                "skipped_objects": self.skipped_objects,
                "invalid_objects": self.invalid_objects,
            },
            "reasons": list(self.reasons),
            "validation_errors": list(self.validation_errors),
            "steps": [item.as_dict() for item in self.steps],
            "decision": self.decision,
        }
