"""Hardware-neutral execution capability resolver."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any



class EffectConfirmationMode(StrEnum):
    """Feedback requirement after command dispatch."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class ConfirmationPolicy:
    """Universal confirmation contract for one execution capability."""

    required_before_dispatch: bool
    effect_confirmation: EffectConfirmationMode
    observe_timeout_ms: int = 0
    observe_interval_ms: int = 200

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "before_dispatch": {
                "confirmation_required": self.required_before_dispatch,
            },
            "after_dispatch": {
                "mode": self.effect_confirmation.value,
                "observe_timeout_ms": self.observe_timeout_ms,
                "observe_interval_ms": self.observe_interval_ms,
            },
        }


@dataclass(frozen=True, slots=True)
class ExecutionCapability:
    """Resolved technical execution strategy for one semantic object."""

    capability_id: str
    provider_id: str
    object_id: str
    supported: bool
    available: bool
    healthy: bool
    strategy: str
    command_domain: str | None
    command_service: str | None
    command_entity_id: str | None
    feedback_required: bool
    feedback_entity_ids: tuple[str, ...]
    idempotency: str
    rollback_supported: bool
    confirmation_policy: ConfirmationPolicy
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "provider_id": self.provider_id,
            "object_id": self.object_id,
            "supported": self.supported,
            "available": self.available,
            "healthy": self.healthy,
            "strategy": self.strategy,
            "command": {
                "domain": self.command_domain,
                "service": self.command_service,
                "entity_id": self.command_entity_id,
            },
            "feedback": {
                "required": self.feedback_required,
                "entity_ids": list(self.feedback_entity_ids),
            },
            "idempotency": self.idempotency,
            "rollback_supported": self.rollback_supported,
            "confirmation_policy": self.confirmation_policy.as_dict(),
            "reason": self.reason,
        }


