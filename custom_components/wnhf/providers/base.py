"""Stable provider contract for modular WNHF providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Any

from homeassistant.core import HomeAssistant

from ..domain.capability import CapabilitySnapshot
from .execution import ProviderExecutionResult, ProviderExecutionValidationResult


_PROVIDER_ID_PATTERN = re.compile(
    r"^provider\.[a-z0-9_]+(?:\.[a-z0-9_]+)+$"
)
_CAPABILITY_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$"
)
_SEMVER_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$"
)


class ProviderContractError(ValueError):
    """Raised when a provider violates the public provider contract."""


class ProviderKind(StrEnum):
    """Origin and ownership of one provider."""

    CORE = "core"
    VENDOR = "vendor"
    EXTERNAL = "external"


class ProviderLifecycleState(StrEnum):
    """Current provider lifecycle state."""

    CREATED = "created"
    LOADED = "loaded"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNLOADED = "unloaded"


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    """Stable discovery metadata for one provider."""

    provider_id: str
    provider_version: str
    contract_version: str
    name: str
    kind: ProviderKind
    module: str
    class_name: str
    discoverable: bool
    priority: int
    supported_capabilities: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable metadata snapshot."""
        return {
            "provider_id": self.provider_id,
            "provider_version": self.provider_version,
            "contract_version": self.contract_version,
            "name": self.name,
            "kind": self.kind.value,
            "module": self.module,
            "class_name": self.class_name,
            "discoverable": self.discoverable,
            "priority": self.priority,
            "supported_capabilities": list(
                self.supported_capabilities
            ),
        }


@dataclass(frozen=True, slots=True)
class ProviderRuntimeState:
    """Generic runtime health independent of a device type."""

    loaded: bool
    available: bool
    healthy: bool
    lifecycle_state: ProviderLifecycleState
    runtime_validated: bool
    last_error: str | None
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable runtime snapshot."""
        return {
            "loaded": self.loaded,
            "available": self.available,
            "healthy": self.healthy,
            "lifecycle_state": self.lifecycle_state.value,
            "runtime_validated": self.runtime_validated,
            "last_error": self.last_error,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class ProviderDiagnostic:
    """Combined provider contract and runtime diagnostic."""

    metadata: ProviderMetadata
    runtime: ProviderRuntimeState
    contract_valid: bool
    contract_errors: tuple[str, ...]
    qualification: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable diagnostic."""
        return {
            "metadata": self.metadata.as_dict(),
            "runtime": self.runtime.as_dict(),
            "contract": {
                "valid": self.contract_valid,
                "errors": list(self.contract_errors),
            },
            "qualification": self.qualification,
        }


