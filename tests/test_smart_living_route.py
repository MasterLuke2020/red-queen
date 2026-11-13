"""Execute the real notification routing-plan method against safe mock states.

No Home Assistant dependency, network, speaker, service or actual notification
dispatch. The tested method body is extracted unchanged from its provider class.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = ROOT / "custom_components/red_queen/providers/notifications.py"
LOGIC = ROOT / "custom_components/red_queen/smart_living_logic.py"

spec = importlib.util.spec_from_file_location("redqueen_route_logic", LOGIC)
assert spec and spec.loader
logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)


def load_real_route_plan():
    tree = ast.parse(PROVIDER.read_text(encoding="utf-8"))
    method = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_route_plan"
    ]
    if len(method) != 1:
        raise AssertionError("Expected exactly one provider routing planner")
    # Importing the full provider would require a live HA installation.
    # Execute only its unchanged method AST with inert fake HA state objects.
    namespace = {
        "NotificationRoute": object, "Any": object,
        "DOMAIN": "red_queen", "DATA_SMART_LIVING": "smart_living",
        "route_voice_decision": logic.route_voice_decision,
    }
    module = ast.fix_missing_locations(
        ast.Module(body=[method[0]], type_ignores=[]),
    )
    exec(compile(module, str(PROVIDER), "exec"), namespace)
    return namespace["_route_plan"]


route_plan = load_real_route_plan()


class FakeStateStore:
    def __init__(self, items):
        self.items = items

    def get(self, entity_id):
        value = self.items.get(entity_id)
        return SimpleNamespace(state=value) if value is not None else None


def scenario(
    *,
    source, profile, mode="home", quiet=False,
    legacy_house_state="unknown", legacy_quiet="off", priority="info",
):
    route = SimpleNamespace(
        house_state_entity_id="sensor.wnhf_house_state",
        quiet_mode_entity_id="binary_sensor.wnhf_quiet_mode_active",
        voice_blocked_states=("away", "vacation"),
        dashboard_enabled=True,
        log_enabled=True,
    )
    states = FakeStateStore({
        route.house_state_entity_id: legacy_house_state,
        route.quiet_mode_entity_id: legacy_quiet,
    })
    runtime = SimpleNamespace(mode=mode, quiet=quiet)
    fake = SimpleNamespace(hass=SimpleNamespace(
        data={"red_queen": {"smart_living": runtime}},
        states=states,
    ))
    return route_plan(fake, route, source=source,
                      profile=profile, priority=priority)


class RoutePlannerSafetyTests(unittest.TestCase):
    def test_smart_broadcast_cannot_bypass_vacation(self):
        plan = scenario(
            source="smart_living", profile="broadcast", mode="vacation",
        )
        self.assertFalse(plan["voice"])
        self.assertNotIn("voice", plan["selected_channels"])
        self.assertIn("mobile", plan["selected_channels"])
        self.assertTrue(plan["voice_context"]["smart_living_guard_applied"])
        self.assertFalse(plan["voice_context"]["broadcast_override"])

    def test_smart_voice_stops_when_quiet_is_missing(self):
        for value in ("on", "unknown", "unavailable"):
            with self.subTest(value=value):
                plan = scenario(
                    source="smart_living", profile="voice", mode="home",
                    quiet=True, legacy_quiet=value,
                )
                self.assertFalse(plan["voice"])
                self.assertIn("smart_living_policy",
                              plan["voice_context"]["suppression_reason"])

    def test_smart_normal_home_voice_enabled(self):
        plan = scenario(source="smart_living", profile="voice")
        self.assertTrue(plan["voice"])
        self.assertIn("voice", plan["selected_channels"])

    def test_existing_broadcast_override_preserved(self):
        plan = scenario(source="old_automation", profile="broadcast",
                        mode="vacation", quiet=True, legacy_quiet="on")
        self.assertTrue(plan["voice"])
        self.assertTrue(plan["voice_context"]["broadcast_override"])
        self.assertFalse(plan["voice_context"]["smart_living_guard_applied"])

    def test_existing_standard_does_not_infer_new_mode_from_missing_sensor(self):
        # Old 1.0 used unknown technical house state and did not see the
        # manually selected new Smart Living resident away state.
        plan = scenario(source="old_automation", profile="standard",
                        mode="away", legacy_house_state="unknown")
        self.assertTrue(plan["voice"])
        self.assertEqual(plan["voice_context"]["house_state"], "unknown")

    def test_existing_standard_still_obeys_explicit_legacy_quiet(self):
        plan = scenario(source="old_automation", profile="standard",
                        mode="home", legacy_quiet="on")
        self.assertFalse(plan["voice"])
        self.assertEqual(plan["voice_context"]["suppression_reason"],
                         "quiet_mode_or_house_state")

    def test_smart_mobile_remains_available_while_away(self):
        plan = scenario(source="smart_living", profile="mobile",
                        mode="vacation", quiet=True, legacy_quiet="on")
        self.assertFalse(plan["voice"])
        self.assertTrue(plan["mobile"])
        self.assertIn("mobile", plan["selected_channels"])


if __name__ == "__main__":
    unittest.main()
