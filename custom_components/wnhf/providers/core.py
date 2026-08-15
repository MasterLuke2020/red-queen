"""Built-in providers backed by existing WNHF engines."""

from __future__ import annotations


from ..domain.capability import CapabilitySnapshot, CapabilityState
from ..executions.capability import ExecutionCapabilityAdapter
from ..executions.pipeline import ExecutionPipeline
from .execution import ProviderExecutionResult, ProviderExecutionValidationResult
from .base import ProviderKind, WNHFProvider


class _BaseProvider(WNHFProvider):
    """Compatibility base implementing provider contract v1.0."""

    provider_kind = ProviderKind.CORE
    provider_version = "1.0.0"
    discoverable = True
    priority = 100

    def __init__(
        self,
        engine: object,
        provider_id: str,
        capability_id: str,
    ) -> None:
        super().__init__(engine.hass)
        self.engine = engine
        self._provider_id = provider_id
        self.capability_id = capability_id

    @property
    def provider_id(self) -> str:
        """Return stable provider identity."""
        return self._provider_id

    def supported_capabilities(self) -> tuple[str, ...]:
        """Return the capability currently served by this provider."""
        return (self.capability_id,)

    def _snapshot(
        self,
        *,
        supported: bool,
        available: bool,
        healthy: bool,
        message: str,
        details: dict,
    ) -> CapabilitySnapshot:
        if not supported:
            state = CapabilityState.UNSUPPORTED
        elif not available:
            state = CapabilityState.UNAVAILABLE
        elif not healthy:
            state = CapabilityState.DEGRADED
        else:
            state = CapabilityState.HEALTHY

        return CapabilitySnapshot(
            capability_id=self.capability_id,
            provider_id=self.provider_id if supported else None,
            supported=supported,
            available=available,
            healthy=healthy,
            state=state,
            message=message,
            details=details,
        )


