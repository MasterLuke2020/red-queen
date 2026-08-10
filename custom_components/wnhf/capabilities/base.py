"""Stable semantic capability contract for WNHF."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Any


_CAPABILITY_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$"
)
_SEMVER_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$"
)


class CapabilityContractError(ValueError):
    """Raised when a capability violates the public contract."""


class CapabilityKind(StrEnum):
    """Capability ownership and scope."""

    CORE = "core"
    DOMAIN = "domain"
    EXTENSION = "extension"


class CapabilityLifecycleState(StrEnum):
    """Capability registration lifecycle state."""

    DECLARED = "declared"
    REGISTERED = "registered"
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class CapabilityAction:
    """One semantic action exposed by a capability."""

    action_id: str
    name: str
    mutating: bool
    confirmation_required: bool
    description: str

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "action_id": self.action_id,
            "name": self.name,
            "mutating": self.mutating,
            "confirmation_required": self.confirmation_required,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    """Immutable semantic capability declaration."""

    capability_id: str
    version: str
    name: str
    description: str
    kind: CapabilityKind
    actions: tuple[CapabilityAction, ...]
    required_provider_capabilities: tuple[str, ...]
    priority: int = 100
    enabled: bool = True

    CONTRACT_VERSION = "1.0"

    def as_dict(self) -> dict[str, Any]:
        """Return the public capability definition."""
        return {
            "capability_id": self.capability_id,
            "version": self.version,
            "contract_version": self.CONTRACT_VERSION,
            "name": self.name,
            "description": self.description,
            "kind": self.kind.value,
            "priority": self.priority,
            "enabled": self.enabled,
            "actions": [
                action.as_dict()
                for action in self.actions
            ],
            "required_provider_capabilities": list(
                self.required_provider_capabilities
            ),
        }


def validate_capability_definition(
    definition: CapabilityDefinition,
) -> tuple[str, ...]:
    """Validate one capability against contract v1.0."""
    errors: list[str] = []

    if not _CAPABILITY_ID_PATTERN.fullmatch(
        definition.capability_id
    ):
        errors.append(
            "capability_id must use lowercase semantic segments."
        )

    if not _SEMVER_PATTERN.fullmatch(definition.version):
        errors.append(
            "version must use semantic versioning x.y.z."
        )

    if not definition.name.strip():
        errors.append("name must not be empty.")

    action_ids = [
        action.action_id
        for action in definition.actions
    ]
    if len(action_ids) != len(set(action_ids)):
        errors.append("actions contain duplicate action IDs.")

    for action in definition.actions:
        if not _CAPABILITY_ID_PATTERN.fullmatch(action.action_id):
            errors.append(
                f"Invalid action ID: {action.action_id!r}."
            )

    provider_capabilities = (
        definition.required_provider_capabilities
    )
    if not provider_capabilities:
        errors.append(
            "required_provider_capabilities must not be empty."
        )
    if len(provider_capabilities) != len(
        set(provider_capabilities)
    ):
        errors.append(
            "required_provider_capabilities contains duplicates."
        )
    for capability_id in provider_capabilities:
        if not _CAPABILITY_ID_PATTERN.fullmatch(capability_id):
            errors.append(
                "Invalid required provider capability: "
                f"{capability_id!r}."
            )

    return tuple(errors)


def capability_contract_definition() -> dict[str, Any]:
    """Return the public capability contract."""
    return {
        "contract_id": "wnhf.capability",
        "contract_version": CapabilityDefinition.CONTRACT_VERSION,
        "status": "stable",
        "required_identity": [
            "capability_id",
            "version",
            "name",
        ],
        "required_sections": [
            "actions",
            "required_provider_capabilities",
        ],
        "capability_id_format": (
            "lowercase semantic segments with optional dots"
        ),
        "resolver_enabled": True,
        "manager_enabled": True,
        "execution_migration_enabled": True,
        "note": (
            "The public Capability Manager remains read-only; canonical "
            "Stage-4.7 execution consumes its resolved capability data."
        ),
    }
