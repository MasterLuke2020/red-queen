"""Pure, explainable evaluation of WNHF rules."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .model import (
    ConditionEvaluation,
    Rule,
    RuleCondition,
    RuleEvaluation,
    RuleRegistry,
    RuleSnapshot,
)


_MISSING = object()


class RuleEvaluator:
    """Evaluate declarative rules against a flat fact dictionary."""

    @staticmethod
    def _compare(
        condition: RuleCondition,
        actual: Any,
        fact_found: bool,
    ) -> bool:
        operator = condition.operator
        expected = condition.value

        if operator == "exists":
            return fact_found
        if operator == "not_exists":
            return not fact_found
        if not fact_found:
            return False
        if operator == "truthy":
            return bool(actual)
        if operator == "falsy":
            return not bool(actual)
        if operator == "eq":
            return actual == expected
        if operator == "ne":
            return actual != expected
        if operator == "gt":
            return actual > expected
        if operator == "gte":
            return actual >= expected
        if operator == "lt":
            return actual < expected
        if operator == "lte":
            return actual <= expected
        if operator == "in":
            return actual in expected
        if operator == "not_in":
            return actual not in expected
        if operator == "contains":
            return expected in actual
        raise ValueError(f"Unsupported rule operator: {operator}")

    @classmethod
    def evaluate_condition(
        cls,
        condition: RuleCondition,
        facts: dict[str, Any],
    ) -> ConditionEvaluation:
        actual = facts.get(condition.fact, _MISSING)
        fact_found = actual is not _MISSING
        public_actual = actual if fact_found else None

        try:
            matched = cls._compare(condition, actual, fact_found)
            explanation = (
                f"{condition.fact}: actual={public_actual!r}, "
                f"operator={condition.operator}, "
                f"expected={condition.value!r} -> "
                f"{'matched' if matched else 'not matched'}"
            )
        except (TypeError, ValueError) as err:
            matched = False
            explanation = (
                f"{condition.fact}: comparison failed "
                f"({type(err).__name__}: {err})"
            )

        return ConditionEvaluation(
            fact=condition.fact,
            operator=condition.operator,
            expected=condition.value,
            actual=public_actual,
            fact_found=fact_found,
            matched=matched,
            explanation=explanation,
        )

    @classmethod
    def evaluate_rule(
        cls,
        rule: Rule,
        facts: dict[str, Any],
    ) -> RuleEvaluation:
        conditions = tuple(
            cls.evaluate_condition(condition, facts)
            for condition in rule.conditions
        )
        return RuleEvaluation(
            rule=rule,
            matched=rule.enabled and all(
                condition.matched for condition in conditions
            ),
            conditions=conditions,
        )

    @classmethod
    def evaluate(
        cls,
        registry: RuleRegistry,
        facts: dict[str, Any],
    ) -> RuleSnapshot:
        evaluations = tuple(
            cls.evaluate_rule(rule, facts)
            for rule in registry.enabled_rules
        )
        matches = tuple(
            sorted(
                (item for item in evaluations if item.matched),
                key=lambda item: (
                    -item.rule.priority,
                    -item.rule.confidence,
                    item.rule.rule_id,
                ),
            )
        )
        winner = matches[0] if matches else None

        if registry.warnings:
            status = "degraded"
        elif not registry.enabled_rules:
            status = "empty"
        elif winner is None:
            status = "no_match"
        else:
            status = "matched"

        return RuleSnapshot(
            generated_at=datetime.now(UTC),
            status=status,
            facts=dict(facts),
            evaluations=evaluations,
            matches=matches,
            winner=winner,
            registry_warnings=registry.warnings,
        )