class LightingCapabilityProvider(_BaseProvider):
    """Auto-discoverable core provider."""

    provider_name = "LightingCapabilityProvider"
    discoverable = True
    _EXECUTABLE_ACTIONS = {
        "lighting.turn_on",
        "lighting.turn_off",
    }

    def __init__(self, engine) -> None:
        super().__init__(engine, "provider.core.lighting", "lighting")

    @staticmethod
    def _resolve_execution_capability(action_id: str, light, snapshot):
        if action_id == "lighting.turn_on":
            return ExecutionCapabilityAdapter.resolve_light_turn_on(
                light,
                snapshot,
            )
        if action_id == "lighting.turn_off":
            return ExecutionCapabilityAdapter.resolve_light_turn_off(
                light,
                snapshot,
            )
        return None

    async def async_validate_execution(
        self,
        *,
        action_id: str,
        target: dict,
        parameters: dict,
        confirmed: bool,
    ) -> ProviderExecutionValidationResult:
        """Validate canonical lighting execution without dispatching hardware."""
        if action_id not in self._EXECUTABLE_ACTIONS:
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
                reason=f"{action_id} requires target.object_id.",
                errors=("target.object_id is required.",),
            )
        if parameters:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"{action_id} does not accept parameters.",
                errors=(f"parameters must be empty for {action_id}.",),
            )

        try:
            light = self.engine._require_house().light(object_id)
            snapshot = self.engine.light_snapshot(object_id)
            capability = self._resolve_execution_capability(
                action_id,
                light,
                snapshot,
            )
        except KeyError:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Unknown semantic light object ID: {object_id}.",
                errors=(f"Unknown semantic light object ID: {object_id}.",),
            )
        except Exception as err:  # noqa: BLE001
            return ProviderExecutionValidationResult(
                valid=False,
                reason="Lighting execution validation failed.",
                errors=(f"{type(err).__name__}: {err}",),
            )

        if capability is None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"No canonical lighting adapter exists for {action_id}.",
                errors=(f"No canonical lighting adapter exists for {action_id}.",),
            )

        if not (
            capability.supported
            and capability.available
            and capability.healthy
        ):
            return ProviderExecutionValidationResult(
                valid=False,
                reason=capability.reason,
                errors=(capability.reason,),
                technical_capability=capability.as_dict(),
            )

        return ProviderExecutionValidationResult(
            valid=True,
            reason=(
                f"{action_id} target and current technical capability "
                "are valid for canonical execution."
            ),
            technical_capability=capability.as_dict(),
        )

    async def async_execute(
        self,
        *,
        action_id: str,
        target: dict,
        parameters: dict,
        confirmed: bool,
    ) -> ProviderExecutionResult:
        """Execute one qualified canonical lighting action."""
        if action_id not in self._EXECUTABLE_ACTIONS:
            return await super().async_execute(
                action_id=action_id,
                target=target,
                parameters=parameters,
                confirmed=confirmed,
            )

        object_id = target.get("object_id")
        if not isinstance(object_id, str) or not object_id.strip():
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=f"{action_id} requires target.object_id.",
            )

        if parameters:
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=f"{action_id} does not accept parameters.",
            )

        try:
            light = self.engine._require_house().light(object_id)
            snapshot = self.engine.light_snapshot(object_id)
            capability = self._resolve_execution_capability(
                action_id,
                light,
                snapshot,
            )
            if capability is None:
                return ProviderExecutionResult(
                    status="unsupported",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=(
                        f"No canonical lighting adapter exists for {action_id}."
                    ),
                )

            if not (
                capability.supported
                and capability.available
                and capability.healthy
            ):
                return ProviderExecutionResult(
                    status="rejected",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=capability.reason,
                    technical_capability=capability.as_dict(),
                )

            # Minimal step adapter for the qualified guarded lighting pipeline.
            class _Step:
                def __init__(self) -> None:
                    self.object_id = object_id
                    self.command_entity_id = capability.command_entity_id
                    self.capability = capability.as_dict()

            pipeline_result = (
                await ExecutionPipeline.async_execute_guarded_step(
                    hass=self.engine.hass,
                    step=_Step(),
                    snapshot_reader=self.engine.light_snapshot,
                    feedback_timeout_seconds=(
                        capability.confirmation_policy.observe_timeout_ms
                        / 1000.0
                    ),
                    feedback_interval_seconds=(
                        capability.confirmation_policy.observe_interval_ms
                        / 1000.0
                    ),
                )
            )

            if pipeline_result.state == "succeeded":
                status = "succeeded"
                effect_confirmed = True
            elif pipeline_result.state == "skipped":
                # The guarded pipeline skips only when feedback already
                # reports the requested target state.
                status = "no_action"
                effect_confirmed = True
            else:
                status = "failed"
                effect_confirmed = bool(
                    pipeline_result.feedback_confirmed
                )

            return ProviderExecutionResult(
                status=status,
                executed=pipeline_result.executed,
                command_sent=pipeline_result.command_sent,
                feedback_confirmed=effect_confirmed,
                reason=pipeline_result.reason,
                error=pipeline_result.error,
                technical_capability=capability.as_dict(),
                feedback_before=pipeline_result.feedback_before,
                feedback_after=pipeline_result.feedback_after,
                feedback_wait_ms=pipeline_result.feedback_wait_ms,
            )

        except Exception as err:  # noqa: BLE001
            return ProviderExecutionResult(
                status="failed",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason="Lighting provider execution failed.",
                error=f"{type(err).__name__}: {err}",
            )

    def snapshot(self) -> CapabilitySnapshot:
        house = self.engine._require_house()
        supported = bool(house.lights)
        snapshots = self.engine.light_snapshots() if supported else []
        available = supported and all(item.available for item in snapshots)
        healthy = available
        return self._snapshot(
            supported=supported,
            available=available,
            healthy=healthy,
            message=(
                "Lighting available."
                if healthy
                else "Lighting is unavailable or incomplete."
                if supported
                else "Lighting is not configured."
            ),
            details={
                "objects": len(house.lights),
                "enabled": len(house.enabled_lights),
                "available": sum(1 for item in snapshots if item.available),
                "on": sum(1 for item in snapshots if item.is_on),
            },
        )


