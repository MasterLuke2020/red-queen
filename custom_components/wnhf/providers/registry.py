"""Provider-centric registry for WNHF provider contract v1.0."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .base import (
    ProviderContractError,
    WNHFProvider,
    validate_provider_contract,
)


@dataclass(frozen=True, slots=True)
class ProviderResolution:
    """One deterministic provider-resolution result."""

    capability_id: str
    selected_provider_id: str | None
    candidate_provider_ids: tuple[str, ...]
    resolved: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable resolution."""
        return {
            "capability_id": self.capability_id,
            "selected_provider_id": self.selected_provider_id,
            "candidate_provider_ids": list(
                self.candidate_provider_ids
            ),
            "resolved": self.resolved,
            "reason": self.reason,
        }


class WNHFProviderRegistry:
    """Provider registry indexed by provider ID and capability ID.

    WP-4.5.2 performs deterministic selection by:
    1. healthy providers before unhealthy providers
    2. available providers before unavailable providers
    3. higher provider priority first
    4. provider ID as stable tie-breaker

    Discovery remains disabled. Providers are still created explicitly by
    WNHF core and then registered through this class.
    """

    VERSION = "1.0-stage4.5.2"

    def __init__(self) -> None:
        self._providers: dict[str, WNHFProvider] = {}
        self._capabilities: dict[str, set[str]] = {}
        self._revision = 0

    @property
    def revision(self) -> int:
        """Return registry mutation revision."""
        return self._revision

    def register(self, provider: WNHFProvider) -> None:
        """Register one unique contract-valid provider."""
        errors = validate_provider_contract(provider)
        if errors:
            raise ProviderContractError(
                f"Provider {provider.provider_id!r} violates contract: "
                + "; ".join(errors)
            )

        if provider.provider_id in self._providers:
            raise ValueError(
                "Provider already registered: "
                f"{provider.provider_id}"
            )

        self._providers[provider.provider_id] = provider
        for capability_id in provider.supported_capabilities():
            self._capabilities.setdefault(
                capability_id,
                set(),
            ).add(provider.provider_id)
        self._revision += 1

    def replace(self, provider: WNHFProvider) -> None:
        """Replace one provider by stable provider ID."""
        if provider.provider_id in self._providers:
            self.unregister(provider.provider_id)
        self.register(provider)

    def unregister(
        self,
        provider_id: str,
    ) -> WNHFProvider | None:
        """Remove one provider and all capability-index entries."""
        provider = self._providers.pop(provider_id, None)
        if provider is None:
            return None

        for capability_id in provider.supported_capabilities():
            provider_ids = self._capabilities.get(capability_id)
            if provider_ids is None:
                continue
            provider_ids.discard(provider_id)
            if not provider_ids:
                self._capabilities.pop(capability_id, None)

        self._revision += 1
        return provider

    def get(
        self,
        provider_id: str,
    ) -> WNHFProvider | None:
        """Return one provider by stable ID."""
        return self._providers.get(provider_id)

    def contains(
        self,
        provider_id: str,
    ) -> bool:
        """Return whether one provider ID is registered."""
        return provider_id in self._providers

    def providers(self) -> tuple[WNHFProvider, ...]:
        """Return all providers in stable provider-ID order."""
        return tuple(
            self._providers[key]
            for key in sorted(self._providers)
        )

    def provider_ids(self) -> tuple[str, ...]:
        """Return stable registered provider IDs."""
        return tuple(sorted(self._providers))

    def capability_ids(self) -> tuple[str, ...]:
        """Return all indexed capability IDs."""
        return tuple(sorted(self._capabilities))

    def providers_for_capability(
        self,
        capability_id: str,
    ) -> tuple[WNHFProvider, ...]:
        """Return deterministic candidate order for one capability."""
        provider_ids = self._capabilities.get(
            capability_id,
            set(),
        )
        providers = [
            self._providers[provider_id]
            for provider_id in provider_ids
            if provider_id in self._providers
        ]

        def sort_key(provider: WNHFProvider) -> tuple[Any, ...]:
            runtime = provider.runtime_state()
            return (
                not runtime.healthy,
                not runtime.available,
                -int(provider.priority),
                provider.provider_id,
            )

        return tuple(sorted(providers, key=sort_key))

    def resolve_provider(
        self,
        capability_id: str,
    ) -> WNHFProvider | None:
        """Return the preferred provider for one capability."""
        candidates = self.providers_for_capability(capability_id)
        return candidates[0] if candidates else None

    def resolution(
        self,
        capability_id: str,
    ) -> ProviderResolution:
        """Return explainable provider selection."""
        candidates = self.providers_for_capability(capability_id)
        if not candidates:
            return ProviderResolution(
                capability_id=capability_id,
                selected_provider_id=None,
                candidate_provider_ids=(),
                resolved=False,
                reason=(
                    "No registered provider declares this capability."
                ),
            )

        selected = candidates[0]
        runtime = selected.runtime_state()
        return ProviderResolution(
            capability_id=capability_id,
            selected_provider_id=selected.provider_id,
            candidate_provider_ids=tuple(
                provider.provider_id
                for provider in candidates
            ),
            resolved=True,
            reason=(
                "Selected by health, availability, priority and stable "
                f"provider ID; healthy={runtime.healthy}, "
                f"available={runtime.available}, "
                f"priority={selected.priority}."
            ),
        )

    def resolve(
        self,
        *,
        capability_id: str,
        object_id: str | None = None,
    ) -> Any | None:
        """Resolve a provider-owned execution binding."""
        provider = self.resolve_provider(capability_id)
        if provider is None:
            return None
        return provider.resolve(
            capability_id=capability_id,
            object_id=object_id,
        )

    def snapshots(self) -> dict[str, Any]:
        """Return preferred capability snapshots."""
        result: dict[str, Any] = {}
        for capability_id in self.capability_ids():
            provider = self.resolve_provider(capability_id)
            if provider is not None:
                result[capability_id] = provider.snapshot()
        return result

    def diagnostics(self) -> dict[str, Any]:
        """Return provider- and capability-centric diagnostics."""
        providers = self.providers()
        capabilities: list[dict[str, Any]] = []

        for capability_id in self.capability_ids():
            resolution = self.resolution(capability_id)
            capabilities.append(resolution.as_dict())

        valid = 0
        provider_items: list[dict[str, Any]] = []
        for provider in providers:
            diagnostic = provider.diagnostics().as_dict()
            if diagnostic["contract"]["valid"]:
                valid += 1
            provider_items.append(diagnostic)

        return {
            "api_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "registry_version": self.VERSION,
            "revision": self.revision,
            "summary": {
                "providers": len(providers),
                "capabilities": len(self._capabilities),
                "contract_valid": valid,
                "contract_invalid": len(providers) - valid,
                "all_contracts_valid": valid == len(providers),
                "discovery_enabled": True,
                "dependency_injection_enabled": False,
            },
            "provider_ids": list(self.provider_ids()),
            "capability_ids": list(self.capability_ids()),
            "capabilities": capabilities,
            "providers": provider_items,
        }
