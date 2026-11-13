"""Immutable rule-engine models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class RuleCondition:
    """One declarative comparison against a fact path."""

    fact: str
    operator: str
    value: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "fact": self.fact,
            "operator": self.operator,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class Rule:
    """One versioned declarative WNHF rule."""

    rule_id: str
    name: str
    version: str
    priority: int
    confidence: float
    enabled: bool
    description: str
    author: str
    conditions: tuple[RuleCondition, ...]
    result: dict[str, Any]
    source_file: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.rule_id,
            "name": self.name,
            "version": self.version,
            "priority": self.priority,
            "confidence": self.confidence,
            "enabled": self.enabled,
            "description": self.description,
            "author": self.author,
            "conditions": [item.as_dict() for item in self.conditions],
            "result": self.result,
            "source_file": self.source_file,
        }


@dataclass(frozen=True, slots=True)
class ConditionEvaluation:
    """Explainable outcome of one condition."""

    fact: str
    operator: str
    expected: Any
    actual: Any
    fact_found: bool
    matched: bool
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "fact": self.fact,
            "operator": self.operator,
            "expected": self.expected,
            "actual": self.actual,
            "fact_found": self.fact_found,
            "matched": self.matched,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    """Explainable outcome of one complete rule."""

    rule: Rule
    matched: bool
    conditions: tuple[ConditionEvaluation, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule.as_dict(),
            "matched": self.matched,
            "conditions": [item.as_dict() for item in self.conditions],
        }


@dataclass(frozen=True, slots=True)
class RuleRegistry:
    """Loaded rule collection and non-fatal loader findings."""

    rules: tuple[Rule, ...] = ()
    warnings: tuple[str, ...] = ()
    loaded_files: tuple[str, ...] = ()

    @property
    def enabled_rules(self) -> tuple[Rule, ...]:
        return tuple(rule for rule in self.rules if rule.enabled)

    def as_dict(self) -> dict[str, Any]:
        return {
            "count": len(self.rules),
            "enabled_count": len(self.enabled_rules),
            "warnings": list(self.warnings),
            "loaded_files": list(self.loaded_files),
            "rules": [rule.as_dict() for rule in self.rules],
        }


@dataclass(frozen=True, slots=True)
class RuleSnapshot:
    """Complete result of one rule-engine evaluation."""

    generated_at: datetime
    status: str
    facts: dict[str, Any]
    evaluations: tuple[RuleEvaluation, ...]
    matches: tuple[RuleEvaluation, ...]
    winner: RuleEvaluation | None
    registry_warnings: tuple[str, ...] = ()

    @property
    def matched_count(self) -> int:
        return len(self.matches)

    @property
    def winner_state(self) -> str | None:
        if self.winner is None:
            return None
        value = self.winner.rule.result.get("state")
        return str(value) if value is not None else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "status": self.status,
            "rule_count": len(self.evaluations),
            "matched_count": self.matched_count,
            "winner": (
                self.winner.as_dict() if self.winner is not None else None
            ),
            "winner_state": self.winner_state,
            "matches": [item.as_dict() for item in self.matches],
            "evaluations": [item.as_dict() for item in self.evaluations],
            "facts": self.facts,
            "registry_warnings": list(self.registry_warnings),
        }
