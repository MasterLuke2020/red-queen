"""Dependency-free tests for GUI scene and rule serialization/contracts.

No Home Assistant runtime, physical lights, or external services needed.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import Any
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/wnhf"


def load_pure_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


logic = load_pure_module("smart_living_logic.py", "rq_editor_scene_logic")
auto = load_pure_module(
    "smart_living_automation_logic.py", "rq_editor_rule_logic"
)


def extract_functions(filename: str, names: list[str], environment: dict):
    source = (ROOT / filename).read_text(encoding="utf-8")
    tree = ast.parse(source)
    funcs = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in names
    ]
    assert set(names) == {node.name for node in funcs}
    code = compile(
        ast.fix_missing_locations(ast.Module(body=funcs, type_ignores=[])),
        filename,
        "exec",
    )
    exec(code, environment)
    return environment


helpers = extract_functions(
    "smart_living_editor.py",
    ["scenes_to_raw", "rules_to_raw", "validate_editor_document"],
    {
        "Any": Any,
        "parse_scenes": logic.parse_scenes,
        "parse_automation_rules": auto.parse_automation_rules,
        "MAX_SCENES": 80,
        "MAX_LIGHTS_PER_SCENE": 32,
    },
)
ui = extract_functions(
    "smart_lighting_options.py",
    ["_scene_light_settings", "_trigger_from_editor"],
    {"Any": Any},
)

LIGHT = "light.dali_eg_buro_rgbw"
SCENE = {
    "id": "buero",
    "name": "Büro",
    "lights": {
        LIGHT: {
            "state": "on",
            "rgbw_color": [0, 0, 0, 255],
            "brightness": 200,
        },
    },
}
RULE = {
    "id": "buero_aus",
    "name": "Büro aus",
    "enabled": False,
    "scene_id": "buero",
    "action": "off",
    "trigger": {"type": "time", "at": "23:00"},
}


class SmartLightingEditorTests(unittest.TestCase):
    def test_existing_scenes_round_trip_without_data_loss(self):
        parsed = logic.parse_scenes([SCENE])
        raw = helpers["scenes_to_raw"](parsed)
        self.assertEqual(raw, [SCENE])
        self.assertEqual(logic.parse_scenes(raw), parsed)

    def test_scene_and_rule_round_trip(self):
        parsed_scene = logic.parse_scenes([SCENE])
        parsed_rule = auto.parse_automation_rules([RULE], parsed_scene)
        unparsed = helpers["rules_to_raw"](parsed_rule)
        self.assertEqual(unparsed, [{**RULE, "allowed_modes": ["home"],
                                     "allow_quiet": False}])
        new_scene, new_rule = helpers["validate_editor_document"](
            [SCENE], unparsed, {LIGHT},
        )
        self.assertEqual(new_scene, parsed_scene)
        self.assertEqual(new_rule, parsed_rule)

    def test_keep_saved_scenes_readable_if_source_disappears(self):
        # On HA startup the scene is kept for repair; its enabled schedule is
        # blocked from registration instead of taking Red Queen down.
        scenes, rules = helpers["validate_editor_document"](
            [SCENE], [RULE], set(), require_sources=False,
        )
        self.assertIn("buero", scenes)
        self.assertIn("buero_aus", rules)
        scheduler = (ROOT / "smart_living_automation.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("self.blocked_rules", scheduler)

    def test_reject_unapproved_sources_and_broken_rule_refs(self):
        with self.assertRaises(ValueError):
            helpers["validate_editor_document"]([SCENE], [RULE], set())
        with self.assertRaises(ValueError):
            helpers["validate_editor_document"](
                [SCENE],
                [{**RULE, "scene_id": "deleted_scene"}],
                {LIGHT},
            )
        with self.assertRaises(ValueError):
            helpers["validate_editor_document"](
                [SCENE, SCENE], [RULE], {LIGHT},
            )

    def test_rgbw_scene_white_is_explicit_and_brightness_independent(self):
        source = {
            "state": "on", "brightness": 200,
            "color_mode": "rgbw",
            "red": 0, "green": 0, "blue": 255, "white": 0,
        }
        self.assertEqual(ui["_scene_light_settings"](source), {
            "state": "on",
            "brightness": 200,
            "rgbw_color": [0, 0, 255, 0],
        })
        source["state"] = "off"
        self.assertEqual(ui["_scene_light_settings"](source), {
            "state": "off",
        })

    def test_time_selector_and_sunset_form_round_trip(self):
        self.assertEqual(ui["_trigger_from_editor"](
            {"trigger_kind": "time"},
            {"at": "23:00:00"},
        ), {"type": "time", "at": "23:00"})
        self.assertEqual(ui["_trigger_from_editor"](
            {"trigger_kind": "sunset"}, {"offset_minutes": -15},
        ), {"type": "sun", "event": "sunset", "offset_minutes": -15})
        self.assertEqual(ui["_trigger_from_editor"](
            {"trigger_kind": "state"},
            {"entity_id": "binary_sensor.bewegung", "to": "on"},
        ), {"type": "state", "entity_id": "binary_sensor.bewegung",
            "to": "on"})

    def test_gui_is_integrated_without_startup_physical_calls(self):
        cfg = (ROOT / "config_flow.py").read_text(encoding="utf-8")
        self.assertIn(
            "class WNHFOptionsFlow(SmartLightingOptionsMixin,",
            cfg,
        )
        self.assertIn('"smart_lighting",', cfg)
        runtime = (ROOT / "smart_living_runtime.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("stored = await self.editor.async_load()", runtime)
        self.assertIn("stored[\"scenes\"], stored[\"automations\"]", runtime)
        mixin = (ROOT / "smart_lighting_options.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("return self._finish(\"smart_lighting_saved\")", mixin)
        self.assertNotIn("async_light_dispatch", mixin)
        self.assertNotIn("async_activate_scene", mixin)
        self.assertNotIn("async_fire(", mixin)


if __name__ == "__main__":
    unittest.main()
