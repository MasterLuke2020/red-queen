"""Resolve existing native Red Queen light entities to canonical object IDs.

These are NOT arbitrary HA light proxies and NOT RGBW sources. A semantic
light can be used only if it is enabled and controllable in the loaded
Red Queen house registry, and its entity registry unique_id matches the
native WNHFLightEntity convention exactly.
"""
from __future__ import annotations

from typing import Any

from .const import DOMAIN


def semantic_light_unique_id(object_id: str) -> str:
    if not isinstance(object_id, str) or not object_id.startswith("light."):
        raise ValueError("Expected a canonical Red Queen light object ID")
    return "wnhf_" + object_id.removeprefix("light.").replace(".", "_")


def resolve_semantic_light_bindings(
    entries: Any,
    enabled_lights: Any,
    config_entry_id: str,
) -> dict[str, str]:
    """Return HA entity_id -> canonical Red Queen object_id.

    No name matching, no WNHF-prefix assumption in HA entity IDs (users may
    rename them), no source command entity inference, and no arbitrary
    'wnhf_id' state-attribute trust. Ambiguous unique IDs are rejected.
    """
    possible: dict[str, list[str]] = {}
    for light in enabled_lights:
        if not getattr(light, "controllable", False):
            continue
        object_id = getattr(light, "object_id", None)
        if not isinstance(object_id, str):
            continue
        try:
            unique_id = semantic_light_unique_id(object_id)
        except ValueError:
            continue
        possible.setdefault(unique_id, []).append(object_id)
    resolved: dict[str, str] = {}
    for entry in entries:
        entity_id = getattr(entry, "entity_id", None)
        if not isinstance(entity_id, str) or not entity_id.startswith("light."):
            continue
        if getattr(entry, "disabled_by", None) is not None:
            continue
        if getattr(entry, "platform", None) != DOMAIN:
            continue
        if getattr(entry, "config_entry_id", None) != config_entry_id:
            continue
        object_ids = possible.get(getattr(entry, "unique_id", None), [])
        if len(object_ids) == 1:
            resolved[entity_id] = object_ids[0]
    return dict(sorted(resolved.items()))
