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
    """Auto-discoverable core provider."""

    provider_name = "CoversCapabilityProvider"
    discoverable = True

    def __init__(self, engine) -> None:
        super().__init__(engine, "provider.core.covers", "covers")

    def snapshot(self) -> CapabilitySnapshot:
        house = self.engine._require_house()
        supported = bool(house.covers)
        snapshots = self.engine.cover_snapshots() if supported else []
        required_entities = self.engine.cover_feedback_entities() if supported else set()
        available = supported and all(
            (state := self.engine.hass.states.get(entity_id)) is not None
            and state.state not in {"unknown", "unavailable"}
            for entity_id in required_entities
        )
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
                "moving": sum(1 for item in snapshots if item.is_moving),
                "errors": len(errors),
            },
        )


class OpeningsCapabilityProvider(_BaseProvider):
    """Auto-discoverable core provider."""

    provider_name = "OpeningsCapabilityProvider"
    discoverable = True

    def __init__(self, engine) -> None:
        super().__init__(engine, "provider.core.openings", "openings")

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
