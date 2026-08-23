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
    """Register the currently implemented Red Queen core domains."""
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
                    action_id="lighting.turn_on",
                    name="Turn lighting on",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Turn on exactly one semantic light object."
                    ),
                ),
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
            version="1.1.0",
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
                CapabilityAction(
                    action_id="covers.open",
                    name="Open cover",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Start opening exactly one semantic cover object."
                    ),
                ),
                CapabilityAction(
                    action_id="covers.close",
                    name="Close cover",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Start closing exactly one semantic cover object."
                    ),
                ),
                CapabilityAction(
                    action_id="covers.blades_open",
                    name="Open cover blades",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Dispatch the configured blade-open command for "
                        "exactly one semantic venetian-blind object."
                    ),
                ),
                CapabilityAction(
                    action_id="covers.blades_close",
                    name="Close cover blades",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Dispatch the configured blade-close command for "
                        "exactly one semantic venetian-blind object."
                    ),
                ),
            ),
            required_provider_capabilities=("covers",),
        ),
        CapabilityDefinition(
            capability_id="openings",
            version="1.2.0",
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
                CapabilityAction(
                    action_id="openings.lock",
                    name="Lock door",
                    mutating=True,
                    confirmation_required=True,
                    description=(
                        "Lock exactly one semantic door object with "
                        "closed-door and lock-feedback guards."
                    ),
                ),
                CapabilityAction(
                    action_id="openings.unlock",
                    name="Unlock door",
                    mutating=True,
                    confirmation_required=True,
                    description=(
                        "Unlock exactly one semantic door object with "
                        "closed-door and lock-feedback guards."
                    ),
                ),
                CapabilityAction(
                    action_id="openings.release",
                    name="Release door opener",
                    mutating=True,
                    confirmation_required=True,
                    description=(
                        "Dispatch exactly one configured electric door-opener "
                        "pulse for one semantic closed door."
                    ),
                ),
            ),
            required_provider_capabilities=("openings",),
        ),
        CapabilityDefinition(
            capability_id="garage",
            version="1.0.0",
            name="Garage",
            description=(
                "Semantic residential garage-door state and directional control."
            ),
            kind=CapabilityKind.CORE,
            actions=(
                CapabilityAction(
                    action_id="garage.snapshot",
                    name="Read garage state",
                    mutating=False,
                    confirmation_required=False,
                    description=(
                        "Read normalized residential garage-door state."
                    ),
                ),
                CapabilityAction(
                    action_id="garage.open",
                    name="Open garage door",
                    mutating=True,
                    confirmation_required=True,
                    description=(
                        "Open exactly one garage door from a proven closed "
                        "end position through its guarded OSC command."
                    ),
                ),
                CapabilityAction(
                    action_id="garage.close",
                    name="Close garage door",
                    mutating=True,
                    confirmation_required=True,
                    description=(
                        "Close exactly one garage door from a proven open "
                        "end position through its guarded OSC command."
                    ),
                ),
                CapabilityAction(
                    action_id="garage.stop",
                    name="Stop garage door",
                    mutating=True,
                    confirmation_required=True,
                    description=(
                        "Dispatch exactly one dedicated STOP pulse while the "
                        "garage door is objectively in the moving state."
                    ),
                ),
            ),
            required_provider_capabilities=("garage",),
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
            capability_id="notifications",
            version="1.1.0",
            name="Notifications",
            description=(
                "Semantic notification targets and provider-neutral message dispatch."
            ),
            kind=CapabilityKind.CORE,
            actions=(
                CapabilityAction(
                    action_id="notifications.snapshot",
                    name="Read notification target state",
                    mutating=False,
                    confirmation_required=False,
                    description=(
                        "Read configured semantic notification targets and their "
                        "current provider availability."
                    ),
                ),
                CapabilityAction(
                    action_id="notifications.send",
                    name="Send notification",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Dispatch one explicit message to exactly one semantic "
                        "notification target."
                    ),
                ),
                CapabilityAction(
                    action_id="notifications.announce",
                    name="Play house announcement",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Play one native TTS announcement through exactly one "
                        "semantic announcement target."
                    ),
                ),
                CapabilityAction(
                    action_id="notifications.route",
                    name="Route notification",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Route one semantic notification request through the "
                        "installation's log, dashboard, mobile and voice channels."
                    ),
                ),
            ),
            required_provider_capabilities=("notifications",),
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
        CapabilityDefinition(
            capability_id="plants",
            version="1.0.0",
            name="Plant Care",
            description=(
                "Semantic plant registry and persistent watering history."
            ),
            kind=CapabilityKind.CORE,
            actions=(
                CapabilityAction(
                    action_id="plants.snapshot",
                    name="Read plant-care state",
                    mutating=False,
                    confirmation_required=False,
                    description=(
                        "Read interval- and history-based care state for "
                        "configured semantic plants."
                    ),
                ),
                CapabilityAction(
                    action_id="plants.record_watering",
                    name="Record plant watering",
                    mutating=True,
                    confirmation_required=False,
                    description=(
                        "Persist one real manual watering event for exactly "
                        "one semantic plant object."
                    ),
                ),
            ),
            required_provider_capabilities=("plants",),
        ),
    )

    for definition in definitions:
        registry.register(definition)
