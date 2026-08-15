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

    VERSION = "1.1-rc2-lighting-bidirectional"
    _LIGHTING_ACTIONS = {
        "lighting.turn_on": True,
        "lighting.turn_off": False,
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
