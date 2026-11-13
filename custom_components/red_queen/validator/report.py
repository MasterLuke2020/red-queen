"""Serializable WNHF validation result objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One validator finding."""

    severity: Severity
    code: str
    message: str
    object_id: str | None = None
    entity_id: str | None = None
    domain: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "object_id": self.object_id,
            "entity_id": self.entity_id,
            "domain": self.domain,
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Complete validation result."""

    generated_at: datetime
    duration_ms: float
    summary: dict[str, int]
    checks: dict[str, str]
    issues: tuple[ValidationIssue, ...]

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(item for item in self.issues if item.severity == "error")

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(item for item in self.issues if item.severity == "warning")

    @property
    def info(self) -> tuple[ValidationIssue, ...]:
        return tuple(item for item in self.issues if item.severity == "info")

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def status(self) -> str:
        if self.errors:
            return "error"
        if self.warnings:
            return "warning"
        return "healthy"

    @property
    def quality_score(self) -> int:
        """Calculate a transparent quality score from validation findings."""
        score = 100
        score -= min(80, len(self.errors) * 15)
        score -= min(20, len(self.warnings) * 2)
        return max(0, score)

    def as_dict(self) -> dict[str, Any]:
        """Return the complete report as a service response."""
        return {
            "status": self.status,
            "valid": self.valid,
            "quality_score": self.quality_score,
            "generated_at": self.generated_at.isoformat(),
            "duration_ms": self.duration_ms,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "summary": self.summary,
            "checks": self.checks,
            "errors": [item.as_dict() for item in self.errors],
            "warnings": [item.as_dict() for item in self.warnings],
            "info": [item.as_dict() for item in self.info],
        }
