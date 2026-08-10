
"""Controlled active execution transaction models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class ExecutionTransactionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    FAILED = "failed"
    NO_ACTION = "no_action"


@dataclass(frozen=True, slots=True)
class ExecutionTransaction:
    execution_id: str
    decision_id: str
    started_at: datetime
    finished_at: datetime
    duration_ms: float
    status: ExecutionTransactionStatus
    confirmed: bool
    action: str | None
    target: dict[str, Any]
    context: str
    decision_status: str
    recommended: bool
    policy_allowed: bool
    policy_id: str | None
    light_id: str | None
    command_entity_id: str | None
    command_sent: bool
    feedback_before: dict[str, Any] | None
    feedback_after: dict[str, Any] | None
    reason: str
    error: str | None
    planner_version: str
    optimizer_version: str
    executor_version: str

    @property
    def executed(self) -> bool:
        return self.command_sent

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "decision_id": self.decision_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "confirmed": self.confirmed,
            "action": self.action,
            "target": self.target,
            "context": self.context,
            "decision_status": self.decision_status,
            "recommended": self.recommended,
            "policy_allowed": self.policy_allowed,
            "policy_id": self.policy_id,
            "light_id": self.light_id,
            "command_entity_id": self.command_entity_id,
            "command_sent": self.command_sent,
            "executed": self.executed,
            "feedback_before": self.feedback_before,
            "feedback_after": self.feedback_after,
            "reason": self.reason,
            "error": self.error,
            "versions": {
                "planner": self.planner_version,
                "optimizer": self.optimizer_version,
                "executor": self.executor_version,
            },
        }
