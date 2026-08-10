"""Immutable Decision Engine models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DecisionStatus(StrEnum):
    """Normalized lifecycle state of one evaluated decision."""

    RECOMMENDED = "recommended"
    NOT_RECOMMENDED = "not_recommended"
    BLOCKED = "blocked"
    DISABLED = "disabled"
    UNCONFIGURED = "unconfigured"


@dataclass(frozen=True, slots=True)
class DecisionRule:
    """One context-sensitive recommendation rule."""

    rule_id: str
    contexts: tuple[str, ...]
    recommend: bool
    priority: int
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.rule_id,
            "contexts": list(self.contexts),
            "recommend": self.recommend,
            "priority": self.priority,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class DecisionDefinition:
    """One semantic decision definition."""

    decision_id: str
    name: str
    description: str
    enabled: bool
    default_recommend: bool
    policy_id: str | None
    action: str
    target: dict[str, Any]
    rules: tuple[DecisionRule, ...]
    source_file: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.decision_id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "default_recommend": self.default_recommend,
            "policy_id": self.policy_id,
            "action": self.action,
            "target": self.target,
            "rules": [rule.as_dict() for rule in self.rules],
            "source_file": self.source_file,
        }


@dataclass(frozen=True, slots=True)
class DecisionRegistry:
    """Loaded, optional decision configuration."""

    decisions: tuple[DecisionDefinition, ...] = ()
    warnings: tuple[str, ...] = ()
    loaded_files: tuple[str, ...] = ()

    def get(self, decision_id: str) -> DecisionDefinition | None:
        return next(
            (
                item
                for item in self.decisions
                if item.decision_id == decision_id
            ),
            None,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "count": len(self.decisions),
            "warnings": list(self.warnings),
            "loaded_files": list(self.loaded_files),
            "decisions": [item.as_dict() for item in self.decisions],
        }


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """Explainable, read-only decision output."""

    decision_id: str
    configured: bool
    enabled: bool
    context: str
    status: DecisionStatus
    recommended: bool
    policy_allowed: bool
    executable: bool
    action: str | None
    target: dict[str, Any]
    matched_rule_id: str | None
    priority: int | None
    reason: str
    policy: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "configured": self.configured,
            "enabled": self.enabled,
            "context": self.context,
            "status": self.status.value,
            "recommended": self.recommended,
            "policy_allowed": self.policy_allowed,
            "executable": self.executable,
            "action": self.action,
            "target": self.target,
            "matched_rule_id": self.matched_rule_id,
            "priority": self.priority,
            "reason": self.reason,
            "policy": self.policy,
            "read_only": True,
        }
