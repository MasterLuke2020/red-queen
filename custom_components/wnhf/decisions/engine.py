"""Pure, read-only decision evaluation."""

from __future__ import annotations

from .model import (
    DecisionRegistry,
    DecisionResult,
    DecisionStatus,
)


class DecisionEvaluator:
    """Combine context recommendation and policy permission."""

    @staticmethod
    def evaluate(
        registry: DecisionRegistry,
        decision_id: str,
        context: str,
        policy_result: dict | None,
    ) -> DecisionResult:
        definition = registry.get(decision_id)

        if definition is None:
            return DecisionResult(
                decision_id=decision_id,
                configured=False,
                enabled=False,
                context=context,
                status=DecisionStatus.UNCONFIGURED,
                recommended=False,
                policy_allowed=True,
                executable=False,
                action=None,
                target={},
                matched_rule_id=None,
                priority=None,
                reason="Decision is not configured.",
                policy=policy_result,
            )

        if not definition.enabled:
            return DecisionResult(
                decision_id=decision_id,
                configured=True,
                enabled=False,
                context=context,
                status=DecisionStatus.DISABLED,
                recommended=False,
                policy_allowed=True,
                executable=False,
                action=definition.action,
                target=definition.target,
                matched_rule_id=None,
                priority=None,
                reason="Decision is disabled.",
                policy=policy_result,
            )

        matches = [
            rule
            for rule in definition.rules
            if context in rule.contexts or "*" in rule.contexts
        ]
        matches.sort(key=lambda rule: (-rule.priority, rule.rule_id))

        if matches:
            winner = matches[0]
            recommended = winner.recommend
            reason = winner.reason
            matched_rule_id = winner.rule_id
            priority = winner.priority
        else:
            winner = None
            recommended = definition.default_recommend
            reason = (
                "Decision default recommendation used: "
                f"{definition.default_recommend}."
            )
            matched_rule_id = None
            priority = None

        policy_allowed = (
            bool(policy_result.get("allowed", True))
            if policy_result is not None
            else True
        )

        if recommended and policy_allowed:
            status = DecisionStatus.RECOMMENDED
        elif recommended and not policy_allowed:
            status = DecisionStatus.BLOCKED
        else:
            status = DecisionStatus.NOT_RECOMMENDED

        # Read-only core: execution is deliberately impossible.
        executable = False

        return DecisionResult(
            decision_id=decision_id,
            configured=True,
            enabled=True,
            context=context,
            status=status,
            recommended=recommended,
            policy_allowed=policy_allowed,
            executable=executable,
            action=definition.action,
            target=definition.target,
            matched_rule_id=matched_rule_id,
            priority=priority,
            reason=reason,
            policy=policy_result,
        )
