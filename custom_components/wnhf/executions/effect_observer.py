"""Universal optional and required effect observation."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from time import perf_counter
from typing import Any

from .capability import ConfirmationPolicy, EffectConfirmationMode
from .real_step import EffectOutcome, EffectStatus


class EffectObserver:
    """Observe a post-command effect independently from dispatch."""

    VERSION = "1.0-stage4.3.2B.4B"

    @staticmethod
    async def async_observe(
        *,
        policy: ConfirmationPolicy,
        expected: str | None,
        snapshot_factory: Callable[[], Any],
        predicate: Callable[[Any], bool],
        observed_factory: Callable[[Any], str | None],
    ) -> tuple[EffectOutcome, Any]:
        """Observe until the effect is seen or the policy timeout expires."""
        if policy.effect_confirmation == EffectConfirmationMode.NONE:
            snapshot = snapshot_factory()
            return (
                EffectOutcome(
                    status=EffectStatus.NOT_REQUIRED,
                    required=False,
                    expected=expected,
                    observed=observed_factory(snapshot),
                    confirmed=False,
                    wait_ms=0.0,
                    message="Effect observation is disabled by policy.",
                ),
                snapshot,
            )

        started = perf_counter()
        timeout_seconds = max(policy.observe_timeout_ms, 0) / 1000
        interval_seconds = max(policy.observe_interval_ms, 10) / 1000
        deadline = started + timeout_seconds
        snapshot = snapshot_factory()

        while True:
            if predicate(snapshot):
                wait_ms = round((perf_counter() - started) * 1000, 2)
                return (
                    EffectOutcome(
                        status=EffectStatus.CONFIRMED,
                        required=(
                            policy.effect_confirmation
                            == EffectConfirmationMode.REQUIRED
                        ),
                        expected=expected,
                        observed=observed_factory(snapshot),
                        confirmed=True,
                        wait_ms=wait_ms,
                        message="Expected effect was observed.",
                    ),
                    snapshot,
                )

            if perf_counter() >= deadline:
                break

            await asyncio.sleep(interval_seconds)
            snapshot = snapshot_factory()

        wait_ms = round((perf_counter() - started) * 1000, 2)
        required = (
            policy.effect_confirmation
            == EffectConfirmationMode.REQUIRED
        )
        return (
            EffectOutcome(
                status=(
                    EffectStatus.FAILED
                    if required
                    else EffectStatus.NOT_OBSERVED
                ),
                required=required,
                expected=expected,
                observed=observed_factory(snapshot),
                confirmed=False,
                wait_ms=wait_ms,
                message=(
                    "Required effect was not observed before timeout."
                    if required
                    else "Optional effect was not observed before timeout."
                ),
            ),
            snapshot,
        )
