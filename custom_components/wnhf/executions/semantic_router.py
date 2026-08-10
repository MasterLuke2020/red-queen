"""Semantic execution router for provider-bound dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SemanticRouteResult:
    """Normalized result from semantic provider routing."""

    status: str
    provider_id: str | None
    dispatched: bool
    provider_result: dict[str, Any] | None
    reason: str
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "provider_id": self.provider_id,
            "dispatched": self.dispatched,
            "provider_result": self.provider_result,
            "reason": self.reason,
            "error": self.error,
        }


class SemanticExecutionRouter:
    """Route an already-resolved execution plan to its selected provider."""

    VERSION = "1.0-stage4.7.4"

    def __init__(self, provider_registry: Any) -> None:
        self._provider_registry = provider_registry

    async def async_route(
        self,
        *,
        plan: dict[str, Any],
    ) -> SemanticRouteResult:
        provider_ids = tuple(plan.get("selected_provider_ids", ()))

        if len(provider_ids) != 1:
            return SemanticRouteResult(
                status="rejected",
                provider_id=None,
                dispatched=False,
                provider_result=None,
                reason=(
                    "Semantic route requires exactly one selected provider "
                    "in WP-4.7.4."
                ),
            )

        provider_id = provider_ids[0]
        provider = self._provider_registry.get(provider_id)

        if provider is None:
            return SemanticRouteResult(
                status="rejected",
                provider_id=provider_id,
                dispatched=False,
                provider_result=None,
                reason="Selected provider is no longer registered.",
            )

        try:
            result = await provider.async_execute(
                action_id=str(plan["action_id"]),
                target=dict(plan["target"]),
                parameters=dict(plan["parameters"]),
                confirmed=bool(plan["confirmed"]),
            )
        except Exception as err:  # noqa: BLE001
            return SemanticRouteResult(
                status="failed",
                provider_id=provider_id,
                dispatched=False,
                provider_result=None,
                reason="Provider execution hook raised an exception.",
                error=f"{type(err).__name__}: {err}",
            )

        return SemanticRouteResult(
            status=result.status,
            provider_id=provider_id,
            dispatched=True,
            provider_result=result.as_dict(),
            reason=result.reason,
            error=result.error,
        )
