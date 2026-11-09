"""Persistent user-facing Smart Lighting scene/rule editor state.

The configurator owns a separate Home Assistant Store. Original legacy YAML
remains untouched, is used until the first explicit save, and remains as the
recovery baseline. Never invoke a light service while editing.
"""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.storage import Store

from .smart_living_logic import parse_scenes
from .smart_living_automation_logic import parse_automation_rules

EDITOR_VERSION = 1
EDITOR_STORAGE_KEY = "wnhf.smart_lighting_editor"
MAX_SCENES = 80
MAX_LIGHTS_PER_SCENE = 32


def scenes_to_raw(scenes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert parsed 1.1 scenes to user-editable, serializable YAML shape."""
    result: list[dict[str, Any]] = []
    for scene in scenes.values():
        result.append({
            "id": scene["id"],
            "name": scene["name"],
            "lights": {
                entity_id: {"state": item["state"], **dict(item["attributes"])}
                for entity_id, item in scene["lights"].items()
            },
        })
    return result


def rules_to_raw(rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": rule["id"],
            "name": rule["name"],
            "enabled": rule["enabled"],
            "scene_id": rule["scene_id"],
            "action": rule["action"],
            "trigger": dict(rule["trigger"]),
            "allowed_modes": list(rule["allowed_modes"]),
            "allow_quiet": rule["allow_quiet"],
        }
        for rule in rules.values()
    ]


def validate_editor_document(
    scenes_raw: Any,
    rules_raw: Any,
    approved_sources: set[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(scenes_raw, list) or len(scenes_raw) > MAX_SCENES:
        raise ValueError("Too many Smart Lighting scenes")
    scenes = parse_scenes(scenes_raw)
    if any(len(scene["lights"]) > MAX_LIGHTS_PER_SCENE for scene in scenes.values()):
        raise ValueError("Scene exceeds maximum target count")
    # Every GUI-managed scene must target a source already safely approved by
    # the current integration runtime. No recursive WNHF/Red Queen proxies.
    for scene in scenes.values():
        if set(scene["lights"]) - approved_sources:
            raise ValueError(
                "Scene refers to a non-approved light: "
                + ", ".join(sorted(set(scene["lights"]) - approved_sources))
            )
    rules = parse_automation_rules(rules_raw, scenes)
    return scenes, rules


class SmartLightingEditorStore:
    """Transactional persist/load with a one-version rollback snapshot."""

    def __init__(self, hass) -> None:
        self._store = Store(hass, EDITOR_VERSION, EDITOR_STORAGE_KEY)

    async def async_load(self) -> dict[str, Any] | None:
        stored = await self._store.async_load()
        if stored is None:
            return None
        if not isinstance(stored, dict) or (
            stored.get("schema") != EDITOR_VERSION
            or not isinstance(stored.get("scenes"), list)
            or not isinstance(stored.get("automations"), list)
        ):
            raise ValueError("Invalid stored Smart Lighting editor document")
        return stored

    async def async_save(
        self,
        scenes_raw: list[dict[str, Any]],
        rules_raw: list[dict[str, Any]],
        approved_sources: set[str],
    ) -> None:
        validate_editor_document(scenes_raw, rules_raw, approved_sources)
        previous = await self.async_load()
        snapshot = (
            {
                "scenes": previous["scenes"],
                "automations": previous["automations"],
            } if previous is not None else None
        )
        await self._store.async_save({
            "schema": EDITOR_VERSION,
            "scenes": scenes_raw,
            "automations": rules_raw,
            "previous": snapshot,
        })
