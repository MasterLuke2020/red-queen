"""Read-only configuration/provider diagnostics for Red Queen commissioning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


CONFIGURATION_DIAGNOSTICS_CONTRACT_VERSION = "1.0"

_REGISTRY_OBJECT_FILES: dict[str, tuple[str, str]] = {
    "rooms": ("rooms.yaml", "rooms"),
    "lights": ("lights.yaml", "lights"),
    "covers": ("covers.yaml", "covers"),
    "openings": ("openings.yaml", "openings"),
    "plants": ("plants.yaml", "plants"),
}


@dataclass(frozen=True, slots=True)
class ConfiguredEntityIssue:
    """One configured entity reference that is not runtime-ready."""

    object_type: str
    object_id: str
    object_name: str
    role: str
    entity_id: str
    status: str
    platform: str | None
    state: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "object_name": self.object_name,
            "role": self.role,
            "entity_id": self.entity_id,
            "status": self.status,
            "platform": self.platform,
            "state": self.state,
        }


@dataclass(frozen=True, slots=True)
class ConfigurationDiagnosticsReport:
    """Compact commissioning/runtime diagnostic result."""

    contract_version: str
    total_references: int
    ready_references: int
    missing_references: int
    disabled_references: int
    unavailable_references: int
    unknown_references: int
    state_missing_references: int
    skipped_disabled_objects: int
    issues: tuple[ConfiguredEntityIssue, ...]

    @property
    def problem_count(self) -> int:
        return len(self.issues)

    @property
    def healthy(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "healthy": self.healthy,
            "total_references": self.total_references,
            "ready_references": self.ready_references,
            "problem_count": self.problem_count,
            "missing_references": self.missing_references,
            "disabled_references": self.disabled_references,
            "unavailable_references": self.unavailable_references,
            "unknown_references": self.unknown_references,
            "state_missing_references": self.state_missing_references,
            "skipped_disabled_objects": self.skipped_disabled_objects,
            "issues": [issue.as_dict() for issue in self.issues],
        }


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _load_registry_objects(
    registry_dir: Path,
) -> tuple[tuple[str, dict[str, Any]], ...]:
    """Load registry objects using blocking file I/O in an executor thread."""
    objects: list[tuple[str, dict[str, Any]]] = []
    for object_type, (filename, root_key) in _REGISTRY_OBJECT_FILES.items():
        document = _load_yaml(registry_dir / filename)
        entries = document.get(root_key)
        if not isinstance(entries, list):
            continue
        for item in entries:
            if isinstance(item, dict):
                objects.append((object_type, item))
    return tuple(objects)


def _iter_entity_refs(
    node: Any,
    *,
    path: tuple[str, ...] = (),
) -> Iterable[tuple[str, str]]:
    """Yield configured entity ids and skip explicitly disabled submodules."""
    if isinstance(node, dict):
        if node.get("enabled") is False:
            return
        for key, value in node.items():
            key_text = str(key)
            next_path = (*path, key_text)
            if (
                isinstance(value, str)
                and value
                and (key_text == "entity_id" or key_text.endswith("_entity_id"))
            ):
                yield ".".join(next_path), value
            else:
                yield from _iter_entity_refs(value, path=next_path)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_entity_refs(value, path=(*path, str(index)))


def _entity_status(
    hass: HomeAssistant,
    registry: er.EntityRegistry,
    entity_id: str,
) -> tuple[str, str | None, str | None]:
    """Classify one explicit configured entity reference on HA's event loop."""
    entry = registry.async_get(entity_id)
    platform = str(entry.platform) if entry is not None and entry.platform else None

    if entry is not None and entry.disabled_by is not None:
        state = hass.states.get(entity_id)
        return "disabled", platform, state.state if state is not None else None

    state = hass.states.get(entity_id)
    if entry is None and state is None:
        return "missing", None, None
    if state is None:
        return "state_missing", platform, None
    if state.state == STATE_UNAVAILABLE:
        return "unavailable", platform, state.state

    domain = entity_id.partition(".")[0]
    if state.state == STATE_UNKNOWN and domain != "button":
        return "unknown", platform, state.state

    return "ready", platform, state.state


async def async_diagnose_configured_entities(
    hass: HomeAssistant,
    registry_dir: Path,
) -> ConfigurationDiagnosticsReport:
    """Inspect configured references without blocking the HA event loop."""
    loaded_objects = await hass.async_add_executor_job(
        _load_registry_objects,
        registry_dir,
    )

    entity_registry = er.async_get(hass)
    issues: list[ConfiguredEntityIssue] = []
    counts = {
        "ready": 0,
        "missing": 0,
        "disabled": 0,
        "unavailable": 0,
        "unknown": 0,
        "state_missing": 0,
    }
    total = 0
    skipped_disabled_objects = 0

    for object_type, item in loaded_objects:
        if item.get("enabled") is False:
            skipped_disabled_objects += 1
            continue

        object_id = str(item.get("id") or "<unknown>")
        object_name = str(item.get("name") or object_id)

        for role, entity_id in _iter_entity_refs(item):
            total += 1
            status, platform, state = _entity_status(
                hass,
                entity_registry,
                entity_id,
            )
            counts[status] += 1
            if status == "ready":
                continue
            issues.append(
                ConfiguredEntityIssue(
                    object_type=object_type,
                    object_id=object_id,
                    object_name=object_name,
                    role=role,
                    entity_id=entity_id,
                    status=status,
                    platform=platform,
                    state=state,
                )
            )

    issues.sort(
        key=lambda issue: (
            issue.status,
            issue.object_type,
            issue.object_name.casefold(),
            issue.role,
            issue.entity_id,
        )
    )
    return ConfigurationDiagnosticsReport(
        contract_version=CONFIGURATION_DIAGNOSTICS_CONTRACT_VERSION,
        total_references=total,
        ready_references=counts["ready"],
        missing_references=counts["missing"],
        disabled_references=counts["disabled"],
        unavailable_references=counts["unavailable"],
        unknown_references=counts["unknown"],
        state_missing_references=counts["state_missing"],
        skipped_disabled_objects=skipped_disabled_objects,
        issues=tuple(issues),
    )
