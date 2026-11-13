"""Central semantic execution dispatcher."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionRoute:
    """Resolved internal executor for one semantic action."""

    action: str
    executor: str


class LegacyExecutionManager:
    """Resolve legacy Decision actions to the pre-Stage-4.7 executors.

    This manager is retained only for compatibility with the legacy
    ``wnhf.execute`` Decision-ID service. New semantic execution must use
    :class:`SemanticExecutionManager` through ``wnhf.execution_execute``.
    """

    VERSION = "1.0-stage3.5"

    ROUTES = {
        "lighting.object_off": ExecutionRoute(
            action="lighting.object_off",
            executor="object",
        ),
        "lighting.room_off": ExecutionRoute(
            action="lighting.room_off",
            executor="room",
        ),
        "lighting.all_off": ExecutionRoute(
            action="lighting.all_off",
            executor="house",
        ),
    }

    @classmethod
    def resolve(cls, action: str | None) -> ExecutionRoute | None:
        """Return the qualified executor route for an action."""
        if action is None:
            return None
        return cls.ROUTES.get(action)
