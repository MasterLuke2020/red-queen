"""Universal WNHF context rules shipped by the framework."""

from __future__ import annotations

from .model import Rule, RuleCondition, RuleRegistry


def core_context_registry() -> RuleRegistry:
    """Return the four universal, versioned WNHF core contexts."""
    return RuleRegistry(
        rules=(
            Rule(
                rule_id="core.context.error",
                name="Error",
                version="1.0",
                priority=100,
                confidence=1.0,
                enabled=True,
                description=(
                    "Framework validation or runtime feedback reports "
                    "a technical error."
                ),
                author="Weidner Net",
                conditions=(
                    RuleCondition(
                        fact="house.has_error",
                        operator="truthy",
                    ),
                ),
                result={
                    "state": "error",
                    "message": "Das Haus meldet einen technischen Fehler.",
                    "source": "core",
                },
                source_file="builtin:core_contexts",
            ),
            Rule(
                rule_id="core.context.attention",
                name="Attention",
                version="1.0",
                priority=80,
                confidence=1.0,
                enabled=True,
                description=(
                    "The building is technically operational but requires "
                    "attention, typically because an opening is open."
                ),
                author="Weidner Net",
                conditions=(
                    RuleCondition(
                        fact="house.has_error",
                        operator="falsy",
                    ),
                    RuleCondition(
                        fact="house.requires_attention",
                        operator="truthy",
                    ),
                ),
                result={
                    "state": "attention",
                    "message": "Das Haus benötigt Aufmerksamkeit.",
                    "source": "core",
                },
                source_file="builtin:core_contexts",
            ),
            Rule(
                rule_id="core.context.activity",
                name="Activity",
                version="1.0",
                priority=20,
                confidence=1.0,
                enabled=True,
                description=(
                    "Visible activity exists while the house is secure "
                    "and technically healthy."
                ),
                author="Weidner Net",
                conditions=(
                    RuleCondition(
                        fact="house.has_error",
                        operator="falsy",
                    ),
                    RuleCondition(
                        fact="house.requires_attention",
                        operator="falsy",
                    ),
                    RuleCondition(
                        fact="house.has_activity",
                        operator="truthy",
                    ),
                ),
                result={
                    "state": "activity",
                    "message": "Im Haus herrscht Aktivität.",
                    "source": "core",
                },
                source_file="builtin:core_contexts",
            ),
            Rule(
                rule_id="core.context.ready",
                name="Ready",
                version="1.0",
                priority=0,
                confidence=1.0,
                enabled=True,
                description=(
                    "The house is technically healthy, secure and quiet."
                ),
                author="Weidner Net",
                conditions=(
                    RuleCondition(
                        fact="house.has_error",
                        operator="falsy",
                    ),
                    RuleCondition(
                        fact="house.requires_attention",
                        operator="falsy",
                    ),
                    RuleCondition(
                        fact="house.has_activity",
                        operator="falsy",
                    ),
                ),
                result={
                    "state": "ready",
                    "message": "Das Haus ist bereit und ruhig.",
                    "source": "core",
                },
                source_file="builtin:core_contexts",
            ),
        )
    )


def combined_context_registry(custom: RuleRegistry) -> RuleRegistry:
    """Combine core and custom rules while protecting core rule IDs."""
    core = core_context_registry()
    core_ids = {rule.rule_id for rule in core.rules}
    custom_rules = tuple(
        rule for rule in custom.rules if rule.rule_id not in core_ids
    )
    duplicate_warnings = tuple(
        (
            f"Custom rule '{rule.rule_id}' cannot override a protected "
            "core context rule and was skipped"
        )
        for rule in custom.rules
        if rule.rule_id in core_ids
    )
    return RuleRegistry(
        rules=core.rules + custom_rules,
        warnings=core.warnings + custom.warnings + duplicate_warnings,
        loaded_files=core.loaded_files + custom.loaded_files,
    )
