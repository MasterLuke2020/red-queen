"""Stable public WNHF execution response."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PublicExecutionResult:
    """Stable response returned by the central Execution Manager."""

    api_version: str
    request_id: str
    requested_id: str
    action: str | None
    executor: str | None
    accepted: bool
    status: str
    executed: bool
    reason: str
    transaction: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "api_version": self.api_version,
            "request_id": self.request_id,
            "id": self.requested_id,
            "action": self.action,
            "executor": self.executor,
            "accepted": self.accepted,
            "status": self.status,
            "executed": self.executed,
            "reason": self.reason,
            "transaction": self.transaction,
        }
