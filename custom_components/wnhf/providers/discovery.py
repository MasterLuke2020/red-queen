"""Controlled automatic discovery of WNHF provider classes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import Any

from homeassistant.core import HomeAssistant

from .base import WNHFProvider, validate_provider_contract
from .registry import WNHFProviderRegistry


@dataclass(frozen=True, slots=True)
class DiscoveryIssue:
    """One non-fatal provider-discovery issue."""

    stage: str
    module: str
    class_name: str | None
    error: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "module": self.module,
            "class_name": self.class_name,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class DiscoveredProvider:
    """One provider successfully registered through discovery."""

    provider_id: str
    module: str
    class_name: str
    provider_version: str
    capabilities: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "module": self.module,
            "class_name": self.class_name,
            "provider_version": self.provider_version,
            "capabilities": list(self.capabilities),
        }


class ProviderDiscovery:
    """Discover internal WNHF providers without external entry points."""

    VERSION = "1.1-stage4.7.7.1"

    def __init__(
        self,
        hass: HomeAssistant,
        engine: object,
        registry: WNHFProviderRegistry,
    ) -> None:
        self._hass = hass
        self._engine = engine
        self._registry = registry
        self._discovered: list[DiscoveredProvider] = []
        self._issues: list[DiscoveryIssue] = []
        self._modules_scanned: list[str] = []
        self._completed = False
        self._generated_at: datetime | None = None

    async def async_discover(self) -> None:
        """Scan, instantiate, validate, set up and register providers."""
        self._discovered.clear()
        self._issues.clear()
        self._modules_scanned.clear()
        self._completed = False

        package_name = __package__
        module_names = await self._hass.async_add_executor_job(
            self._discover_module_names,
            package_name,
        )

        for module_name in module_names:
            self._modules_scanned.append(module_name)
            try:
                module = await self._hass.async_add_executor_job(
                    importlib.import_module,
                    module_name,
                )
            except Exception as err:  # noqa: BLE001
                self._issues.append(
                    DiscoveryIssue(
                        stage="import",
                        module=module_name,
                        class_name=None,
                        error=f"{type(err).__name__}: {err}",
                    )
                )
                continue

            for provider_class in self._provider_classes(module):
                await self._async_register_class(
                    module_name,
                    provider_class,
                )

        self._completed = True
        self._generated_at = datetime.now(UTC)

    @classmethod
    def _discover_module_names(
        cls,
        package_name: str,
    ) -> tuple[str, ...]:
        """Perform package import and pkgutil filesystem scan off-loop."""
        package = importlib.import_module(package_name)
        return tuple(
            sorted(
                module_info.name
                for module_info in pkgutil.iter_modules(
                    package.__path__,
                    prefix=f"{package_name}.",
                )
                if cls._module_is_eligible(module_info.name)
            )
        )

    @staticmethod
    def _module_is_eligible(module_name: str) -> bool:
        leaf = module_name.rsplit(".", 1)[-1]
        return (
            leaf not in {
                "__init__",
                "base",
                "registry",
                "discovery",
            }
            and not leaf.startswith("_")
        )

    @staticmethod
    def _provider_classes(
        module: ModuleType,
    ) -> tuple[type[WNHFProvider], ...]:
        result: list[type[WNHFProvider]] = []
        for _, candidate in inspect.getmembers(module, inspect.isclass):
            if candidate is WNHFProvider:
                continue
            if candidate.__module__ != module.__name__:
                continue
            if not issubclass(candidate, WNHFProvider):
                continue
            if inspect.isabstract(candidate):
                continue
            if not bool(getattr(candidate, "discoverable", False)):
                continue
            result.append(candidate)

        return tuple(
            sorted(result, key=lambda item: item.__name__)
        )

    async def _async_register_class(
        self,
        module_name: str,
        provider_class: type[WNHFProvider],
    ) -> None:
        try:
            provider = self._instantiate(provider_class)
        except Exception as err:  # noqa: BLE001
            self._issues.append(
                DiscoveryIssue(
                    stage="instantiate",
                    module=module_name,
                    class_name=provider_class.__name__,
                    error=f"{type(err).__name__}: {err}",
                )
            )
            return

        errors = validate_provider_contract(provider)
        if errors:
            self._issues.append(
                DiscoveryIssue(
                    stage="contract",
                    module=module_name,
                    class_name=provider_class.__name__,
                    error="; ".join(errors),
                )
            )
            return

        try:
            await provider.async_setup()
            self._registry.register(provider)
        except Exception as err:  # noqa: BLE001
            self._issues.append(
                DiscoveryIssue(
                    stage="register",
                    module=module_name,
                    class_name=provider_class.__name__,
                    error=f"{type(err).__name__}: {err}",
                )
            )
            try:
                await provider.async_unload()
            except Exception:
                pass
            return

        self._discovered.append(
            DiscoveredProvider(
                provider_id=provider.provider_id,
                module=module_name,
                class_name=provider_class.__name__,
                provider_version=provider.provider_version,
                capabilities=provider.supported_capabilities(),
            )
        )

    def _instantiate(
        self,
        provider_class: type[WNHFProvider],
    ) -> WNHFProvider:
        signature = inspect.signature(provider_class)
        parameters = tuple(signature.parameters.values())
        names = {
            parameter.name
            for parameter in parameters
            if parameter.kind in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            }
        }

        required = tuple(
            parameter
            for parameter in parameters
            if parameter.default is inspect.Parameter.empty
            and parameter.kind
            in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            }
        )

        if not required:
            return provider_class()
        if names == {"engine"}:
            return provider_class(engine=self._engine)
        if names == {"hass"}:
            return provider_class(hass=self._hass)

        raise TypeError(
            "Discoverable provider constructor must require no argument, "
            "'engine', or 'hass'."
        )

    async def async_unload(self) -> None:
        """Unload providers registered through this discovery instance."""
        for item in reversed(self._discovered):
            provider = self._registry.unregister(item.provider_id)
            if provider is None:
                continue
            try:
                await provider.async_unload()
            except Exception as err:  # noqa: BLE001
                self._issues.append(
                    DiscoveryIssue(
                        stage="unload",
                        module=item.module,
                        class_name=item.class_name,
                        error=f"{type(err).__name__}: {err}",
                    )
                )

    def snapshot(self) -> dict[str, Any]:
        return {
            "api_version": "1.0",
            "discovery_version": self.VERSION,
            "generated_at": (
                self._generated_at.isoformat()
                if self._generated_at is not None
                else None
            ),
            "completed": self._completed,
            "package": __package__,
            "policy": {
                "internal_package_only": True,
                "external_entry_points_enabled": False,
                "recursive_modules": False,
                "contract_validation_required": True,
                "abstract_classes_ignored": True,
                "discoverable_flag_required": True,
                "startup_blocking_errors": False,
            },
            "summary": {
                "modules_scanned": len(self._modules_scanned),
                "providers_discovered": len(self._discovered),
                "issues": len(self._issues),
                "all_discovered_valid": not self._issues,
            },
            "modules_scanned": list(self._modules_scanned),
            "providers": [
                item.as_dict()
                for item in sorted(
                    self._discovered,
                    key=lambda value: value.provider_id,
                )
            ],
            "issues": [
                item.as_dict()
                for item in self._issues
            ],
        }