class WNHFProvider(ABC):
    """Stable base contract for every future WNHF provider.

    WP-4.5.1 introduces the contract only. Discovery and registry selection
    are intentionally implemented in later Work Packages.
    """

    CONTRACT_VERSION = "1.0"
    provider_version = "1.0.0"
    provider_kind = ProviderKind.CORE
    provider_name: str | None = None
    discoverable = True
    priority = 100

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        self.hass = hass
        self._loaded = True
        self._last_error: str | None = None

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Return the globally unique stable provider ID."""

    @abstractmethod
    def supported_capabilities(self) -> tuple[str, ...]:
        """Return stable semantic capability IDs supplied by the provider."""

    @abstractmethod
    def snapshot(self) -> CapabilitySnapshot:
        """Return the existing capability-level health snapshot."""

    async def async_setup(self) -> None:
        """Initialize the provider before registration."""
        self._loaded = True
        self._last_error = None

    async def async_unload(self) -> None:
        """Unload provider-owned runtime resources."""
        self._loaded = False

    def resolve(
        self,
        *,
        capability_id: str,
        object_id: str | None = None,
    ) -> Any | None:
        """Resolve a provider-specific execution binding.

        The default intentionally returns ``None``. Existing snapshot
        providers do not yet participate in execution dependency injection.
        """
        return None

    async def async_validate_execution(
        self,
        *,
        action_id: str,
        target: dict[str, Any],
        parameters: dict[str, Any],
        confirmed: bool,
    ) -> ProviderExecutionValidationResult:
        """Validate an execution request without dispatching hardware.

        Providers that expose canonical real execution should override this
        hook. The default remains deliberately non-executing and invalid.
        """
        return ProviderExecutionValidationResult(
            valid=False,
            reason=(
                "Provider does not expose non-mutating canonical execution "
                f"validation for {action_id!r}."
            ),
            errors=("provider_execution_validation_not_implemented",),
        )

    async def async_execute(
        self,
        *,
        action_id: str,
        target: dict[str, Any],
        parameters: dict[str, Any],
        confirmed: bool,
    ) -> ProviderExecutionResult:
        """Execute one semantic action when implemented by this provider.

        The default is deliberately non-executing so newly discovered
        providers cannot mutate hardware merely by being registered.
        """
        return ProviderExecutionResult(
            status="unsupported",
            executed=False,
            command_sent=False,
            feedback_confirmed=False,
            reason=(
                "Provider does not implement generic semantic execution "
                f"for {action_id!r}."
            ),
        )

    def qualification(self) -> dict[str, Any] | None:
        """Return provider-owned qualification metadata when available."""
        return None

    def metadata(self) -> ProviderMetadata:
        """Return stable discovery metadata."""
        name = self.provider_name or type(self).__name__
        return ProviderMetadata(
            provider_id=self.provider_id,
            provider_version=self.provider_version,
            contract_version=self.CONTRACT_VERSION,
            name=name,
            kind=self.provider_kind,
            module=type(self).__module__,
            class_name=type(self).__name__,
            discoverable=self.discoverable,
            priority=self.priority,
            supported_capabilities=self.supported_capabilities(),
        )

    def runtime_state(self) -> ProviderRuntimeState:
        """Derive generic runtime health from the existing snapshot."""
        try:
            snapshot = self.snapshot()
        except Exception as err:  # noqa: BLE001
            self._last_error = f"{type(err).__name__}: {err}"
            return ProviderRuntimeState(
                loaded=self._loaded,
                available=False,
                healthy=False,
                lifecycle_state=ProviderLifecycleState.FAILED,
                runtime_validated=False,
                last_error=self._last_error,
                details={},
            )

        lifecycle = (
            ProviderLifecycleState.LOADED
            if snapshot.healthy
            else ProviderLifecycleState.DEGRADED
        )
        return ProviderRuntimeState(
            loaded=self._loaded,
            available=snapshot.available,
            healthy=snapshot.healthy,
            lifecycle_state=lifecycle,
            runtime_validated=True,
            last_error=self._last_error,
            details={
                "capability_snapshot": snapshot.as_dict(),
            },
        )

    def diagnostics(self) -> ProviderDiagnostic:
        """Return complete provider diagnostics without side effects."""
        errors = validate_provider_contract(self)
        return ProviderDiagnostic(
            metadata=self.metadata(),
            runtime=self.runtime_state(),
            contract_valid=not errors,
            contract_errors=errors,
            qualification=self.qualification(),
        )


def validate_provider_contract(
    provider: WNHFProvider,
) -> tuple[str, ...]:
    """Validate one provider against contract v1.0."""
    errors: list[str] = []

    provider_id = provider.provider_id
    if not _PROVIDER_ID_PATTERN.fullmatch(provider_id):
        errors.append(
            "provider_id must match "
            "'provider.<namespace>.<name>[.<name>...]'."
        )

    if not _SEMVER_PATTERN.fullmatch(provider.provider_version):
        errors.append(
            "provider_version must use semantic versioning x.y.z."
        )

    capabilities = provider.supported_capabilities()
    if not capabilities:
        errors.append(
            "supported_capabilities must contain at least one capability."
        )
    if len(set(capabilities)) != len(capabilities):
        errors.append(
            "supported_capabilities contains duplicate IDs."
        )
    for capability_id in capabilities:
        if not _CAPABILITY_ID_PATTERN.fullmatch(capability_id):
            errors.append(
                "Invalid capability ID "
                f"{capability_id!r}; expected lowercase semantic ID "
                "such as 'lighting' or 'access.lock'."
            )

    metadata = provider.metadata()
    if metadata.provider_id != provider_id:
        errors.append(
            "metadata.provider_id differs from provider.provider_id."
        )
    if metadata.contract_version != provider.CONTRACT_VERSION:
        errors.append(
            "metadata.contract_version differs from provider contract."
        )

    for method_name in (
        "snapshot",
        "resolve",
        "qualification",
        "runtime_state",
        "diagnostics",
        "metadata",
        "async_setup",
        "async_unload",
    ):
        if not callable(getattr(provider, method_name, None)):
            errors.append(
                f"Required provider member is not callable: {method_name}."
            )

    return tuple(errors)


def provider_contract_definition() -> dict[str, Any]:
    """Return the public provider contract definition."""
    return {
        "contract_id": "wnhf.provider",
        "contract_version": WNHFProvider.CONTRACT_VERSION,
        "status": "stable",
        "required_identity": [
            "provider_id",
            "provider_version",
        ],
        "required_methods": [
            "supported_capabilities",
            "snapshot",
            "resolve",
            "qualification",
            "runtime_state",
            "diagnostics",
            "metadata",
            "async_setup",
            "async_unload",
        ],
        "lifecycle_states": [
            item.value for item in ProviderLifecycleState
        ],
        "provider_kinds": [
            item.value for item in ProviderKind
        ],
        "discovery_enabled": True,
        "dependency_injection_enabled": False,
        "note": (
            "Controlled internal discovery is enabled. External entry points "
            "and dependency injection remain disabled."
        ),
    }