class CoversCapabilityProvider(_BaseProvider):
    """Auto-discoverable core cover provider."""

    provider_name = "CoversCapabilityProvider"
    discoverable = True
    _EXECUTABLE_ACTIONS = {
        "covers.open",
        "covers.close",
    }

    def __init__(self, engine) -> None:
        super().__init__(engine, "provider.core.covers", "covers")

    @staticmethod
    def _resolve_execution_capability(action_id: str, cover, snapshot):
        if action_id == "covers.open":
            return ExecutionCapabilityAdapter.resolve_cover_open(
                cover,
                snapshot,
            )
        if action_id == "covers.close":
            return ExecutionCapabilityAdapter.resolve_cover_close(
                cover,
                snapshot,
            )
        return None

    @staticmethod
    def _opposite_movement(action_id: str, snapshot) -> bool:
        if action_id == "covers.open":
            return snapshot.is_closing
        if action_id == "covers.close":
            return snapshot.is_opening
        return False

    async def async_validate_execution(
        self,
        *,
        action_id: str,
        target: dict,
        parameters: dict,
        confirmed: bool,
    ) -> ProviderExecutionValidationResult:
        """Validate canonical directional cover execution."""
        if action_id not in self._EXECUTABLE_ACTIONS:
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
                reason=f"{action_id} requires target.object_id.",
                errors=("target.object_id is required.",),
            )
        if parameters:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"{action_id} does not accept parameters.",
                errors=(f"parameters must be empty for {action_id}.",),
            )

        try:
            cover = self.engine._require_house().cover(object_id)
            snapshot = self.engine.cover_snapshot(object_id)
            capability = self._resolve_execution_capability(
                action_id,
                cover,
                snapshot,
            )
        except KeyError:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Unknown semantic cover object ID: {object_id}.",
                errors=(f"Unknown semantic cover object ID: {object_id}.",),
            )
        except Exception as err:  # noqa: BLE001
            return ProviderExecutionValidationResult(
                valid=False,
                reason="Cover execution validation failed.",
                errors=(f"{type(err).__name__}: {err}",),
            )

        if capability is None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"No canonical cover adapter exists for {action_id}.",
                errors=(f"No canonical cover adapter exists for {action_id}.",),
            )

        if not (
            capability.supported
            and capability.available
            and capability.healthy
        ):
            return ProviderExecutionValidationResult(
                valid=False,
                reason=capability.reason,
                errors=(capability.reason,),
                technical_capability=capability.as_dict(),
            )

        if self._opposite_movement(action_id, snapshot):
            return ProviderExecutionValidationResult(
                valid=False,
                reason=(
                    "Cover is currently moving in the opposite direction; "
                    "canonical reversal is intentionally not enabled."
                ),
                errors=(
                    "Wait for a stable cover state before reversing direction.",
                ),
                technical_capability=capability.as_dict(),
            )

        return ProviderExecutionValidationResult(
            valid=True,
            reason=(
                f"{action_id} target and current cover feedback are valid "
                "for canonical execution."
            ),
            technical_capability=capability.as_dict(),
        )

    async def async_execute(
        self,
        *,
        action_id: str,
        target: dict,
        parameters: dict,
        confirmed: bool,
    ) -> ProviderExecutionResult:
        """Execute one qualified canonical directional cover action."""
        if action_id not in self._EXECUTABLE_ACTIONS:
            return await super().async_execute(
                action_id=action_id,
                target=target,
                parameters=parameters,
                confirmed=confirmed,
            )

        object_id = target.get("object_id")
        if not isinstance(object_id, str) or not object_id.strip():
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=f"{action_id} requires target.object_id.",
            )

        if parameters:
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=f"{action_id} does not accept parameters.",
            )

        try:
            cover = self.engine._require_house().cover(object_id)
            snapshot = self.engine.cover_snapshot(object_id)
            capability = self._resolve_execution_capability(
                action_id,
                cover,
                snapshot,
            )

            if capability is None:
                return ProviderExecutionResult(
                    status="unsupported",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=f"No canonical cover adapter exists for {action_id}.",
                )

            if not (
                capability.supported
                and capability.available
                and capability.healthy
            ):
                return ProviderExecutionResult(
                    status="rejected",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=capability.reason,
                    technical_capability=capability.as_dict(),
                )

            if self._opposite_movement(action_id, snapshot):
                return ProviderExecutionResult(
                    status="rejected",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=(
                        "Cover is moving in the opposite direction; wait for "
                        "a stable state before reversing direction."
                    ),
                    technical_capability=capability.as_dict(),
                    feedback_before=snapshot.as_dict(),
                )

            class _Step:
                def __init__(self) -> None:
                    self.object_id = object_id
                    self.command_entity_id = capability.command_entity_id
                    self.capability = capability.as_dict()

            pipeline_result = (
                await ExecutionPipeline.async_execute_guarded_cover_step(
                    hass=self.engine.hass,
                    step=_Step(),
                    snapshot_reader=self.engine.cover_snapshot,
                    feedback_timeout_seconds=(
                        capability.confirmation_policy.observe_timeout_ms
                        / 1000.0
                    ),
                    feedback_interval_seconds=(
                        capability.confirmation_policy.observe_interval_ms
                        / 1000.0
                    ),
                )
            )

            if pipeline_result.state == "succeeded":
                status = "succeeded"
                effect_confirmed = True
            elif pipeline_result.state == "skipped":
                status = "no_action"
                effect_confirmed = True
            elif pipeline_result.state == "in_progress":
                status = "in_progress"
                effect_confirmed = True
            elif pipeline_result.state == "rejected":
                status = "rejected"
                effect_confirmed = False
            else:
                status = "failed"
                effect_confirmed = bool(
                    pipeline_result.feedback_confirmed
                )

            return ProviderExecutionResult(
                status=status,
                executed=pipeline_result.executed,
                command_sent=pipeline_result.command_sent,
                feedback_confirmed=effect_confirmed,
                reason=pipeline_result.reason,
                error=pipeline_result.error,
                technical_capability=capability.as_dict(),
                feedback_before=pipeline_result.feedback_before,
                feedback_after=pipeline_result.feedback_after,
                feedback_wait_ms=pipeline_result.feedback_wait_ms,
            )

        except Exception as err:  # noqa: BLE001
            return ProviderExecutionResult(
                status="failed",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason="Cover provider execution failed.",
                error=f"{type(err).__name__}: {err}",
            )

    def snapshot(self) -> CapabilitySnapshot:
        house = self.engine._require_house()
        supported = bool(house.covers)
        snapshots = self.engine.cover_snapshots() if supported else []
        available = supported and all(item.available for item in snapshots)
        errors = [item for item in snapshots if item.is_error]
        healthy = available and not errors
        return self._snapshot(
            supported=supported,
            available=available,
            healthy=healthy,
            message=(
                "Covers available."
                if healthy
                else "Cover feedback contains errors."
                if errors
                else "Covers are unavailable or incomplete."
                if supported
                else "Covers are not configured."
            ),
            details={
                "objects": len(house.covers),
                "enabled": len(house.enabled_covers),
                "available": sum(1 for item in snapshots if item.available),
                "moving": sum(1 for item in snapshots if item.is_moving),
                "errors": len(errors),
                "canonical_actions": sorted(self._EXECUTABLE_ACTIONS),
                "canonical_blade_execution": False,
            },
        )


