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
    GarageCapabilityProvider,
    LightingCapabilityProvider,
    OpeningsCapabilityProvider,
    SecurityCapabilityProvider,
    ValidatorCapabilityProvider,
)
from .plants import PlantsCapabilityProvider

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
    "GarageCapabilityProvider",
    "LightingCapabilityProvider",
    "OpeningsCapabilityProvider",
    "SecurityCapabilityProvider",
    "ValidatorCapabilityProvider",
    "PlantsCapabilityProvider",
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
