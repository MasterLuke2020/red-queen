"""Isolated Home Assistant synthetic test of Red Queen semantic light sources.

Executed inside the CI HA image. No PLC, credentials or physical services.
"""
from __future__ import annotations

import asyncio
from collections import deque
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import sys

sys.path.insert(0, "/config")
from homeassistant.exceptions import HomeAssistantError
from custom_components.red_queen import smart_living_runtime as runtime_module
from custom_components.red_queen.smart_lighting_semantic import (
    semantic_light_unique_id, resolve_semantic_light_bindings,
)
from custom_components.red_queen.smart_living_editor import validate_editor_document

OBJECT = "light.outside.straße_up_down"
ENTITY = "light.hof_vorplatz_red_queen_strasse_up_down"
ENTRY = "synthetic-config-entry"


def registry_entry(entity_id, object_id, *, platform="red_queen", config_entry_id=ENTRY,
                   disabled_by=None):
    return SimpleNamespace(
        entity_id=entity_id, platform=platform,
        unique_id=semantic_light_unique_id(object_id),
        config_entry_id=config_entry_id, disabled_by=disabled_by,
    )


def check_mapping():
    lights = [
        SimpleNamespace(object_id=OBJECT, controllable=True),
        SimpleNamespace(object_id="light.house.uncontrolled", controllable=False),
    ]
    entries = [
        registry_entry(ENTITY, OBJECT),
        registry_entry("light.wnhf_disabled", OBJECT, disabled_by="user"),
        registry_entry("light.wnhf_other", OBJECT, config_entry_id="other"),
        registry_entry("light.asyncua_proxy", OBJECT, platform="asyncua"),
        registry_entry("light.wnhf_uncontrollable", "light.house.uncontrolled"),
    ]
    resolved = resolve_semantic_light_bindings(entries, lights, ENTRY)
    assert resolved == {ENTITY: OBJECT}, resolved
    assert semantic_light_unique_id(OBJECT) == "wnhf_outside_straße_up_down"
    # User-defined HA entity IDs remain valid even without the wnhf_ prefix.
    renamed = registry_entry("light.aussen_strasse", OBJECT)
    assert resolve_semantic_light_bindings([renamed], lights, ENTRY) == {
        "light.aussen_strasse": OBJECT,
    }
    # Duplicate object slugs must not become ambiguous bindings.
    colliding = [
        SimpleNamespace(object_id="light.a.b_c", controllable=True),
        SimpleNamespace(object_id="light.a_b.c", controllable=True),
    ]
    assert not resolve_semantic_light_bindings(
        [registry_entry("light.ambiguous", "light.a.b_c")], colliding, ENTRY,
    )
    # Bad/missing entity ID cannot be used to invoke arbitrary actions.
    assert not resolve_semantic_light_bindings(
        [registry_entry("switch.a", OBJECT)], lights, ENTRY,
    )
    print("PASS: strict canonical unique ID mapping; renamed entities supported")


async def check_dispatch():
    fake_state = SimpleNamespace(
        state="off",
        attributes={"supported_color_modes": ["onoff"]},
    )
    calls = []

    class FakeServices:
        def has_service(self, domain, service):
            return domain == "light" and service in {"turn_on", "turn_off"}

        async def async_call(self, *args, **kwargs):
            calls.append(("raw_service", args, kwargs))
            raise AssertionError("Canonical Red Queen source must not route via light proxy")

    fake_hass = SimpleNamespace(
        states=SimpleNamespace(
            get=lambda entity_id:fake_state if entity_id==ENTITY else None,
        ),
        services=FakeServices(),
    )
    runtime = runtime_module.SmartLivingRuntime.__new__(
        runtime_module.SmartLivingRuntime
    )
    runtime.hass = fake_hass
    runtime.rgbw_targets = {}
    runtime.semantic_targets = {ENTITY:OBJECT}
    runtime._target_locks = {}
    runtime.audit = deque(maxlen=100)
    assert ENTITY in runtime.scene_targets

    async def canonical(_hass, *, action_id, object_id):
        calls.append(("canonical", action_id, object_id))
        return {"state":"succeeded"}

    with patch.object(runtime_module, "async_execute_canonical", canonical):
        await runtime.async_light_dispatch(ENTITY, "turn_on", {})
        assert calls == [("canonical", "lighting.turn_on", OBJECT)], calls
        fake_state.state = "on"
        await runtime.async_light_dispatch(ENTITY, "turn_off", {})
        assert calls[-1] == ("canonical", "lighting.turn_off", OBJECT)
        assert len(runtime.audit) == 2
        # No dangerous brightness or RGBW channel writes to PLC-semantic lights.
        for attrs in (
            {"brightness": 200}, {"rgb_color":[255,0,0]},
            {"rgbw_color":[0,0,0,255]},
        ):
            try:
                await runtime.async_light_dispatch(ENTITY, "turn_on", attrs)
            except HomeAssistantError:
                pass
            else:
                raise AssertionError(f"Semantic color/brightness allowed: {attrs}")
        assert len(calls) == 2

        try:
            await runtime.async_light_dispatch("light.wnhf_unknown", "turn_on", {})
        except HomeAssistantError:
            pass
        else:
            raise AssertionError("Unregistered source allowed")
        assert len(calls) == 2

    scenes = [{
        "id": "aussen_licht", "name":"Außenlicht",
        "lights": {ENTITY: {"state": "on"}},
    }]
    rules = [{
        "id":"aussen_um_23","name":"Aus um 23",
        "scene_id":"aussen_licht", "action":"off", "enabled":False,
        "trigger":{"type":"time", "at":"23:00"},
    }]
    parsed_scene, parsed_rules = validate_editor_document(
        scenes, rules, {ENTITY}, require_sources=True,
    )
    assert ENTITY in parsed_scene["aussen_licht"]["lights"]
    assert "aussen_um_23" in parsed_rules
    print("PASS: canonical ON/OFF dispatch only; color/brightness rejected")


async def main():
    check_mapping()
    await check_dispatch()
    print("PASS: HA synthetic semantic light staging; no hardware touched")


if __name__ == "__main__":
    asyncio.run(main())