class OpeningsCapabilityProvider(_BaseProvider):
    """Auto-discoverable core openings/access provider."""

    provider_name = "OpeningsCapabilityProvider"
    discoverable = True
    _EXECUTABLE_ACTIONS = {
        "openings.lock",
        "openings.unlock",
    }
    _TECHNICAL_ACTIONS = {
        "openings.lock": "access.lock",
        "openings.unlock": "access.unlock",
    }

    def __init__(self, engine) -> None:
        super().__init__(engine, "provider.core.openings", "openings")

    @classmethod
    def _technical_action_id(cls, action_id: str) -> str | None:
        return cls._TECHNICAL_ACTIONS.get(action_id)

    @staticmethod
    def _desired_lock_state(action_id: str) -> str | None:
        if action_id == "openings.lock":
            return "locked"
        if action_id == "openings.unlock":
            return "unlocked"
        return None

    @classmethod
    def _resolve_execution_capability(cls, action_id: str, opening, runtime):
        technical_action_id = cls._technical_action_id(action_id)
        if technical_action_id is None:
            return None
        return ExecutionCapabilityAdapter.resolve(
            opening,
            technical_action_id,
            runtime,
        )

    async def async_validate_execution(
        self,
        *,
        action_id: str,
        target: dict,
        parameters: dict,
        confirmed: bool,
    ) -> ProviderExecutionValidationResult:
        """Validate canonical lock/unlock execution without dispatch."""
        if action_id not in self._EXECUTABLE_ACTIONS:
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
                reason=f"{action_id} requires target.object_id.",
                errors=("target.object_id is required.",),
            )
        if parameters:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"{action_id} does not accept parameters.",
                errors=(f"parameters must be empty for {action_id}.",),
            )
        if not confirmed:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"{action_id} requires explicit confirmation.",
                errors=("confirmed must be true for canonical lock execution.",),
            )

        try:
            opening = self.engine._require_house().openings.get(object_id)
            if opening is None:
                return ProviderExecutionValidationResult(
                    valid=False,
                    reason=f"Unknown semantic opening object ID: {object_id}.",
                    errors=(f"Unknown semantic opening object ID: {object_id}.",),
                )

            runtime = self.engine.access_object_snapshot(object_id)
            capability = self._resolve_execution_capability(
                action_id,
                opening,
                runtime,
            )
        except Exception as err:  # noqa: BLE001
            return ProviderExecutionValidationResult(
                valid=False,
                reason="Openings lock execution validation failed.",
                errors=(f"{type(err).__name__}: {err}",),
            )

        if capability is None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"No canonical openings adapter exists for {action_id}.",
                errors=(f"No canonical openings adapter exists for {action_id}.",),
            )

        if not (
            capability.supported
            and capability.available
            and capability.healthy
        ):
            return ProviderExecutionValidationResult(
                valid=False,
                reason=capability.reason,
                errors=(capability.reason,),
                technical_capability=capability.as_dict(),
            )

        if runtime.is_open:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=(
                    "Door is open; canonical lock/unlock execution is "
                    "intentionally blocked until the door is closed."
                ),
                errors=("Close the door before changing its lock state.",),
                technical_capability=capability.as_dict(),
            )

        if runtime.lock_state not in {"locked", "unlocked"}:
            return ProviderExecutionValidationResult(
                valid=False,
                reason="Door lock feedback is not a valid stable lock state.",
                errors=("Lock feedback must report locked or unlocked.",),
                technical_capability=capability.as_dict(),
            )

        return ProviderExecutionValidationResult(
            valid=True,
            reason=(
                f"{action_id} target, closed-door guard and lock feedback "
                "are valid for canonical execution."
            ),
            technical_capability=capability.as_dict(),
        )

    async def async_execute(
        self,
        *,
        action_id: str,
        target: dict,
        parameters: dict,
        confirmed: bool,
    ) -> ProviderExecutionResult:
        """Execute one confirmed canonical lock/unlock action."""
        if action_id not in self._EXECUTABLE_ACTIONS:
            return await super().async_execute(
                action_id=action_id,
                target=target,
                parameters=parameters,
                confirmed=confirmed,
            )

        object_id = target.get("object_id")
        if not isinstance(object_id, str) or not object_id.strip():
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=f"{action_id} requires target.object_id.",
            )
        if parameters:
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=f"{action_id} does not accept parameters.",
            )
        if not confirmed:
            return ProviderExecutionResult(
                status="rejected",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason=f"{action_id} requires explicit confirmation.",
            )

        try:
            opening = self.engine._require_house().openings.get(object_id)
            if opening is None:
                return ProviderExecutionResult(
                    status="rejected",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=f"Unknown semantic opening object ID: {object_id}.",
                )

            runtime = self.engine.access_object_snapshot(object_id)
            capability = self._resolve_execution_capability(
                action_id,
                opening,
                runtime,
            )
            desired_state = self._desired_lock_state(action_id)

            if capability is None or desired_state is None:
                return ProviderExecutionResult(
                    status="unsupported",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=f"No canonical openings adapter exists for {action_id}.",
                )

            if not (
                capability.supported
                and capability.available
                and capability.healthy
            ):
                return ProviderExecutionResult(
                    status="rejected",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=capability.reason,
                    technical_capability=capability.as_dict(),
                    feedback_before=runtime.as_dict(),
                )

            if runtime.is_open:
                return ProviderExecutionResult(
                    status="rejected",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason=(
                        "Door is open; canonical lock/unlock execution is "
                        "blocked until the door is closed."
                    ),
                    technical_capability=capability.as_dict(),
                    feedback_before=runtime.as_dict(),
                )

            if runtime.lock_state not in {"locked", "unlocked"}:
                return ProviderExecutionResult(
                    status="rejected",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    reason="Door lock feedback is not a valid stable lock state.",
                    technical_capability=capability.as_dict(),
                    feedback_before=runtime.as_dict(),
                )

            if runtime.lock_state == desired_state:
                return ProviderExecutionResult(
                    status="no_action",
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=True,
                    reason=(
                        f"Door already reports {desired_state}; no command sent."
                    ),
                    technical_capability=capability.as_dict(),
                    feedback_before=runtime.as_dict(),
                    feedback_after=runtime.as_dict(),
                    feedback_wait_ms=0.0,
                )

            command_outcome = await self.engine.command_dispatcher.async_dispatch(
                capability
            )
            if not command_outcome.completed:
                return ProviderExecutionResult(
                    status="failed",
                    executed=False,
                    command_sent=bool(command_outcome.dispatched),
                    feedback_confirmed=False,
                    reason=f"{action_id} command dispatch failed.",
                    error=command_outcome.message,
                    technical_capability=capability.as_dict(),
                    feedback_before=runtime.as_dict(),
                )

            effect_outcome, observed_runtime = (
                await self.engine.effect_observer.async_observe(
                    policy=capability.confirmation_policy,
                    expected=desired_state,
                    snapshot_factory=lambda: self.engine.access_object_snapshot(
                        object_id
                    ),
                    predicate=lambda item: (
                        item.available and item.lock_state == desired_state
                    ),
                    observed_factory=lambda item: item.lock_state,
                )
            )

            if effect_outcome.confirmed:
                status = "succeeded"
                reason = (
                    f"{action_id} command sent and {desired_state} feedback "
                    "confirmed."
                )
            else:
                status = "failed"
                reason = (
                    f"{action_id} command was sent, but {desired_state} "
                    "feedback was not confirmed before timeout."
                )

            return ProviderExecutionResult(
                status=status,
                executed=True,
                command_sent=bool(command_outcome.dispatched),
                feedback_confirmed=bool(effect_outcome.confirmed),
                reason=reason,
                technical_capability=capability.as_dict(),
                feedback_before=runtime.as_dict(),
                feedback_after=observed_runtime.as_dict(),
                feedback_wait_ms=effect_outcome.wait_ms,
            )

        except Exception as err:  # noqa: BLE001
            return ProviderExecutionResult(
                status="failed",
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                reason="Openings provider lock execution failed.",
                error=f"{type(err).__name__}: {err}",
            )

    def snapshot(self) -> CapabilitySnapshot:
        house = self.engine._require_house()
        supported = bool(house.openings)
        access = self.engine.access_snapshot() if supported else None
        available = bool(access is not None and access.all_available)
        healthy = bool(
            available
            and access is not None
            and access.garage_error == 0
        )
        return self._snapshot(
            supported=supported,
            available=available,
            healthy=healthy,
            message=(
                "Access runtime available."
                if healthy
                else "Access feedback contains an invalid garage state."
                if access is not None and access.garage_error
                else "Access feedback is unavailable or incomplete."
                if supported
                else "Access is not configured."
            ),
            details=(
                {
                    "objects": access.total,
                    "enabled": access.enabled,
                    "available": access.available,
                    "open": access.open_count,
                    "secure": access.secure,
                    "locked_doors": access.locked_doors,
                    "unlocked_doors": access.unlocked_doors,
                    "garage": {
                        "open": access.garage_open,
                        "closed": access.garage_closed,
                        "moving": access.garage_moving,
                        "intermediate_open": (
                            access.garage_intermediate_open
                        ),
                        "error": access.garage_error,
                    },
                }
                if access is not None
                else {}
            ),
        )


