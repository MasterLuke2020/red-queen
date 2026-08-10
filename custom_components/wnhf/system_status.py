"""Stable aggregated WNHF system status model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SystemCheck:
    """One runtime-readiness check."""

    check_id: str
    status: str
    required: bool
    message: str
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status,
            "required": self.required,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class SystemStatusSnapshot:
    """Immutable aggregate runtime status."""

    api_version: str
    generated_at: datetime
    framework_version: str
    status: str
    runtime_ready: bool
    health_score: int
    error_count: int
    warning_count: int
    active_transaction_count: int
    queued_transaction_count: int
    summary: dict[str, Any]
    checks: tuple[SystemCheck, ...]
    last_public_execution: dict[str, Any] | None

    @property
    def alpha_ready(self) -> bool:
        """Deprecated internal compatibility alias for pre-WP-4.7.8.5 code."""
        return self.runtime_ready

    def as_dict(self) -> dict[str, Any]:
        return {
            "api_version": self.api_version,
            "generated_at": self.generated_at.isoformat(),
            "framework_version": self.framework_version,
            "status": self.status,
            "runtime_ready": self.runtime_ready,
            "health_score": self.health_score,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "active_transaction_count": self.active_transaction_count,
            "queued_transaction_count": self.queued_transaction_count,
            "summary": self.summary,
            "checks": [item.as_dict() for item in self.checks],
            "last_public_execution": self.last_public_execution,
            "last_canonical_execution": self.last_public_execution,
        }
