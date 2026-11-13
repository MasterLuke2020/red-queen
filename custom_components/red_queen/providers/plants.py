"""Native provider for Red Queen Plant Care."""

from __future__ import annotations

from homeassistant.helpers.dispatcher import async_dispatcher_send

from ..const import SIGNAL_PLANTS_UPDATED
from ..domain.capability import CapabilitySnapshot, CapabilityState
from .base import ProviderKind, WNHFProvider
from .execution import ProviderExecutionResult, ProviderExecutionValidationResult


class PlantsCapabilityProvider(WNHFProvider):
    """Persist human-confirmed watering events without hardware claims."""

    provider_kind = ProviderKind.CORE
    provider_version = "1.0.0"
    provider_name = "PlantsCapabilityProvider"
    discoverable = True
    priority = 100

    def __init__(self, engine) -> None:
        super().__init__(engine.hass)
        self.engine = engine

    @property
    def provider_id(self) -> str:
        return "provider.core.plants"

    def supported_capabilities(self) -> tuple[str, ...]:
        return ("plants",)

    def snapshot(self) -> CapabilitySnapshot:
        house = self.engine._require_house()
        store = self.engine.plant_watering_history_store
        # The registry is intentionally optional. An empty Plant Care domain is
        # a healthy configured capability, not a framework warning.
        supported = True
        available = store.loaded and store.load_error is None
        healthy = available and store.write_error is None
        if not available:
            state = CapabilityState.UNAVAILABLE
            message = "Plant watering history is unavailable."
        elif not healthy:
            state = CapabilityState.DEGRADED
            message = "Plant watering history has a persistence warning."
        else:
            state = CapabilityState.HEALTHY
            message = (
                f"Plant Care is ready for {len(house.plants)} configured plants."
            )
        return CapabilitySnapshot(
            capability_id="plants",
            provider_id=self.provider_id,
            supported=supported,
            available=available,
            healthy=healthy,
            state=state,
            message=message,
            details={
                "plant_count": len(house.plants),
                "enabled_plant_count": len(house.enabled_plants),
                "watering_history": store.snapshot(),
                "moisture_sensor_evaluation_enabled": False,
            },
        )

    def _technical_capability(self, object_id: str) -> dict:
        return {
            "capability_id": "plants.record_watering",
            "provider_id": "provider.core.plants.history",
            "object_id": object_id,
            "supported": True,
            "available": True,
            "healthy": True,
            "strategy": "persistent_verified_state_event",
            "command": {
                "domain": "wnhf",
                "operation": "record_watering",
                "storage": "plant_care/watering_history.json",
            },
            "feedback": {
                "required": True,
                "mode": "persistent_read_after_write",
            },
            "idempotency": "non_idempotent_event_append",
            "rollback_supported": False,
            "confirmation_policy": {
                "before_dispatch": {"confirmation_required": False},
                "after_dispatch": {
                    "mode": "required",
                    "observe_timeout_ms": 0,
                    "observe_interval_ms": 0,
                },
            },
            "verification_scope": "state",
            "hardware_effect_claimed": False,
            "reason": (
                "The manual watering event is qualified only after an atomic "
                "persistent write and read-after-write verification."
            ),
        }

    async def async_validate_execution(
        self,
        *,
        action_id: str,
        target: dict,
        parameters: dict,
        confirmed: bool,
    ) -> ProviderExecutionValidationResult:
        if action_id != "plants.record_watering":
            return await super().async_validate_execution(
                action_id=action_id,
                target=target,
                parameters=parameters,
                confirmed=confirmed,
            )
        object_id = target.get("object_id")
        if not isinstance(object_id, str) or not object_id.strip():
            return ProviderExecutionValidationResult(
                valid=False,
                reason="plants.record_watering requires target.object_id.",
                errors=("target.object_id is required.",),
            )
        if parameters:
            return ProviderExecutionValidationResult(
                valid=False,
                reason="plants.record_watering does not accept parameters.",
                errors=("parameters must be empty for plants.record_watering.",),
            )
        try:
            plant = self.engine._require_house().plant(object_id)
        except KeyError:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Unknown semantic plant object ID: {object_id}.",
                errors=(f"Unknown semantic plant object ID: {object_id}.",),
            )
        if not plant.enabled:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Plant '{object_id}' is disabled.",
                errors=("Disabled plants cannot receive watering events.",),
            )
        store = self.engine.plant_watering_history_store
        if not store.loaded or store.load_error is not None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason="Plant watering history is unavailable.",
                errors=(store.load_error or "watering_history_not_loaded",),
            )
        return ProviderExecutionValidationResult(
            valid=True,
            reason=(
                "Semantic plant target and persistent watering history are "
                "valid for canonical execution."
            ),
            technical_capability=self._technical_capability(object_id),
        )

    async def async_execute(
        self,
        *,
        action_id: str,
        target: dict,
        parameters: dict,
        confirmed: bool,
    ) -> ProviderExecutionResult:
        validation = await self.async_validate_execution(
            action_id=action_id,
            target=target,
            parameters=parameters,
            confirmed=confirmed,
        )
        if not validation.valid:
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=validation.reason,
                technical_capability=validation.technical_capability,
                verification_scope="state",
            )
        object_id = target["object_id"]
        before = self.engine.plant_care_snapshot(object_id).as_dict()
        try:
            after = await self.engine.async_record_plant_watering(object_id)
        except Exception as err:  # noqa: BLE001
            return ProviderExecutionResult(
                status="failed",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason="Persistent watering event could not be recorded.",
                error=f"{type(err).__name__}: {err}",
                technical_capability=validation.technical_capability,
                feedback_before=before,
                verification_scope="state",
            )
        async_dispatcher_send(self.hass, SIGNAL_PLANTS_UPDATED)
        return ProviderExecutionResult(
            status="succeeded",
            executed=True,
            command_sent=True,
            feedback_confirmed=True,
            reason=(
                "Watering event was atomically persisted and verified. "
                "Physical watering and soil moisture are not independently "
                "claimed."
            ),
            technical_capability=validation.technical_capability,
            feedback_before=before,
            feedback_after=after,
            feedback_wait_ms=0,
            verification_scope="state",
        )
