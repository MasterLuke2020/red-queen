"""Semantic context state derived from WNHF facts and rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..rules.model import RuleEvaluation, RuleSnapshot


@dataclass(frozen=True, slots=True)
class ContextScores:
    """Transparent normalized scores used as rule facts."""

    activity: int
    attention: int
    security: int
    health: int

    def as_dict(self) -> dict[str, int]:
        return {
            "activity": self.activity,
            "attention": self.attention,
            "security": self.security,
            "health": self.health,
        }


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    """Final semantic interpretation of the current house state."""

    generated_at: datetime
    state: str
    message: str
    confidence: float
    priority: int
    rule_id: str
    rule_name: str
    source: str
    scores: ContextScores
    reasons: tuple[str, ...]
    rule_snapshot: RuleSnapshot

    @property
    def confidence_percent(self) -> int:
        return round(self.confidence * 100)

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "state": self.state,
            "message": self.message,
            "confidence": self.confidence,
            "confidence_percent": self.confidence_percent,
            "priority": self.priority,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "source": self.source,
            "scores": self.scores.as_dict(),
            "reasons": list(self.reasons),
            "matched_count": self.rule_snapshot.matched_count,
            "matches": [
                evaluation.as_dict()
                for evaluation in self.rule_snapshot.matches
            ],
            "winner": (
                self.rule_snapshot.winner.as_dict()
                if self.rule_snapshot.winner is not None
                else None
            ),
            "facts": self.rule_snapshot.facts,
            "registry_warnings": list(
                self.rule_snapshot.registry_warnings
            ),
        }
