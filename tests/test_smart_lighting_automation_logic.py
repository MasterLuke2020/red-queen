"""Dependency-free regression tests for opt-in Red Queen Smart Lighting 1.2."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/wnhf"
module_path = ROOT / "smart_living_automation_logic.py"
spec = importlib.util.spec_from_file_location("rq_automation_logic_test", module_path)
assert spec is not None and spec.loader is not None
logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)


def make_rule(**updates):
    rule = {
        "id": "aussen_an",
        "name": "Außenbeleuchtung Abend",
        "scene_id": "aussen",
        "action": "on",
        "trigger": {"type": "sun", "event": "sunset"},
    }
    rule.update(updates)
    return rule


SCENES = {"aussen": {"lights": {
    "light.dali_aussen_rgbw": {"state": "on", "attributes": {}},
}}}


class RulesTests(unittest.TestCase):
    def test_empty_rules_are_inert(self):
        self.assertEqual(logic.parse_automation_rules(None, SCENES), {})
        self.assertEqual(logic.parse_automation_rules([], SCENES), {})

    def test_disabled_by_default_and_default_guard(self):
        rules = logic.parse_automation_rules([make_rule()], SCENES)
        rule = rules["aussen_an"]
        self.assertFalse(rule["enabled"])
        self.assertEqual(rule["allowed_modes"], ("home",))
        self.assertFalse(rule["allow_quiet"])
        self.assertEqual(rule["trigger"], {
            "type": "sun", "event": "sunset", "offset_minutes": 0,
        })
        self.assertEqual(
            logic.automation_permission(rule, "home", False),
            (False, "rule_disabled"),
        )

    def test_sunset_outdoor_explicit_opt_in_and_limited_off(self):
        rules = logic.parse_automation_rules([
            make_rule(
                enabled=True, allowed_modes=["home", "away", "vacation"],
                allow_quiet=True, trigger={
                    "type": "sun", "event": "sunset", "offset_minutes": -15,
                },
            ),
            make_rule(
                id="aussen_aus", name="Außenbeleuchtung aus",
                enabled=True, action="off",
                trigger={"type": "time", "at": "23:00"},
            ),
        ], SCENES)
        self.assertEqual(len(rules), 2)
        self.assertEqual(rules["aussen_an"]["trigger"]["offset_minutes"], -15)
        self.assertEqual(rules["aussen_aus"]["trigger"]["at"], "23:00")
        self.assertTrue(logic.automation_permission(
            rules["aussen_an"], "vacation", True, quiet_state="on",
        )[0])
        self.assertFalse(logic.automation_permission(
            rules["aussen_an"], "vacation", True, quiet_state="unavailable",
        )[0])
        self.assertTrue(logic.automation_permission(
            rules["aussen_aus"], "away", True,
        )[0])
        self.assertTrue(logic.automation_permission(
            rules["aussen_aus"], "unknown", True,
        )[0])

    def test_no_implicit_away_or_quiet_bypass(self):
        rule = logic.parse_automation_rules([
            make_rule(enabled=True)
        ], SCENES)["aussen_an"]
        self.assertTrue(logic.automation_permission(rule, "home", False)[0])
        self.assertFalse(logic.automation_permission(rule, "away", False)[0])
        self.assertFalse(logic.automation_permission(rule, "vacation", False)[0])
        self.assertFalse(logic.automation_permission(rule, "home", True)[0])
        self.assertFalse(logic.automation_permission(rule, "unknown", True)[0])

    def test_strict_rejection(self):
        cases = [
            make_rule(id="INVALID"),
            make_rule(scene_id="unknown"),
            make_rule(name=" "),
            make_rule(action="toggle"),
            make_rule(action=[]),
            make_rule(enabled="true"),
            make_rule(allow_quiet="yes"),
            make_rule(allowed_modes=[]),
            make_rule(allowed_modes=["away", "away"]),
            make_rule(allowed_modes=["all"]),
            make_rule(allowed_modes=[{}]),
            make_rule(trigger={"type": "time", "at": "24:00"}),
            make_rule(trigger={"type": "time", "at": "23:00:59"}),
            make_rule(trigger={"type": "time", "at": "23:00", "extra": 1}),
            make_rule(trigger={"type": "sun", "event": "moonrise"}),
            make_rule(trigger={"type": "sun", "event": []}),
            make_rule(trigger={"type": "sun", "event": "sunset",
                               "offset_minutes": True}),
            make_rule(trigger={"type": "sun", "event": "sunset",
                               "offset_minutes": 121}),
            make_rule(trigger={"type": "state", "entity_id": "binary_sensor.x"}),
            make_rule(arbitrary="service.call"),
        ]
        for rule in cases:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                logic.parse_automation_rules([rule], SCENES)
        with self.assertRaises(ValueError):
            logic.parse_automation_rules([make_rule(), make_rule()], SCENES)

    def test_runtime_contract_is_opt_in_and_unsubscribes(self):
        runtime = ast.parse(
            (ROOT / "smart_living_automation.py").read_text(encoding="utf-8")
        )
        source = ast.unparse(runtime)
        self.assertIn("async_track_sunset", source)
        self.assertIn("async_track_sunrise", source)
        self.assertIn("async_track_time_change", source)
        self.assertIn("self._listeners.append(unsubscribe)", source)
        self.assertIn("unsubscribe()", source)
        self.assertIn("self.runtime.async_light_dispatch(", source)
        self.assertIn("automation_permission(", source)
        self.assertNotIn("lighting_all_off(", source)
        core = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("smart_living.async_start_automations()", core)
        self.assertIn("runtime.async_stop_automations()", core)
        existing = (ROOT / "smart_living_runtime.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("parse_automation_rules(", existing)
        self.assertIn('category="lighting.automatic_scene"', existing)
        self.assertIn('SERVICE_SMART_AUTOMATIONS_SNAPSHOT,', (
            ROOT / "services.py"
        ).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