class SecurityCapabilityProvider(_BaseProvider):
    """Auto-discoverable core provider."""

    provider_name = "SecurityCapabilityProvider"
    discoverable = True

    def __init__(self, engine) -> None:
        super().__init__(engine, "provider.core.security", "security")

    def snapshot(self) -> CapabilitySnapshot:
        house = self.engine._require_house()
        supported = bool(house.openings)
        if not supported:
            return self._snapshot(
                supported=False,
                available=False,
                healthy=False,
                message="Security is not configured.",
                details={},
            )

        security = self.engine.security_snapshot()
        openings_provider = OpeningsCapabilityProvider(self.engine).snapshot()
        available = openings_provider.available
        healthy = available
        return self._snapshot(
            supported=True,
            available=available,
            healthy=healthy,
            message=(
                "Security available."
                if healthy
                else "Security source data is unavailable."
            ),
            details={
                "secure": security.secure,
                "alert": security.alert,
                "open_count": security.open_count,
            },
        )


class ValidatorCapabilityProvider(_BaseProvider):
    """Auto-discoverable core provider."""

    provider_name = "ValidatorCapabilityProvider"
    discoverable = True

    def __init__(self, engine) -> None:
        super().__init__(engine, "provider.core.validator", "validator")

    def snapshot(self) -> CapabilitySnapshot:
        report = self.engine.validation_snapshot()
        supported = True
        available = report is not None
        healthy = available and report.valid
        return self._snapshot(
            supported=supported,
            available=available,
            healthy=healthy,
            message=(
                "Validator healthy."
                if healthy
                else "Validator has not run yet."
                if not available
                else "Validator reports errors."
            ),
            details={
                "status": report.status if report is not None else "pending",
                "quality_score": (
                    report.quality_score if report is not None else 0
                ),
                "errors": len(report.errors) if report is not None else 0,
                "warnings": len(report.warnings) if report is not None else 0,
            },
        )
