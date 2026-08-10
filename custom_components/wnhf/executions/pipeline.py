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

    VERSION = "1.0-stage3.4"

    @staticmethod
    def validate_guarded_step(step) -> tuple[bool, str]:
        """Validate one supported guarded momentary step."""
        capability = step.capability
        command = capability.get("command") or {}
        valid = (
            capability.get("capability_id") == "lighting.turn_off"
            and capability.get("supported") is True
            and capability.get("available") is True
            and capability.get("healthy") is True
            and capability.get("strategy") == "guarded_momentary_pulse"
            and command.get("domain") == "button"
            and command.get("service") == "press"
            and command.get("entity_id") == step.command_entity_id
        )
        if valid:
            return True, "Guarded step is supported by the pipeline."
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
        """Execute exactly one guarded step and verify off feedback."""
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

            if snapshot_before.is_off:
                return PipelineStepResult(
                    state="skipped",
                    command_sent=False,
                    executed=False,
                    feedback_confirmed=False,
                    feedback_before=feedback_before,
                    feedback_after=None,
                    feedback_wait_ms=0.0,
                    reason="Object already reports off; no command sent.",
                    error=None,
                )

            if not snapshot_before.is_on:
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
                if snapshot_after.available and snapshot_after.is_off:
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
                    reason="Command sent and off feedback confirmed.",
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
                    "Command sent, but off feedback was not confirmed "
                    "before timeout."
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
