"""YAML loader for declarative WNHF rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .model import Rule, RuleCondition, RuleRegistry


class RuleLoadError(ValueError):
    """Raised for an invalid individual rule definition."""


_ALLOWED_OPERATORS = {
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "not_in",
    "contains",
    "truthy",
    "falsy",
    "exists",
    "not_exists",
}


def _required_text(item: dict[str, Any], key: str, source: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuleLoadError(f"{source}: missing or invalid '{key}'")
    return value.strip()


def _parse_condition(
    raw: Any,
    source: str,
    index: int,
) -> RuleCondition:
    if not isinstance(raw, dict):
        raise RuleLoadError(
            f"{source}: condition #{index} must be a dictionary"
        )

    fact = _required_text(raw, "fact", source)
    operator = _required_text(raw, "operator", source)

    if operator not in _ALLOWED_OPERATORS:
        raise RuleLoadError(
            f"{source}: unsupported operator '{operator}'"
        )

    needs_value = operator not in {
        "truthy",
        "falsy",
        "exists",
        "not_exists",
    }
    if needs_value and "value" not in raw:
        raise RuleLoadError(
            f"{source}: condition '{fact}' requires a value"
        )

    return RuleCondition(
        fact=fact,
        operator=operator,
        value=raw.get("value"),
    )


def _parse_rule(raw: Any, source_file: str) -> Rule:
    if not isinstance(raw, dict):
        raise RuleLoadError(f"{source_file}: rule must be a dictionary")

    rule_id = _required_text(raw, "id", source_file)
    name = raw.get("name", rule_id)
    version = str(raw.get("version", "1.0"))
    description = str(raw.get("description", ""))
    author = str(raw.get("author", ""))

    priority = raw.get("priority", 0)
    if not isinstance(priority, int):
        raise RuleLoadError(
            f"{source_file}: rule '{rule_id}' priority must be an integer"
        )

    confidence = raw.get("confidence", 1.0)
    if not isinstance(confidence, (int, float)):
        raise RuleLoadError(
            f"{source_file}: rule '{rule_id}' confidence must be numeric"
        )
    confidence = float(confidence)
    if not 0.0 <= confidence <= 1.0:
        raise RuleLoadError(
            f"{source_file}: rule '{rule_id}' confidence must be 0..1"
        )

    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise RuleLoadError(
            f"{source_file}: rule '{rule_id}' enabled must be boolean"
        )

    conditions_raw = raw.get("conditions", [])
    if not isinstance(conditions_raw, list) or not conditions_raw:
        raise RuleLoadError(
            f"{source_file}: rule '{rule_id}' needs at least one condition"
        )

    result = raw.get("result")
    if not isinstance(result, dict) or not result:
        raise RuleLoadError(
            f"{source_file}: rule '{rule_id}' result must be a dictionary"
        )

    return Rule(
        rule_id=rule_id,
        name=str(name),
        version=version,
        priority=priority,
        confidence=confidence,
        enabled=enabled,
        description=description,
        author=author,
        conditions=tuple(
            _parse_condition(condition, source_file, index)
            for index, condition in enumerate(conditions_raw, start=1)
        ),
        result=dict(result),
        source_file=source_file,
    )


def _rule_items(raw: Any, source_file: str) -> list[Any]:
    if not isinstance(raw, dict):
        raise RuleLoadError(
            f"{source_file}: YAML root must be a dictionary"
        )

    if "rules" in raw:
        items = raw["rules"]
        if not isinstance(items, list):
            raise RuleLoadError(
                f"{source_file}: 'rules' must be a list"
            )
        return items

    if "rule" in raw:
        return [raw["rule"]]

    raise RuleLoadError(
        f"{source_file}: expected root key 'rule' or 'rules'"
    )


def load_rule_registry(root: Path) -> RuleRegistry:
    """Load all YAML rules; missing directory is a valid empty registry."""
    if not root.exists():
        return RuleRegistry()

    if not root.is_dir():
        return RuleRegistry(
            warnings=(f"Rules path is not a directory: {root}",)
        )

    rules: list[Rule] = []
    warnings: list[str] = []
    loaded_files: list[str] = []
    seen_ids: set[str] = set()

    paths = sorted((*root.glob("*.yaml"), *root.glob("*.yml")))
    for path in paths:
        source_file = str(path)
        loaded_files.append(source_file)

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            for item in _rule_items(raw, source_file):
                rule = _parse_rule(item, source_file)
                if rule.rule_id in seen_ids:
                    warnings.append(
                        f"Duplicate rule id '{rule.rule_id}' in {source_file}; "
                        "later definition skipped"
                    )
                    continue
                seen_ids.add(rule.rule_id)
                rules.append(rule)
        except (OSError, UnicodeError, yaml.YAMLError, RuleLoadError) as err:
            warnings.append(str(err))

    return RuleRegistry(
        rules=tuple(rules),
        warnings=tuple(warnings),
        loaded_files=tuple(loaded_files),
    )
