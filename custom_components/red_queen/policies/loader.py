"""Simple YAML loader for optional WNHF policies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .model import (
    Policy,
    PolicyDecisionValue,
    PolicyMode,
    PolicyRegistry,
    PolicyRule,
)


def _decision(value: Any, source: str) -> PolicyDecisionValue:
    try:
        return PolicyDecisionValue(str(value).lower())
    except ValueError as err:
        raise ValueError(
            f"{source}: decision must be 'allow' or 'deny'"
        ) from err


def _parse_rule(raw: Any, index: int, source: str) -> PolicyRule:
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: rule #{index} must be a dictionary")

    contexts_raw = raw.get("contexts", raw.get("context", []))
    if isinstance(contexts_raw, str):
        contexts = (contexts_raw,)
    elif isinstance(contexts_raw, list):
        contexts = tuple(str(item) for item in contexts_raw)
    else:
        raise ValueError(f"{source}: rule #{index} has invalid contexts")

    if not contexts:
        raise ValueError(f"{source}: rule #{index} needs a context")

    capabilities_raw = raw.get("requires_capabilities", [])
    if isinstance(capabilities_raw, str):
        capabilities = (capabilities_raw,)
    elif isinstance(capabilities_raw, list):
        capabilities = tuple(str(item) for item in capabilities_raw)
    else:
        raise ValueError(
            f"{source}: rule #{index} has invalid requires_capabilities"
        )

    priority = raw.get("priority", 0)
    if not isinstance(priority, int):
        raise ValueError(f"{source}: rule #{index} priority must be integer")

    return PolicyRule(
        rule_id=str(raw.get("id", f"rule_{index}")),
        contexts=contexts,
        decision=_decision(raw.get("decision", "allow"), source),
        priority=priority,
        reason=str(raw.get("reason", "Configured policy rule matched.")),
        requires_capabilities=capabilities,
    )


def _parse_policy(raw: Any, source: str) -> Policy:
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: policy must be a dictionary")

    policy_id = raw.get("id")
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise ValueError(f"{source}: policy needs an id")

    rules_raw = raw.get("rules", [])
    if not isinstance(rules_raw, list):
        raise ValueError(f"{source}: rules must be a list")

    return Policy(
        policy_id=policy_id.strip(),
        name=str(raw.get("name", policy_id)),
        description=str(raw.get("description", "")),
        default=_decision(raw.get("default", "allow"), source),
        enabled=bool(raw.get("enabled", True)),
        rules=tuple(
            _parse_rule(rule, index, source)
            for index, rule in enumerate(rules_raw, start=1)
        ),
        source_file=source,
    )


def load_policy_registry(root: Path) -> PolicyRegistry:
    """Load settings and policies. Missing configuration is valid."""
    if not root.exists():
        return PolicyRegistry()

    warnings: list[str] = []
    loaded_files: list[str] = []
    mode = PolicyMode.MONITOR

    settings_path = root / "settings.yaml"
    if settings_path.exists():
        loaded_files.append(str(settings_path))
        try:
            raw = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
            if not isinstance(raw, dict):
                raise ValueError("settings.yaml root must be a dictionary")
            mode = PolicyMode(str(raw.get("mode", "monitor")).lower())
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as err:
            warnings.append(f"{settings_path}: {err}")

    policies: list[Policy] = []
    seen: set[str] = set()

    for path in sorted((*root.glob("*.yaml"), *root.glob("*.yml"))):
        if path.name == "settings.yaml":
            continue
        loaded_files.append(str(path))
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("YAML root must be a dictionary")

            items = raw.get("policies")
            if items is None:
                items = [raw["policy"]] if "policy" in raw else None
            if not isinstance(items, list):
                raise ValueError("Expected 'policy' or 'policies'")

            for item in items:
                policy = _parse_policy(item, str(path))
                if policy.policy_id in seen:
                    warnings.append(
                        f"Duplicate policy '{policy.policy_id}' skipped: {path}"
                    )
                    continue
                seen.add(policy.policy_id)
                policies.append(policy)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError, KeyError) as err:
            warnings.append(f"{path}: {err}")

    return PolicyRegistry(
        mode=mode,
        policies=tuple(policies),
        warnings=tuple(warnings),
        loaded_files=tuple(loaded_files),
    )
