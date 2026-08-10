"""Simple YAML loader for optional WNHF decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .model import DecisionDefinition, DecisionRegistry, DecisionRule


def _contexts(raw: Any, source: str) -> tuple[str, ...]:
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, list) and raw:
        return tuple(str(item) for item in raw)
    raise ValueError(f"{source}: rule needs context or contexts")


def _parse_rule(raw: Any, index: int, source: str) -> DecisionRule:
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: rule #{index} must be a dictionary")

    priority = raw.get("priority", 0)
    if not isinstance(priority, int):
        raise ValueError(f"{source}: rule #{index} priority must be integer")

    return DecisionRule(
        rule_id=str(raw.get("id", f"rule_{index}")),
        contexts=_contexts(
            raw.get("contexts", raw.get("context")),
            source,
        ),
        recommend=bool(raw.get("recommend", True)),
        priority=priority,
        reason=str(
            raw.get(
                "reason",
                "Configured Decision Engine rule matched.",
            )
        ),
    )


def _parse_decision(raw: Any, source: str) -> DecisionDefinition:
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: decision must be a dictionary")

    decision_id = raw.get("id")
    if not isinstance(decision_id, str) or not decision_id.strip():
        raise ValueError(f"{source}: decision needs an id")

    action = raw.get("action")
    if not isinstance(action, str) or not action.strip():
        raise ValueError(f"{source}: decision '{decision_id}' needs action")

    target = raw.get("target", {})
    if not isinstance(target, dict):
        raise ValueError(f"{source}: target must be a dictionary")

    rules_raw = raw.get("rules", [])
    if not isinstance(rules_raw, list):
        raise ValueError(f"{source}: rules must be a list")

    policy_id = raw.get("policy")
    if policy_id is not None:
        policy_id = str(policy_id)

    return DecisionDefinition(
        decision_id=decision_id.strip(),
        name=str(raw.get("name", decision_id)),
        description=str(raw.get("description", "")),
        enabled=bool(raw.get("enabled", True)),
        default_recommend=bool(raw.get("default_recommend", False)),
        policy_id=policy_id,
        action=action.strip(),
        target=dict(target),
        rules=tuple(
            _parse_rule(item, index, source)
            for index, item in enumerate(rules_raw, start=1)
        ),
        source_file=source,
    )


def load_decision_registry(root: Path) -> DecisionRegistry:
    """Load decision YAML. Missing directory is a valid empty registry."""
    if not root.exists():
        return DecisionRegistry()

    warnings: list[str] = []
    loaded_files: list[str] = []
    decisions: list[DecisionDefinition] = []
    seen: set[str] = set()

    for path in sorted((*root.glob("*.yaml"), *root.glob("*.yml"))):
        loaded_files.append(str(path))
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("YAML root must be a dictionary")

            items = raw.get("decisions")
            if items is None:
                items = [raw["decision"]] if "decision" in raw else None
            if not isinstance(items, list):
                raise ValueError("Expected 'decision' or 'decisions'")

            for item in items:
                decision = _parse_decision(item, str(path))
                if decision.decision_id in seen:
                    warnings.append(
                        f"Duplicate decision '{decision.decision_id}' "
                        f"skipped: {path}"
                    )
                    continue
                seen.add(decision.decision_id)
                decisions.append(decision)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError, KeyError) as err:
            warnings.append(f"{path}: {err}")

    return DecisionRegistry(
        decisions=tuple(decisions),
        warnings=tuple(warnings),
        loaded_files=tuple(loaded_files),
    )
