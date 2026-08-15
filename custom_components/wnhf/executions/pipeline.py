"""Shared execution pipeline for guarded technical steps."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class PipelineStepResult:
    """Technical result of one guarded pipeline step."""

    state: str
    command_sent: bool
    executed: bool
    feedback_confirmed: bool
    feedback_before: dict[str, Any] | None
    feedback_after: dict[str, Any] | None
    feedback_wait_ms: float
    reason: str
    error: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "command_sent": self.command_sent,
            "executed": self.executed,
            "feedback_confirmed": self.feedback_confirmed,
            "feedback_before": self.feedback_before,
            "feedback_after": self.feedback_after,
            "feedback_wait_ms": self.feedback_wait_ms,
            "reason": self.reason,
            "error": self.error,
        }


class ExecutionPipeline:
    """Hardware-neutral guarded step validation and dispatch."""

    VERSION = "1.3-rc3-cover-bidirectional"
    _LIGHTING_ACTIONS = {
        "lighting.turn_on": True,
        "lighting.turn_off": False,
    }
    _COVER_ACTIONS = {
        "covers.open": ("open", "opening", "closing"),
        "covers.close": ("closed", "closing", "opening"),
    }

    @classmethod
    def validate_guarded_step(cls, step) -> tuple[bool, str]:
        """Validate one supported guarded momentary lighting step."""
        capability = step.capability
        command = capability.get("command") or {}
        valid = (
            capability.get("capability_id") in cls._LIGHTING_ACTIONS
            and capability.get("supported") is True
            and capability.get("available") is True
            and capability.get("healthy") is True
            and capability.get("strategy") == "guarded_momentary_pulse"
            and command.get("domain") == "button"
            and command.get("service") == "press"
            and command.get("entity_id") == step.command_entity_id
        )
        if valid:
            return True, "Guarded lighting step is supported by the pipeline."
        return False, "Step capability is not permitted by the pipeline."

    @classmethod
    async def async_execute_guarded_step(
        cls,
        *,
        hass,
        step,
        snapshot_reader: Callable[[str], Any],
        feedback_timeout_seconds: float,
        feedback_interval_seconds: float,
    ) -> PipelineStepResult:
        """Execute one guarded lighting step and verify the requested state."""
        valid, validation_reason = cls.validate_guarded_step(step)
        if not valid:
            return PipelineStepResult(
                state="failed",
                command_sent=False,
                executed=False,
                feedback_confirmed=False,
                feedback_before=None,
                feedback_after=None,
                feedback_wait_ms=0.0,
                reason=validation_reason,
                error=None,
            )

        capability = step.capability
        command = capability["command"]
        capability_id = str(capability["capability_id"])
        desired_on = cls._LIGHTING_ACTIONS[capability_id]
        desired_label = "on" if desired_on else "off"

        try:
            snapshot_before = snapshot_reader(step.object_id)
            feedback_before = snapshot_before.as_dict()

            if not snapshot_before.available:
                return PipelineStepResult(
                    state="failed",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=False,
                    feedback_before=feedback_before,
                    feedback_after=None,
                    feedback_wait_ms=0.0,
                    reason="Runtime feedback is unavailable.",
                    error=None,
                )

            already_satisfied = (
                snapshot_before.is_on if desired_on else snapshot_before.is_off
            )
            if already_satisfied:
                return PipelineStepResult(
                    state="skipped",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=False,
                    feedback_before=feedback_before,
                    feedback_after=None,
                    feedback_wait_ms=0.0,
                    reason=(
                        f"Object already reports {desired_label}; "
                        "no command sent."
                    ),
                    error=None,
                )

            opposite_state_confirmed = (
                snapshot_before.is_off if desired_on else snapshot_before.is_on
            )
            if not opposite_state_confirmed:
                return PipelineStepResult(
                    state="failed",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=False,
                    feedback_before=feedback_before,
                    feedback_after=None,
                    feedback_wait_ms=0.0,
                    reason="Runtime feedback is ambiguous.",
                    error=None,
                )

            await hass.services.async_call(
                command["domain"],
                command["service"],
                {"entity_id": command["entity_id"]},
                blocking=True,
            )

            feedback_started = perf_counter()
            deadline = feedback_started + feedback_timeout_seconds
            feedback_after = None
            feedback_confirmed = False

            while True:
                snapshot_after = snapshot_reader(step.object_id)
                feedback_after = snapshot_after.as_dict()
                reached_target = (
                    snapshot_after.is_on
                    if desired_on
                    else snapshot_after.is_off
                )
                if snapshot_after.available and reached_target:
                    feedback_confirmed = True
                    break
                if perf_counter() >= deadline:
                    break
                await asyncio.sleep(feedback_interval_seconds)

            feedback_wait_ms = round(
                (perf_counter() - feedback_started) * 1000,
                2,
            )

            if feedback_confirmed:
                return PipelineStepResult(
                    state="succeeded",
                    command_sent=True,
                    executed=True,
                    feedback_confirmed=True,
                    feedback_before=feedback_before,
                    feedback_after=feedback_after,
                    feedback_wait_ms=feedback_wait_ms,
                    reason=(
                        f"Command sent and {desired_label} feedback confirmed."
                    ),
                    error=None,
                )

            return PipelineStepResult(
                state="failed",
                command_sent=True,
                executed=True,
                feedback_confirmed=False,
                feedback_before=feedback_before,
                feedback_after=feedback_after,
                feedback_wait_ms=feedback_wait_ms,
                reason=(
                    f"Command sent, but {desired_label} feedback was not "
                    "confirmed before timeout."
                ),
                error=None,
            )

        except Exception as err:  # noqa: BLE001
            return PipelineStepResult(
                state="failed",
                command_sent=False,
                executed=False,
                feedback_confirmed=False,
                feedback_before=None,
                feedback_after=None,
                feedback_wait_ms=0.0,
                reason="Pipeline step failed with an exception.",
                error=f"{type(err).__name__}: {err}",
            )

    @classmethod
    def validate_guarded_cover_step(cls, step) -> tuple[bool, str]:
        """Validate one supported directional cover step."""
        capability = step.capability
        command = capability.get("command") or {}
        valid = (
            capability.get("capability_id") in cls._COVER_ACTIONS
            and capability.get("supported") is True
            and capability.get("available") is True
            and capability.get("healthy") is True
            and capability.get("strategy") == "guarded_directional_cover_pulse"
            and command.get("domain") == "button"
            and command.get("service") == "press"
            and command.get("entity_id") == step.command_entity_id
        )
        if valid:
            return True, "Guarded directional cover step is supported."
        return False, "Cover step capability is not permitted by the pipeline."

    @classmethod
    async def async_execute_guarded_cover_step(
        cls,
        *,
        hass,
        step,
        snapshot_reader: Callable[[str], Any],
        feedback_timeout_seconds: float,
        feedback_interval_seconds: float,
    ) -> PipelineStepResult:
        """Dispatch one cover direction and confirm movement or target state."""
        valid, validation_reason = cls.validate_guarded_cover_step(step)
        if not valid:
            return PipelineStepResult(
                state="failed",
                command_sent=False,
                executed=False,
                feedback_confirmed=False,
                feedback_before=None,
                feedback_after=None,
                feedback_wait_ms=0.0,
                reason=validation_reason,
                error=None,
            )

        capability = step.capability
        command = capability["command"]
        capability_id = str(capability["capability_id"])
        target_state, moving_state, opposite_moving_state = (
            cls._COVER_ACTIONS[capability_id]
        )

        def state_matches(snapshot, state_name: str) -> bool:
            return str(snapshot.state.value) == state_name

        try:
            snapshot_before = snapshot_reader(step.object_id)
            feedback_before = snapshot_before.as_dict()

            if not snapshot_before.available:
                return PipelineStepResult(
                    state="failed",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=False,
                    feedback_before=feedback_before,
                    feedback_after=None,
                    feedback_wait_ms=0.0,
                    reason="Cover runtime feedback is unavailable.",
                    error=None,
                )

            if snapshot_before.is_error:
                return PipelineStepResult(
                    state="failed",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=False,
                    feedback_before=feedback_before,
                    feedback_after=None,
                    feedback_wait_ms=0.0,
                    reason="Cover feedback is contradictory/error state.",
                    error=None,
                )

            if state_matches(snapshot_before, target_state):
                return PipelineStepResult(
                    state="skipped",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=True,
                    feedback_before=feedback_before,
                    feedback_after=feedback_before,
                    feedback_wait_ms=0.0,
                    reason=(
                        f"Cover already reports {target_state}; no command sent."
                    ),
                    error=None,
                )

            if state_matches(snapshot_before, moving_state):
                return PipelineStepResult(
                    state="in_progress",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=True,
                    feedback_before=feedback_before,
                    feedback_after=feedback_before,
                    feedback_wait_ms=0.0,
                    reason=(
                        f"Cover already reports {moving_state}; no duplicate "
                        "command sent."
                    ),
                    error=None,
                )

            if state_matches(snapshot_before, opposite_moving_state):
                return PipelineStepResult(
                    state="rejected",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=False,
                    feedback_before=feedback_before,
                    feedback_after=feedback_before,
                    feedback_wait_ms=0.0,
                    reason=(
                        f"Cover is currently {opposite_moving_state}; wait for "
                        "a stable state before reversing direction."
                    ),
                    error=None,
                )

            await hass.services.async_call(
                command["domain"],
                command["service"],
                {"entity_id": command["entity_id"]},
                blocking=True,
            )

            feedback_started = perf_counter()
            deadline = feedback_started + feedback_timeout_seconds
            feedback_after = None
            feedback_confirmed = False
            error_detected = False

            while True:
                snapshot_after = snapshot_reader(step.object_id)
                feedback_after = snapshot_after.as_dict()

                if snapshot_after.available and snapshot_after.is_error:
                    error_detected = True
                    break

                reached_effect = (
                    snapshot_after.available
                    and (
                        state_matches(snapshot_after, target_state)
                        or state_matches(snapshot_after, moving_state)
                    )
                )
                if reached_effect:
                    feedback_confirmed = True
                    break
                if perf_counter() >= deadline:
                    break
                await asyncio.sleep(feedback_interval_seconds)

            feedback_wait_ms = round(
                (perf_counter() - feedback_started) * 1000,
                2,
            )

            if feedback_confirmed:
                observed_state = (feedback_after or {}).get("state", "unknown")
                return PipelineStepResult(
                    state="succeeded",
                    command_sent=True,
                    executed=True,
                    feedback_confirmed=True,
                    feedback_before=feedback_before,
                    feedback_after=feedback_after,
                    feedback_wait_ms=feedback_wait_ms,
                    reason=(
                        f"Cover command sent and {observed_state} feedback "
                        "confirmed."
                    ),
                    error=None,
                )

            return PipelineStepResult(
                state="failed",
                command_sent=True,
                executed=True,
                feedback_confirmed=False,
                feedback_before=feedback_before,
                feedback_after=feedback_after,
                feedback_wait_ms=feedback_wait_ms,
                reason=(
                    "Cover command sent, but expected movement/target feedback "
                    "was not confirmed."
                    if not error_detected
                    else "Cover entered a contradictory/error state after command."
                ),
                error=None,
            )

        except Exception as err:  # noqa: BLE001
            return PipelineStepResult(
                state="failed",
                command_sent=False,
                executed=False,
                feedback_confirmed=False,
                feedback_before=None,
                feedback_after=None,
                feedback_wait_ms=0.0,
                reason="Cover pipeline step failed with an exception.",
                error=f"{type(err).__name__}: {err}",
            )

