"""Immutable models for the WNHF Policy Engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class PolicyMode(StrEnum):
    OFF = "off"
    MONITOR = "monitor"
    ENFORCE = "enforce"


class PolicyDecisionValue(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """One simple policy rule."""

    rule_id: str
    contexts: tuple[str, ...]
    decision: PolicyDecisionValue
    priority: int
    reason: str
    requires_capabilities: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.rule_id,
            "contexts": list(self.contexts),
            "decision": self.decision.value,
            "priority": self.priority,
            "reason": self.reason,
            "requires_capabilities": list(self.requires_capabilities),
        }


@dataclass(frozen=True, slots=True)
class Policy:
    """One configurable permission question."""

    policy_id: str
    name: str
    description: str
    default: PolicyDecisionValue
    enabled: bool
    rules: tuple[PolicyRule, ...]
    source_file: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "default": self.default.value,
            "enabled": self.enabled,
            "rules": [rule.as_dict() for rule in self.rules],
            "source_file": self.source_file,
        }


@dataclass(frozen=True, slots=True)
class PolicyRegistry:
    """Loaded policy configuration."""

    mode: PolicyMode = PolicyMode.MONITOR
    policies: tuple[Policy, ...] = ()
    warnings: tuple[str, ...] = ()
    loaded_files: tuple[str, ...] = ()

    def get(self, policy_id: str) -> Policy | None:
        return next(
            (policy for policy in self.policies if policy.policy_id == policy_id),
            None,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "count": len(self.policies),
            "warnings": list(self.warnings),
            "loaded_files": list(self.loaded_files),
            "policies": [policy.as_dict() for policy in self.policies],
        }


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Explainable policy result."""

    policy_id: str
    configured: bool
    mode: PolicyMode
    context: str
    calculated: PolicyDecisionValue
    effective: PolicyDecisionValue
    default_used: bool
    matched_rule_id: str | None
    priority: int | None
    reason: str
    monitor_only: bool
    capability_results: dict[str, bool]

    @property
    def allowed(self) -> bool:
        return self.effective is PolicyDecisionValue.ALLOW

    @property
    def would_allow(self) -> bool:
        return self.calculated is PolicyDecisionValue.ALLOW

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "configured": self.configured,
            "mode": self.mode.value,
            "context": self.context,
            "calculated": self.calculated.value,
            "effective": self.effective.value,
            "allowed": self.allowed,
            "would_allow": self.would_allow,
            "default_used": self.default_used,
            "matched_rule_id": self.matched_rule_id,
            "priority": self.priority,
            "reason": self.reason,
            "monitor_only": self.monitor_only,
            "capability_results": self.capability_results,
        }
