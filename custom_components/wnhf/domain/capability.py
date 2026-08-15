"""Capability and provider abstractions for WNHF."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Protocol


class CapabilityState(StrEnum):
    UNSUPPORTED = "unsupported"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    HEALTHY = "healthy"


class CapabilityKind(StrEnum):
    MONITOR = "monitor"
    ACTION = "action"


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    capability_id: str
    domain_id: str
    operation: str
    kind: CapabilityKind
    description: str
    requires_command: bool
    requires_feedback: bool
    confirmation_recommended: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "domain_id": self.domain_id,
            "operation": self.operation,
            "kind": self.kind.value,
            "description": self.description,
            "requires_command": self.requires_command,
            "requires_feedback": self.requires_feedback,
            "confirmation_recommended": self.confirmation_recommended,
        }


@dataclass(frozen=True, slots=True)
class ObjectCapability:
    object_id: str
    object_type: str
    room_id: str
    capability_id: str
    supported: bool
    enabled: bool
    command_entity_ids: tuple[str, ...]
    feedback_entity_ids: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "room_id": self.room_id,
            "capability_id": self.capability_id,
            "supported": self.supported,
            "enabled": self.enabled,
            "command_entity_ids": list(self.command_entity_ids),
            "feedback_entity_ids": list(self.feedback_entity_ids),
            "reason": self.reason,
        }


class CapabilityCatalog:
    VERSION = "1.0"

    def __init__(self, definitions: Iterable[CapabilityDefinition] = ()) -> None:
        self._definitions: dict[str, CapabilityDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: CapabilityDefinition) -> None:
        if definition.capability_id in self._definitions:
            raise ValueError(
                f"Capability definition already registered: "
                f"{definition.capability_id}"
            )
        self._definitions[definition.capability_id] = definition

    def replace(self, definition: CapabilityDefinition) -> None:
        self._definitions[definition.capability_id] = definition

    def get(self, capability_id: str) -> CapabilityDefinition | None:
        return self._definitions.get(capability_id)

    def contains(self, capability_id: str) -> bool:
        return capability_id in self._definitions

    def definitions(self) -> tuple[CapabilityDefinition, ...]:
        return tuple(
            self._definitions[key] for key in sorted(self._definitions)
        )

    def as_dict(self) -> dict[str, Any]:
        definitions = self.definitions()
        return {
            "catalog_version": self.VERSION,
            "count": len(definitions),
            "monitor_count": sum(
                item.kind == CapabilityKind.MONITOR for item in definitions
            ),
            "action_count": sum(
                item.kind == CapabilityKind.ACTION for item in definitions
            ),
            "domains": sorted({item.domain_id for item in definitions}),
            "definitions": [item.as_dict() for item in definitions],
        }

    @classmethod
    def builtin(cls) -> "CapabilityCatalog":
        m = CapabilityKind.MONITOR
        a = CapabilityKind.ACTION
        return cls((
            CapabilityDefinition("lighting.monitor_state", "lighting", "monitor_state", m, "Read lighting state.", False, True),
            CapabilityDefinition("lighting.turn_on", "lighting", "turn_on", a, "Set light on.", True, True),
            CapabilityDefinition("lighting.turn_off", "lighting", "turn_off", a, "Set light off.", True, True),
            CapabilityDefinition("lighting.toggle", "lighting", "toggle", a, "Send guarded toggle pulse.", True, True),
            CapabilityDefinition("access.monitor_open_state", "access", "monitor_open_state", m, "Read opening state.", False, True),
            CapabilityDefinition("access.monitor_lock_state", "access", "monitor_lock_state", m, "Read lock state.", False, True),
            CapabilityDefinition("access.monitor_garage_state", "access", "monitor_garage_state", m, "Derive garage state.", False, True),
            CapabilityDefinition("access.lock", "access", "lock", a, "Lock motorized door.", True, True, True),
            CapabilityDefinition("access.unlock", "access", "unlock", a, "Unlock motorized door.", True, True, True),
            CapabilityDefinition("access.door_open", "access", "door_open", a, "Activate door opener.", True, False, True),
            CapabilityDefinition("access.toggle", "access", "toggle", a, "Send garage OSC pulse.", True, True, True),
            CapabilityDefinition("access.stop", "access", "stop", a, "Stop garage movement.", True, True, True),
            CapabilityDefinition("covers.monitor_state", "covers", "monitor_state", m, "Read cover movement/end state.", False, True),
            CapabilityDefinition("covers.open", "covers", "open", a, "Open cover.", True, True),
            CapabilityDefinition("covers.close", "covers", "close", a, "Close cover.", True, True),
            CapabilityDefinition("covers.blades_open", "covers", "blades_open", a, "Open slats.", True, True),
            CapabilityDefinition("covers.blades_close", "covers", "blades_close", a, "Close slats.", True, True),
        ))


@dataclass(frozen=True, slots=True)
class CapabilitySnapshot:
    capability_id: str
    provider_id: str | None
    supported: bool
    available: bool
    healthy: bool
    state: CapabilityState
    message: str
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "provider_id": self.provider_id,
            "supported": self.supported,
            "available": self.available,
            "healthy": self.healthy,
            "state": self.state.value,
            "message": self.message,
            "details": self.details,
        }


class CapabilityProvider(Protocol):
    provider_id: str
    capability_id: str
    def snapshot(self) -> CapabilitySnapshot: ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, CapabilityProvider] = {}

    def register(self, provider: CapabilityProvider) -> None:
        key = provider.capability_id
        if key in self._providers:
            raise ValueError(f"Capability provider already registered: {key}")
        self._providers[key] = provider

    def replace(self, provider: CapabilityProvider) -> None:
        self._providers[provider.capability_id] = provider

    def get(self, capability_id: str) -> CapabilityProvider | None:
        return self._providers.get(capability_id)

    def contains(self, capability_id: str) -> bool:
        return capability_id in self._providers

    def snapshots(self) -> dict[str, CapabilitySnapshot]:
        return {
            capability_id: provider.snapshot()
            for capability_id, provider in self._providers.items()
        }

    def provider_ids(self) -> tuple[str, ...]:
        return tuple(
            provider.provider_id for provider in self._providers.values()
        )

    def provider_instances(self) -> tuple[CapabilityProvider, ...]:
        """Return registered providers in stable capability order."""
        return tuple(
            self._providers[key]
            for key in sorted(self._providers)
        )
