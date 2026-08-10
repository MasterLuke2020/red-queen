"""Pure policy evaluation."""

from __future__ import annotations

from .model import (
    PolicyDecision,
    PolicyDecisionValue,
    PolicyMode,
    PolicyRegistry,
)


class PolicyEvaluator:
    """Evaluate permission policies without executing actions."""

    @staticmethod
    def evaluate(
        registry: PolicyRegistry,
        policy_id: str,
        context: str,
        capabilities: dict[str, dict],
    ) -> PolicyDecision:
        policy = registry.get(policy_id)

        # Missing policies intentionally fail open for easy introduction.
        if policy is None or not policy.enabled:
            calculated = PolicyDecisionValue.ALLOW
            reason = (
                "Policy is not configured; framework fallback is allow."
                if policy is None
                else "Policy is disabled; framework fallback is allow."
            )
            matched_rule = None
            priority = None
            default_used = True
            capability_results: dict[str, bool] = {}
            configured = policy is not None
        else:
            candidates = []
            for rule in policy.rules:
                if context not in rule.contexts and "*" not in rule.contexts:
                    continue

                capability_results = {
                    capability_id: bool(
                        capabilities.get(capability_id, {}).get("available", False)
                    )
                    for capability_id in rule.requires_capabilities
                }
                if not all(capability_results.values()):
                    continue
                candidates.append((rule, capability_results))

            candidates.sort(
                key=lambda item: (-item[0].priority, item[0].rule_id)
            )

            if candidates:
                matched_rule, capability_results = candidates[0]
                calculated = matched_rule.decision
                reason = matched_rule.reason
                priority = matched_rule.priority
                default_used = False
            else:
                matched_rule = None
                capability_results = {}
                calculated = policy.default
                reason = f"Policy default '{policy.default.value}' used."
                priority = None
                default_used = True
            configured = True

        if registry.mode is PolicyMode.ENFORCE:
            effective = calculated
            monitor_only = False
        else:
            effective = PolicyDecisionValue.ALLOW
            monitor_only = registry.mode is PolicyMode.MONITOR

        if registry.mode is PolicyMode.OFF:
            reason = "Policy Engine is off; action is allowed."

        return PolicyDecision(
            policy_id=policy_id,
            configured=configured,
            mode=registry.mode,
            context=context,
            calculated=calculated,
            effective=effective,
            default_used=default_used,
            matched_rule_id=(
                matched_rule.rule_id if matched_rule is not None else None
            ),
            priority=priority,
            reason=reason,
            monitor_only=monitor_only,
            capability_results=capability_results,
        )