class ExecutionCapabilityAdapter:
    """Resolve semantic objects into hardware-neutral execution strategies."""

    VERSION = "2.7-rc5-garage-directional"

    @staticmethod
    def _unsupported(
        *,
        object_id: str,
        capability_id: str,
        command_entity_id: str | None = None,
        feedback_entity_ids: tuple[str, ...] = (),
        reason: str,
    ) -> ExecutionCapability:
        return ExecutionCapability(
            capability_id=capability_id,
            provider_id="provider.core.unsupported",
            object_id=object_id,
            supported=False,
            available=False,
            healthy=False,
            strategy="unsupported",
            command_domain=None,
            command_service=None,
            command_entity_id=command_entity_id,
            feedback_required=bool(feedback_entity_ids),
            feedback_entity_ids=feedback_entity_ids,
            idempotency="not_available",
            rollback_supported=False,
            confirmation_policy=ConfirmationPolicy(
                required_before_dispatch=True,
                effect_confirmation=EffectConfirmationMode.NONE,
            ),
            reason=reason,
        )

    @classmethod
    def resolve(
        cls,
        semantic_object,
        capability_id: str,
        snapshot=None,
    ) -> ExecutionCapability:
        """Resolve one canonical capability for one Registry object."""
        object_capabilities = {
            item.capability_id: item
            for item in semantic_object.object_capabilities()
        }
        declaration = object_capabilities.get(capability_id)
        if declaration is None:
            return cls._unsupported(
                object_id=semantic_object.object_id,
                capability_id=capability_id,
                reason=(
                    "The semantic object does not declare this capability."
                ),
            )

        if not semantic_object.enabled:
            return cls._unsupported(
                object_id=semantic_object.object_id,
                capability_id=capability_id,
                command_entity_id=(
                    declaration.command_entity_ids[0]
                    if declaration.command_entity_ids else None
                ),
                feedback_entity_ids=declaration.feedback_entity_ids,
                reason="The Registry object is disabled.",
            )

        if capability_id == "lighting.turn_on":
            return cls.resolve_light_turn_on(semantic_object, snapshot)

        if capability_id == "lighting.turn_off":
            return cls.resolve_light_turn_off(semantic_object, snapshot)

        if capability_id == "covers.open":
            return cls.resolve_cover_open(semantic_object, snapshot)

        if capability_id == "covers.close":
            return cls.resolve_cover_close(semantic_object, snapshot)

        if capability_id == "covers.blades_open":
            return cls.resolve_cover_blades_open(semantic_object, snapshot)

        if capability_id == "covers.blades_close":
            return cls.resolve_cover_blades_close(semantic_object, snapshot)

        if capability_id in {"access.lock", "access.unlock"}:
            return cls._resolve_access_lock_operation(
                semantic_object,
                capability_id,
                snapshot,
            )

        if capability_id == "access.door_open":
            return cls._resolve_access_door_open(
                semantic_object,
                snapshot,
            )

        if capability_id in {"access.toggle", "access.stop"}:
            return cls._resolve_access_garage_operation(
                semantic_object,
                capability_id,
                snapshot,
            )

        return cls._unsupported(
            object_id=semantic_object.object_id,
            capability_id=capability_id,
            command_entity_id=(
                declaration.command_entity_ids[0]
                if declaration.command_entity_ids else None
            ),
            feedback_entity_ids=declaration.feedback_entity_ids,
            reason=(
                "The capability is declared, but no qualified execution "
                "resolver exists in this stage."
            ),
        )

    @classmethod
    def resolve_light_turn_on(cls, light, snapshot=None) -> ExecutionCapability:
        """Resolve a safe turn-on strategy for one light."""
        if snapshot is None:
            return ExecutionCapability(
                capability_id="lighting.turn_on",
                provider_id="provider.core.lighting.disabled",
                object_id=light.object_id,
                supported=False,
                available=False,
                healthy=False,
                strategy="disabled_or_not_loaded",
                command_domain=None,
                command_service=None,
                command_entity_id=light.command_entity_id,
                feedback_required=True,
                feedback_entity_ids=tuple(light.state_entity_ids),
                idempotency="not_available",
                rollback_supported=False,
                confirmation_policy=ConfirmationPolicy(
                    required_before_dispatch=False,
                    effect_confirmation=EffectConfirmationMode.REQUIRED,
                    observe_timeout_ms=5000,
                ),
                reason="No runtime snapshot exists.",
            )

        if light.control_mode == "toggle" and light.command_entity_id:
            available = bool(snapshot.available)
            healthy = available and bool(light.state_entity_ids)
            return ExecutionCapability(
                capability_id="lighting.turn_on",
                provider_id="provider.core.lighting.toggle",
                object_id=light.object_id,
                supported=True,
                available=available,
                healthy=healthy,
                strategy="guarded_momentary_pulse",
                command_domain="button",
                command_service="press",
                command_entity_id=light.command_entity_id,
                feedback_required=True,
                feedback_entity_ids=tuple(light.state_entity_ids),
                idempotency="guarded_by_feedback",
                rollback_supported=False,
                confirmation_policy=ConfirmationPolicy(
                    required_before_dispatch=False,
                    effect_confirmation=EffectConfirmationMode.REQUIRED,
                    observe_timeout_ms=5000,
                ),
                reason=(
                    "Momentary pulse is permitted only after feedback "
                    "confirms that the light is currently off."
                ),
            )

        return cls._unsupported(
            object_id=light.object_id,
            capability_id="lighting.turn_on",
            command_entity_id=light.command_entity_id,
            feedback_entity_ids=tuple(light.state_entity_ids),
            reason=f"No safe adapter for control_mode={light.control_mode!r}.",
        )

    @classmethod
    def resolve_light_turn_off(cls, light, snapshot=None) -> ExecutionCapability:
        """Resolve a safe turn-off strategy for one light."""
        if snapshot is None:
            return ExecutionCapability(
                capability_id="lighting.turn_off",
                provider_id="provider.core.lighting.disabled",
                object_id=light.object_id,
                supported=False,
                available=False,
                healthy=False,
                strategy="disabled_or_not_loaded",
                command_domain=None,
                command_service=None,
                command_entity_id=light.command_entity_id,
                feedback_required=True,
                feedback_entity_ids=tuple(light.state_entity_ids),
                idempotency="not_available",
                rollback_supported=False,
                confirmation_policy=ConfirmationPolicy(
                    required_before_dispatch=False,
                    effect_confirmation=EffectConfirmationMode.REQUIRED,
                    observe_timeout_ms=5000,
                ),
                reason="No runtime snapshot exists.",
            )

        if light.control_mode == "toggle" and light.command_entity_id:
            available = bool(snapshot.available)
            healthy = available and bool(light.state_entity_ids)
            return ExecutionCapability(
                capability_id="lighting.turn_off",
                provider_id="provider.core.lighting.toggle",
                object_id=light.object_id,
                supported=True,
                available=available,
                healthy=healthy,
                strategy="guarded_momentary_pulse",
                command_domain="button",
                command_service="press",
                command_entity_id=light.command_entity_id,
                feedback_required=True,
                feedback_entity_ids=tuple(light.state_entity_ids),
                idempotency="guarded_by_feedback",
                rollback_supported=False,
                confirmation_policy=ConfirmationPolicy(
                    required_before_dispatch=False,
                    effect_confirmation=EffectConfirmationMode.REQUIRED,
                    observe_timeout_ms=5000,
                ),
                reason=(
                    "Momentary pulse is permitted only after feedback "
                    "confirms that the light is currently on."
                ),
            )

        return cls._unsupported(
            object_id=light.object_id,
            capability_id="lighting.turn_off",
            command_entity_id=light.command_entity_id,
            feedback_entity_ids=tuple(light.state_entity_ids),
            reason=f"No safe adapter for control_mode={light.control_mode!r}.",
        )

    @classmethod
    def _resolve_cover_direction(
        cls,
        cover,
        snapshot,
        *,
        action_id: str,
        command_entity_id: str | None,
        registry_capability: str,
    ) -> ExecutionCapability:
        """Resolve one feedback-guarded directional cover command."""
        feedback_entity_ids = tuple(cover.direction_feedback_entity_ids)

        if registry_capability not in cover.capabilities:
            return cls._unsupported(
                object_id=cover.object_id,
                capability_id=action_id,
                command_entity_id=command_entity_id,
                feedback_entity_ids=feedback_entity_ids,
                reason=(
                    f"Registry cover does not declare capability "
                    f"{registry_capability!r}."
                ),
            )

        if snapshot is None:
            return cls._unsupported(
                object_id=cover.object_id,
                capability_id=action_id,
                command_entity_id=command_entity_id,
                feedback_entity_ids=feedback_entity_ids,
                reason="No runtime cover snapshot exists.",
            )

        available = bool(snapshot.available)
        healthy = available and not bool(snapshot.is_error)
        direction = "opening" if action_id == "covers.open" else "closing"
        return ExecutionCapability(
            capability_id=action_id,
            provider_id="provider.core.covers.directional",
            object_id=cover.object_id,
            supported=True,
            available=available,
            healthy=healthy,
            strategy="guarded_directional_cover_pulse",
            command_domain="button",
            command_service="press",
            command_entity_id=command_entity_id,
            feedback_required=True,
            feedback_entity_ids=feedback_entity_ids,
            idempotency="guarded_by_directional_feedback",
            rollback_supported=False,
            confirmation_policy=ConfirmationPolicy(
                required_before_dispatch=False,
                effect_confirmation=EffectConfirmationMode.REQUIRED,
                observe_timeout_ms=5000,
                observe_interval_ms=100,
            ),
            reason=(
                f"Directional cover pulse is permitted only with available, "
                f"non-conflicting feedback; {direction} or the target end "
                "state must be observed after dispatch."
            ),
        )

    @classmethod
    def resolve_cover_open(cls, cover, snapshot=None) -> ExecutionCapability:
        """Resolve canonical covers.open execution."""
        return cls._resolve_cover_direction(
            cover,
            snapshot,
            action_id="covers.open",
            command_entity_id=cover.open_command_entity_id,
            registry_capability="open",
        )

    @classmethod
    def resolve_cover_close(cls, cover, snapshot=None) -> ExecutionCapability:
        """Resolve canonical covers.close execution."""
        return cls._resolve_cover_direction(
            cover,
            snapshot,
            action_id="covers.close",
            command_entity_id=cover.close_command_entity_id,
            registry_capability="close",
        )

    @classmethod
    def _resolve_cover_blades(
        cls,
        cover,
        snapshot,
        *,
        action_id: str,
        command_entity_id: str | None,
        registry_capability: str,
    ) -> ExecutionCapability:
        """Resolve one dispatch-scoped venetian-blind blade command."""
        if registry_capability not in cover.capabilities:
            return cls._unsupported(
                object_id=cover.object_id,
                capability_id=action_id,
                command_entity_id=command_entity_id,
                reason=(
                    "Registry cover does not declare capability "
                    f"{registry_capability!r}."
                ),
            )

        if not command_entity_id:
            return cls._unsupported(
                object_id=cover.object_id,
                capability_id=action_id,
                reason="No blade command entity is configured.",
            )

        if snapshot is None:
            return cls._unsupported(
                object_id=cover.object_id,
                capability_id=action_id,
                command_entity_id=command_entity_id,
                reason="No runtime cover snapshot exists.",
            )

        available = bool(snapshot.available)
        healthy = available and not bool(snapshot.is_error)
        return ExecutionCapability(
            capability_id=action_id,
            provider_id="provider.core.covers.blades",
            object_id=cover.object_id,
            supported=True,
            available=available,
            healthy=healthy,
            strategy="dispatch_scoped_blade_pulse",
            command_domain="button",
            command_service="press",
            command_entity_id=command_entity_id,
            feedback_required=False,
            feedback_entity_ids=(),
            idempotency="non_idempotent_dispatch",
            rollback_supported=False,
            confirmation_policy=ConfirmationPolicy(
                required_before_dispatch=False,
                effect_confirmation=EffectConfirmationMode.NONE,
            ),
            reason=(
                "Configured blade command is dispatch-qualified. No objective "
                "blade-position feedback or final blade state is claimed."
            ),
        )

    @classmethod
    def resolve_cover_blades_open(
        cls,
        cover,
        snapshot=None,
    ) -> ExecutionCapability:
        """Resolve canonical covers.blades_open execution."""
        return cls._resolve_cover_blades(
            cover,
            snapshot,
            action_id="covers.blades_open",
            command_entity_id=cover.blades_open_command_entity_id,
            registry_capability="blades_open",
        )

    @classmethod
    def resolve_cover_blades_close(
        cls,
        cover,
        snapshot=None,
    ) -> ExecutionCapability:
        """Resolve canonical covers.blades_close execution."""
        return cls._resolve_cover_blades(
            cover,
            snapshot,
            action_id="covers.blades_close",
            command_entity_id=cover.blades_close_command_entity_id,
            registry_capability="blades_close",
        )

    @classmethod
    def _resolve_garage_direction(
        cls,
        opening,
        snapshot,
        *,
        action_id: str,
    ) -> ExecutionCapability:
        """Resolve one canonical garage direction through a guarded OSC pulse.

        Residential garage drives commonly expose one OSC (open/stop/close)
        pulse input rather than dedicated directional inputs.  A canonical
        direction is therefore safe only when both end-position feedback
        signals are available and the runtime starts at a proven end position.
        The provider applies the final state guard before dispatch.
        """
        garage = opening.garage_door
        if garage is None or not opening.is_garage_door:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id=action_id,
                reason="No dedicated garage-door OSC module is configured.",
            )

        feedback = (
            garage.open_feedback_entity_id,
            garage.closed_feedback_entity_id,
        )
        if action_id not in {"garage.open", "garage.close"}:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id=action_id,
                command_entity_id=garage.toggle_command_entity_id,
                feedback_entity_ids=feedback,
                reason="Unsupported canonical garage direction.",
            )

        if snapshot is None:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id=action_id,
                command_entity_id=garage.toggle_command_entity_id,
                feedback_entity_ids=feedback,
                reason="No runtime garage snapshot exists.",
            )

        available = bool(snapshot.available)
        healthy = available and snapshot.state != "error"
        target = "open" if action_id == "garage.open" else "closed"
        return ExecutionCapability(
            capability_id=action_id,
            provider_id="provider.core.garage.osc",
            object_id=opening.object_id,
            supported=True,
            available=available,
            healthy=healthy,
            strategy="guarded_directional_osc_pulse",
            command_domain="button",
            command_service="press",
            command_entity_id=garage.toggle_command_entity_id,
            feedback_required=True,
            feedback_entity_ids=feedback,
            idempotency=f"guarded_by_{target}_end_feedback",
            rollback_supported=False,
            confirmation_policy=ConfirmationPolicy(
                required_before_dispatch=True,
                effect_confirmation=EffectConfirmationMode.REQUIRED,
                observe_timeout_ms=5000,
                observe_interval_ms=100,
            ),
            reason=(
                "OSC pulse is permitted only from a proven garage end "
                f"position; movement start and terminal {target} feedback "
                "must be observed after dispatch."
            ),
        )

    @classmethod
    def resolve_garage_open(cls, opening, snapshot=None) -> ExecutionCapability:
        """Resolve canonical garage.open execution."""
        return cls._resolve_garage_direction(
            opening,
            snapshot,
            action_id="garage.open",
        )

    @classmethod
    def resolve_garage_close(cls, opening, snapshot=None) -> ExecutionCapability:
        """Resolve canonical garage.close execution."""
        return cls._resolve_garage_direction(
            opening,
            snapshot,
            action_id="garage.close",
        )

    @classmethod
    def resolve_garage_stop(cls, opening, snapshot=None) -> ExecutionCapability:
        """Resolve canonical garage.stop through a dedicated STOP pulse."""
        garage = opening.garage_door
        if garage is None or not opening.is_garage_door:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id="garage.stop",
                reason="No dedicated garage-door module is configured.",
            )

        feedback = (
            garage.open_feedback_entity_id,
            garage.closed_feedback_entity_id,
        )
        if not garage.stop_command_entity_id:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id="garage.stop",
                feedback_entity_ids=feedback,
                reason="No dedicated garage STOP command is configured.",
            )
        if snapshot is None:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id="garage.stop",
                command_entity_id=garage.stop_command_entity_id,
                feedback_entity_ids=feedback,
                reason="No runtime garage snapshot exists.",
            )

        available = bool(snapshot.available)
        healthy = available and snapshot.state != "error"
        return ExecutionCapability(
            capability_id="garage.stop",
            provider_id="provider.core.garage.stop",
            object_id=opening.object_id,
            supported=True,
            available=available,
            healthy=healthy,
            strategy="guarded_dedicated_stop_pulse",
            command_domain="button",
            command_service="press",
            command_entity_id=garage.stop_command_entity_id,
            feedback_required=False,
            feedback_entity_ids=feedback,
            idempotency="guarded_by_moving_state",
            rollback_supported=False,
            confirmation_policy=ConfirmationPolicy(
                required_before_dispatch=True,
                effect_confirmation=EffectConfirmationMode.NONE,
            ),
            reason=(
                "STOP is permitted only while the garage door is objectively "
                "moving. Dispatch proves only the configured STOP pulse; no "
                "physical stopped state is claimed without motion feedback."
            ),
        )

    @classmethod
    def _resolve_access_lock_operation(
        cls,
        opening,
        capability_id: str,
        snapshot,
    ) -> ExecutionCapability:
        lock = opening.lock
        if lock is None:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id=capability_id,
                reason="No motor-lock module is configured.",
            )

        command_entity_id = (
            lock.lock_command_entity_id
            if capability_id == "access.lock"
            else lock.unlock_command_entity_id
        )
        if not command_entity_id:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id=capability_id,
                feedback_entity_ids=(lock.feedback_entity_id,),
                reason="The required motor-lock command is not configured.",
            )

        available = bool(snapshot is not None and snapshot.available)
        healthy = available and snapshot.lock_state in {"locked", "unlocked"}
        target = "locked" if capability_id == "access.lock" else "unlocked"
        return ExecutionCapability(
            capability_id=capability_id,
            provider_id="provider.core.access.motor_lock",
            object_id=opening.object_id,
            supported=True,
            available=available,
            healthy=healthy,
            strategy="guarded_button_with_lock_feedback",
            command_domain="button",
            command_service="press",
            command_entity_id=command_entity_id,
            feedback_required=True,
            feedback_entity_ids=(lock.feedback_entity_id,),
            idempotency=f"guarded_by_{target}_feedback",
            rollback_supported=False,
            confirmation_policy=ConfirmationPolicy(
                required_before_dispatch=True,
                effect_confirmation=EffectConfirmationMode.REQUIRED,
                observe_timeout_ms=8000,
            ),
            reason=(
                f"Button pulse is permitted only after feedback confirms "
                f"that the lock is not already {target}."
            ),
        )

    @classmethod
    def _resolve_access_door_open(cls, opening, snapshot) -> ExecutionCapability:
        opener = opening.door_opener
        if opener is None:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id="access.door_open",
                reason="No electric door opener is configured.",
            )

        available = bool(snapshot is not None and snapshot.available)
        feedback_entity_ids = (
            (opening.state_entity_id,)
            if opening.state_entity_id is not None
            else ()
        )
        return ExecutionCapability(
            capability_id="access.door_open",
            provider_id="provider.core.access.door_opener",
            object_id=opening.object_id,
            supported=True,
            available=available,
            healthy=available and bool(feedback_entity_ids),
            strategy="confirmed_dispatch_scoped_momentary_pulse",
            command_domain="button",
            command_service="press",
            command_entity_id=opener.command_entity_id,
            feedback_required=False,
            feedback_entity_ids=feedback_entity_ids,
            idempotency="non_idempotent_dispatch",
            rollback_supported=False,
            confirmation_policy=ConfirmationPolicy(
                required_before_dispatch=True,
                effect_confirmation=EffectConfirmationMode.NONE,
            ),
            reason=(
                "Explicit confirmation and a closed, available door contact "
                "are required before dispatch. Successful execution proves "
                "only the configured door-opener pulse dispatch."
            ),
        )

    @classmethod
    def _resolve_access_garage_operation(
        cls,
        opening,
        capability_id: str,
        snapshot,
    ) -> ExecutionCapability:
        garage = opening.garage_door
        if garage is None:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id=capability_id,
                reason="No dedicated garage-door module is configured.",
            )

        command_entity_id = (
            garage.toggle_command_entity_id
            if capability_id == "access.toggle"
            else garage.stop_command_entity_id
        )
        feedback = (
            garage.open_feedback_entity_id,
            garage.closed_feedback_entity_id,
        )
        if not command_entity_id:
            return cls._unsupported(
                object_id=opening.object_id,
                capability_id=capability_id,
                feedback_entity_ids=feedback,
                reason=(
                    "The requested garage-door command is not configured."
                ),
            )

        available = bool(snapshot is not None and snapshot.available)
        healthy = available and snapshot.state != "error"
        return ExecutionCapability(
            capability_id=capability_id,
            provider_id="provider.core.access.garage_osc",
            object_id=opening.object_id,
            supported=True,
            available=available,
            healthy=healthy,
            strategy=(
                "guarded_osc_pulse"
                if capability_id == "access.toggle"
                else "guarded_stop_pulse"
            ),
            command_domain="button",
            command_service="press",
            command_entity_id=command_entity_id,
            feedback_required=True,
            feedback_entity_ids=feedback,
            idempotency=(
                "non_idempotent_state_guarded_pulse"
                if capability_id == "access.toggle"
                else "guarded_by_movement_state"
            ),
            rollback_supported=False,
            confirmation_policy=ConfirmationPolicy(
                required_before_dispatch=True,
                effect_confirmation=EffectConfirmationMode.REQUIRED,
                observe_timeout_ms=5000,
                observe_interval_ms=100,
            ),
            reason=(
                "The command requires a stable garage end position and "
                "valid, non-contradictory feedback before dispatch."
            ),
        )
