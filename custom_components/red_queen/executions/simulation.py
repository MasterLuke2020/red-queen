"""Dry-run multi-step transaction state-machine models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class MultiStepSimulationStatus(StrEnum):
    """Final status of a multi-step simulation."""

    SIMULATED = "simulated"
    NO_ACTION = "no_action"
    REJECTED = "rejected"
    FAILED = "failed"


class MultiStepSimulationStepStatus(StrEnum):
    """Simulated state of one transaction step."""

    WOULD_EXECUTE = "would_execute"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class MultiStepSimulationStep:
    """One simulated result in sequence order."""

    step_id: str
    sequence: int
    object_id: str
    object_name: str
    room_id: str
    status: MultiStepSimulationStepStatus
    progress_percent: float
    operation: str
    capability: dict[str, Any]
    command_entity_id: str
    feedback_before: dict[str, Any]
    command_sent: bool
    executed: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "sequence": self.sequence,
            "object_id": self.object_id,
            "object_name": self.object_name,
            "room_id": self.room_id,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "operation": self.operation,
            "capability": self.capability,
            "command_entity_id": self.command_entity_id,
            "feedback_before": self.feedback_before,
            "command_sent": self.command_sent,
            "executed": self.executed,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class MultiStepSimulation:
    """Immutable dry-run transaction simulation."""

    simulation_id: str
    generated_at: datetime
    finished_at: datetime
    duration_ms: float
    decision_id: str
    plan_id: str
    action: str | None
    target: dict[str, Any]
    context: str
    confirmed: bool
    accepted: bool
    status: MultiStepSimulationStatus
    dry_run: bool
    executed: bool
    eligible_for_commit: bool
    sequence_mode: str
    stop_on_error: bool
    rollback_ready: bool
    total_steps: int
    completed_steps: int
    would_execute_steps: int
    skipped_steps: int
    blocked_steps: int
    progress_percent: float
    reason: str
    errors: tuple[str, ...]
    steps: tuple[MultiStepSimulationStep, ...]
    blueprint: dict[str, Any]
    simulator_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "generated_at": self.generated_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration_ms": self.duration_ms,
            "decision_id": self.decision_id,
            "plan_id": self.plan_id,
            "action": self.action,
            "target": self.target,
            "context": self.context,
            "confirmed": self.confirmed,
            "accepted": self.accepted,
            "status": self.status.value,
            "dry_run": self.dry_run,
            "executed": self.executed,
            "eligible_for_commit": self.eligible_for_commit,
            "transaction": {
                "mode": "multi_step_simulation",
                "sequence_mode": self.sequence_mode,
                "stop_on_error": self.stop_on_error,
                "rollback_ready": self.rollback_ready,
            },
            "summary": {
                "total_steps": self.total_steps,
                "completed_steps": self.completed_steps,
                "would_execute_steps": self.would_execute_steps,
                "skipped_steps": self.skipped_steps,
                "blocked_steps": self.blocked_steps,
                "progress_percent": self.progress_percent,
            },
            "reason": self.reason,
            "errors": list(self.errors),
            "steps": [item.as_dict() for item in self.steps],
            "versions": {
                "simulator": self.simulator_version,
            },
            "blueprint": self.blueprint,
        }
