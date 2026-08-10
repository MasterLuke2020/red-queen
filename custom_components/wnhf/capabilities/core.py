"""Built-in semantic capability declarations."""

from __future__ import annotations

from .base import (
    CapabilityAction,
    CapabilityDefinition,
    CapabilityKind,
)
from .registry import CapabilityRegistry


def register_core_capabilities(
    registry: CapabilityRegistry,
) -> None:
    """Register the five currently implemented WNHF domains."""
    definitions = (
        CapabilityDefinition(
            capability_id="lighting",
            version="1.0.0",
            name="Lighting",
            description=(
                "Semantic lighting state and control domain."
            ),
            kind=CapabilityKind.CORE,
            actions=(
                CapabilityAction(
                    action_id="lighting.turn_off",
                    name="Turn lighting off",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Turn off exactly one semantic light object."
                    ),
                ),
            ),
            required_provider_capabilities=("lighting",),
        ),
        CapabilityDefinition(
            capability_id="covers",
            version="1.0.0",
            name="Covers",
            description=(
                "Semantic cover state and movement domain."
            ),
            kind=CapabilityKind.CORE,
            actions=(
                CapabilityAction(
                    action_id="covers.snapshot",
                    name="Read cover state",
                    mutating=False,
                    confirmation_required=False,
                    description=(
                        "Read semantic cover state."
                    ),
                ),
            ),
            required_provider_capabilities=("covers",),
        ),
        CapabilityDefinition(
            capability_id="openings",
            version="1.0.0",
            name="Openings",
            description=(
                "Semantic windows, doors, locks and garage domain."
            ),
            kind=CapabilityKind.CORE,
            actions=(
                CapabilityAction(
                    action_id="openings.snapshot",
                    name="Read opening state",
                    mutating=False,
                    confirmation_required=False,
                    description=(
                        "Read semantic opening and access state."
                    ),
                ),
            ),
            required_provider_capabilities=("openings",),
        ),
        CapabilityDefinition(
            capability_id="security",
            version="1.0.0",
            name="Security",
            description=(
                "Aggregated semantic security state."
            ),
            kind=CapabilityKind.CORE,
            actions=(
                CapabilityAction(
                    action_id="security.snapshot",
                    name="Read security state",
                    mutating=False,
                    confirmation_required=False,
                    description=(
                        "Read aggregated semantic security state."
                    ),
                ),
            ),
            required_provider_capabilities=("security",),
        ),
        CapabilityDefinition(
            capability_id="validator",
            version="1.0.0",
            name="Validator",
            description=(
                "Framework registry and runtime validation."
            ),
            kind=CapabilityKind.CORE,
            actions=(
                CapabilityAction(
                    action_id="validator.validate",
                    name="Validate framework",
                    mutating=False,
                    confirmation_required=False,
                    description=(
                        "Run semantic and runtime validation."
                    ),
                ),
            ),
            required_provider_capabilities=("validator",),
        ),
    )

    for definition in definitions:
        registry.register(definition)
