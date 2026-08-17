"""Provider-side generic execution contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderExecutionValidationResult:
    """Non-mutating provider validation for one semantic execution request."""

    valid: bool
    reason: str
    errors: tuple[str, ...] = ()
    technical_capability: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "errors": list(self.errors),
            "technical_capability": self.technical_capability,
        }


@dataclass(frozen=True, slots=True)
class ProviderExecutionResult:
    """Normalized result returned by one provider execution hook."""

    status: str
    executed: bool
    command_sent: bool
    feedback_confirmed: bool
    reason: str
    error: str | None = None
    technical_capability: dict[str, Any] | None = None
    feedback_before: dict[str, Any] | None = None
    feedback_after: dict[str, Any] | None = None
    feedback_wait_ms: float = 0.0
    # "effect" proves an observed target effect. "dispatch" proves only that
    # the provider call completed; it does not claim remote delivery/read.
    verification_scope: str = "effect"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "executed": self.executed,
            "command_sent": self.command_sent,
            "feedback_confirmed": self.feedback_confirmed,
            "reason": self.reason,
            "error": self.error,
            "technical_capability": self.technical_capability,
            "feedback_before": self.feedback_before,
            "feedback_after": self.feedback_after,
            "feedback_wait_ms": self.feedback_wait_ms,
            "verification_scope": self.verification_scope,
        }
