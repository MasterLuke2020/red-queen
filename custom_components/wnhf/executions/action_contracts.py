"""Canonical semantic action execution contracts.

This module is intentionally small and side-effect free. Capability declarations
answer which semantic actions exist; this registry answers which of those actions
are currently enabled through the canonical real-execution surface and validates
their public request envelope before any provider dispatch can occur.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CanonicalActionExecutionContract:
    """Public request contract for one real-execution-enabled semantic action."""

    action_id: str
    target_mode: str
    required_target_keys: tuple[str, ...]
    allowed_target_keys: tuple[str, ...]
    allowed_parameter_keys: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "real_execution_enabled": True,
            "target_mode": self.target_mode,
            "required_target_keys": list(self.required_target_keys),
            "allowed_target_keys": list(self.allowed_target_keys),
            "allowed_parameter_keys": list(self.allowed_parameter_keys),
        }

    def validate_target(self, target: dict[str, Any]) -> tuple[str, ...]:
        errors: list[str] = []
        if not isinstance(target, dict):
            return ("target must be an object/map.",)

        keys = set(target)
        missing = [key for key in self.required_target_keys if key not in keys]
        if missing:
            errors.append(
                "target is missing required key(s): " + ", ".join(sorted(missing)) + "."
            )

        unexpected = sorted(keys - set(self.allowed_target_keys))
        if unexpected:
            errors.append(
                "target contains unsupported key(s): " + ", ".join(unexpected) + "."
            )

        object_id = target.get("object_id")
        if "object_id" in self.required_target_keys and (
            not isinstance(object_id, str) or not object_id.strip()
        ):
            errors.append("target.object_id must be a non-empty semantic object ID.")

        return tuple(errors)

    def validate_parameters(self, parameters: dict[str, Any]) -> tuple[str, ...]:
        if not isinstance(parameters, dict):
            return ("parameters must be an object/map.",)
        unexpected = sorted(set(parameters) - set(self.allowed_parameter_keys))
        if unexpected:
            return (
                "parameters contains unsupported key(s): "
                + ", ".join(unexpected)
                + ".",
            )
        return ()


_CANONICAL_ACTION_CONTRACTS = {
    "lighting.turn_off": CanonicalActionExecutionContract(
        action_id="lighting.turn_off",
        target_mode="single_object",
        required_target_keys=("object_id",),
        allowed_target_keys=("object_id",),
        allowed_parameter_keys=(),
    ),
}

REAL_EXECUTION_ENABLED_ACTIONS = frozenset(_CANONICAL_ACTION_CONTRACTS)


def get_canonical_action_contract(
    action_id: str,
) -> CanonicalActionExecutionContract | None:
    """Return the real-execution contract, if the action is enabled."""
    return _CANONICAL_ACTION_CONTRACTS.get(action_id)


def is_real_execution_enabled(action_id: str) -> bool:
    """Return whether an action is exposed through canonical real execution."""
    return action_id in REAL_EXECUTION_ENABLED_ACTIONS
