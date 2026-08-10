"""Built-in WNHF providers and stable provider contract."""

from .base import (
    ProviderContractError,
    ProviderDiagnostic,
    ProviderKind,
    ProviderLifecycleState,
    ProviderMetadata,
    ProviderRuntimeState,
    WNHFProvider,
    provider_contract_definition,
    validate_provider_contract,
)

from .core import (
    CoversCapabilityProvider,
    LightingCapabilityProvider,
    OpeningsCapabilityProvider,
    SecurityCapabilityProvider,
    ValidatorCapabilityProvider,
)

__all__ = [
    "ProviderExecutionResult",
    "ProviderDiagnosticsContext",
    "UnifiedProviderDiagnostics",
    "DiscoveredProvider",
    "DiscoveryIssue",
    "ProviderDiscovery",
    "ProviderResolution",
    "WNHFProviderRegistry",
    "ProviderContractError",
    "ProviderDiagnostic",
    "ProviderKind",
    "ProviderLifecycleState",
    "ProviderMetadata",
    "ProviderRuntimeState",
    "WNHFProvider",
    "provider_contract_definition",
    "validate_provider_contract",
    "CoversCapabilityProvider",
    "LightingCapabilityProvider",
    "OpeningsCapabilityProvider",
    "SecurityCapabilityProvider",
    "ValidatorCapabilityProvider",
]


from .registry import (
    ProviderResolution,
    WNHFProviderRegistry,
)


from .discovery import (
    DiscoveredProvider,
    DiscoveryIssue,
    ProviderDiscovery,
)


from .diagnostics import (
    ProviderDiagnosticsContext,
    UnifiedProviderDiagnostics,
)


from .execution import ProviderExecutionResult
