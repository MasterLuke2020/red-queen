"""Home Assistant-only synthetic smoke for Smart Lighting options-flow forms.

Run inside an isolated Home Assistant CI container. No network, hardware,
user data, persistent config writes, or physical light service calls.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import sys
from types import SimpleNamespace

sys.path.insert(0, "/config")

from custom_components.red_queen.smart_lighting_options import SmartLightingOptionsMixin
from custom_components.red_queen.smart_living_logic import parse_scenes
from custom_components.red_queen.smart_living_automation_logic import parse_automation_rules
from custom_components.red_queen.smart_living_editor import validate_editor_document

SOURCE = "light.dali_test_rgbw"
SHELLY = "light.shelly_rgbw2_streifen"
ONOFF = "light.shelly_relais"
SCENE = {
    "id": "test_abend", "name": "Test Evening",
    "lights": {SOURCE: {"state": "on", "brightness": 180}},
}
RULE = {
    "id": "test_aus", "name": "Test Off", "enabled": False,
    "scene_id": "test_abend", "action": "off",
    "trigger": {"type": "time", "at": "23:00"},
    "allowed_modes": ["home"], "allow_quiet": False,
}


class FakeEditor:
    def __init__(self):
        self.scenes = [deepcopy(SCENE)]
        self.automations = [deepcopy(RULE)]
        self.save_count = 0

    async def async_save(self, scenes, rules, approved):
        assert SOURCE in approved
        validate_editor_document(scenes, rules, approved)
        self.scenes = deepcopy(scenes)
        self.automations = deepcopy(rules)
        self.save_count += 1


class FakeRuntime:
    def __init__(self):
        self.rgbw_targets = {SOURCE: "Synthetic DALI RGBW"}
        self.semantic_targets = {}
        self.scene_targets = dict(self.rgbw_targets)
        # Candidates are visible for selection, not yet allowed for dispatch.
        self.editor_selectable_targets = {
            **self.scene_targets,
            SHELLY: "Shelly RGBW", ONOFF: "Shelly ONOFF",
        }
        self.editor = FakeEditor()

    def editor_document(self):
        return deepcopy({
            "scenes": self.editor.scenes,
            "automations": self.editor.automations,
        })


class FakeFlow(SmartLightingOptionsMixin):
    def __init__(self):
        self.runtime = FakeRuntime()
        states = {
            SOURCE: SimpleNamespace(
                state="off", attributes={"supported_color_modes": ["rgbw"]},
            ),
            SHELLY: SimpleNamespace(
                state="off", attributes={"supported_color_modes": ["rgbw"]},
            ),
            ONOFF: SimpleNamespace(
                state="off", attributes={"supported_color_modes": ["onoff"]},
            ),
        }
        self.hass = SimpleNamespace(
            data={"red_queen": {"smart_living": self.runtime}},
            states=SimpleNamespace(get=states.get),
        )

    def async_show_form(self, **kwargs):
        schema = kwargs.get("data_schema")
        assert schema is not None, kwargs
        return {"kind": "form", **kwargs}

    def async_show_menu(self, **kwargs):
        assert kwargs["menu_options"]
        return {"kind": "menu", **kwargs}

    def async_abort(self, **kwargs):
        return {"kind": "abort", **kwargs}

    def _finish(self, action):
        return {"kind": "saved", "action": action}


async def main():
    flow = FakeFlow()

    form = await flow.async_step_smart_lighting()
    assert "smart_scenes" in form["menu_options"]
    form = await flow.async_step_smart_scenes()
    assert "smart_scene_pick" in form["menu_options"]
    form = await flow.async_step_smart_scene_add()
    assert form["kind"] == "form"
    form = await flow.async_step_smart_scene_first_light()
    assert form["kind"] == "abort"   # first-light only after starting a scene

    form = await flow.async_step_smart_scene_add({
        "id": "new_scene", "name": "New Scene",
    })
    assert form["kind"] == "form" and form["step_id"] == "smart_scene_first_light"
    form = await flow.async_step_smart_scene_first_light({
        "entity_id": SOURCE, "state": "on", "color_mode": "rgbw",
        "brightness": 180, "red": 0, "green": 0, "blue": 0, "white": 255,
    })
    assert form["kind"] == "saved", form
    assert len(flow.runtime.editor.scenes) == 2
    assert flow.runtime.editor.scenes[1]["lights"][SOURCE][
        "rgbw_color"] == [0, 0, 0, 255]

    form = await flow.async_step_smart_scene_pick()
    assert form["kind"] == "form"
    form = await flow.async_step_smart_scene_pick({"scene_id": "test_abend"})
    assert form["kind"] == "menu"
    form = await flow.async_step_smart_scene_target_pick()
    assert form["kind"] == "form"
    form = await flow.async_step_smart_scene_target_pick({"entity_id": SOURCE})
    assert form["kind"] == "form" and form["step_id"] == "smart_scene_target_edit"
    form = await flow.async_step_smart_scene_target_edit({
        "entity_id": SOURCE, "state": "on", "color_mode": "rgbw",
        "brightness": 160, "red": 0, "green": 0, "blue": 200,
        "white": 0,
    })
    assert form["kind"] == "saved", form
    assert flow.runtime.editor.scenes[0]["lights"][SOURCE][
        "rgbw_color"] == [0, 0, 200, 0]

    # Manufacturer-neutral RGBW light selection via the same HA light UI.
    form = await flow.async_step_smart_scene_add({
        "id": "new_shelly", "name": "Shelly LED",
    })
    assert form["kind"] == "form"
    field_names = {
        getattr(field, "schema", field)
        for field in form["data_schema"].schema
    }
    assert field_names == {"entity_id"}, field_names
    form = await flow.async_step_smart_scene_first_light({
        "entity_id": SHELLY,
    })
    fields = {
        getattr(field, "schema", field)
        for field in form["data_schema"].schema
    }
    assert {"brightness", "color_mode", "red", "green", "blue", "white"} <= fields
    form = await flow.async_step_smart_scene_first_light({
        "entity_id": SHELLY, "state": "on", "color_mode": "rgbw",
        "brightness": 170, "red": 13, "green": 23, "blue": 33, "white": 80,
    })
    assert form["kind"] == "saved", form
    assert flow.runtime.editor.scenes[-1]["lights"][SHELLY] == {
        "state": "on", "brightness": 170, "rgbw_color": [13, 23, 33, 80],
    }

    # HA reports onoff only: RGB and dimming controls must not be shown.
    form = await flow.async_step_smart_scene_add({
        "id": "new_onoff", "name": "Shelly Relay",
    })
    form = await flow.async_step_smart_scene_first_light({
        "entity_id": ONOFF,
    })
    fields = {
        getattr(field, "schema", field)
        for field in form["data_schema"].schema
    }
    assert fields == {"entity_id", "state"}, fields
    form = await flow.async_step_smart_scene_first_light({
        "entity_id": ONOFF, "state": "on",
    })
    assert form["kind"] == "saved"
    assert flow.runtime.editor.scenes[-1]["lights"][ONOFF] == {"state": "on"}

    form = await flow.async_step_smart_rules()
    assert "smart_rule_pick" in form["menu_options"]
    form = await flow.async_step_smart_rule_add()
    assert form["kind"] == "form"
    form = await flow.async_step_smart_rule_add({
        "name": "Sunset test", "scene_id": "test_abend",
        "action": "on", "trigger_kind": "sunset",
        "allowed_modes": ["home"], "allow_quiet": False,
        "enabled": False,
    })
    assert form["step_id"] == "smart_rule_trigger"
    form = await flow.async_step_smart_rule_trigger({
        "offset_minutes": -15,
    })
    assert form["kind"] == "saved", form
    assert len(flow.runtime.editor.automations) == 2
    assert flow.runtime.editor.automations[1]["trigger"] == {
        "type": "sun", "event": "sunset", "offset_minutes": -15,
    }
    assert flow.runtime.editor.automations[1]["enabled"] is False

    form = await flow.async_step_smart_rule_pick({"rule_id": "test_aus"})
    assert form["kind"] == "menu"
    form = await flow.async_step_smart_rule_edit()
    assert form["kind"] == "form"
    form = await flow.async_step_smart_rule_toggle()
    assert form["kind"] == "form"
    form = await flow.async_step_smart_rule_toggle({"confirm": True})
    assert form["kind"] == "saved", form
    assert flow.runtime.editor.automations[0]["enabled"] is True
    assert flow.runtime.editor.save_count == 6
    print("PASS: HA native Smart Lighting scene and rule forms validated")
    print("PASS: six GUI saves, including vendor-neutral Shelly RGBW and ONOFF")
    print("PASS: light controls derive from HA supported_color_modes")
    print("PASS: GUI save path writes only to synthetic editor; no hardware")


if __name__ == "__main__":
    asyncio.run(main())
