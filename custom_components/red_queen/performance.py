"""Performance metrics for WNHF."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import fmean
from typing import Any


@dataclass(slots=True)
class ActionPerformance:
    """Measurements for one WNHF action."""

    action_id: str
    calls: int = 0
    total_ms: float = 0.0
    last_ms: float | None = None
    minimum_ms: float | None = None
    maximum_ms: float | None = None
    last_called_at: datetime | None = None

    def record(self, duration_ms: float, called_at: datetime) -> None:
        """Record one action execution."""
        duration_ms = round(duration_ms, 2)
        self.calls += 1
        self.total_ms += duration_ms
        self.last_ms = duration_ms
        self.minimum_ms = (
            duration_ms
            if self.minimum_ms is None
            else min(self.minimum_ms, duration_ms)
        )
        self.maximum_ms = (
            duration_ms
            if self.maximum_ms is None
            else max(self.maximum_ms, duration_ms)
        )
        self.last_called_at = called_at

    @property
    def average_ms(self) -> float | None:
        """Return mean duration."""
        if self.calls == 0:
            return None
        return round(self.total_ms / self.calls, 2)

    def as_dict(self) -> dict[str, Any]:
        """Return state-attribute-safe data."""
        return {
            "action_id": self.action_id,
            "calls": self.calls,
            "last_ms": self.last_ms,
            "average_ms": self.average_ms,
            "minimum_ms": self.minimum_ms,
            "maximum_ms": self.maximum_ms,
            "last_called_at": (
                self.last_called_at.isoformat()
                if self.last_called_at is not None
                else None
            ),
        }


@dataclass(slots=True)
class PerformanceStore:
    """In-memory WNHF performance store."""

    actions: dict[str, ActionPerformance] = field(default_factory=dict)
    last_action_id: str | None = None

    def record(
        self,
        action_id: str,
        duration_ms: float,
        called_at: datetime,
    ) -> None:
        """Record a measurement."""
        metric = self.actions.setdefault(
            action_id,
            ActionPerformance(action_id=action_id),
        )
        metric.record(duration_ms, called_at)
        self.last_action_id = action_id

    @property
    def last_action(self) -> ActionPerformance | None:
        """Return latest action metric."""
        if self.last_action_id is None:
            return None
        return self.actions.get(self.last_action_id)

    def as_dict(self) -> dict[str, Any]:
        """Return all action metrics."""
        return {
            action_id: metric.as_dict()
            for action_id, metric in self.actions.items()
        }
