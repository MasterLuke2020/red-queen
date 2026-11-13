"""Validate safe 1.1-compatible Home Assistant evening fallback fixtures."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1] / "configuration"
FILES = (
    ROOT / "ha_native_outdoor_sunset.ui.yaml",
    ROOT / "ha_native_outdoor_2300.ui.yaml",
)
EXPECTED = {
    "light.wnhf_garage_aussen_up_down",
    "light.hof_vorplatz_red_queen_strasse_up_down",
    "light.wnhf_hof_up_down",
}
EXCLUDED = {
    "light.wnhf_strasse_up_down",
    "light.wnhf_garage_innen",
    "light.wnhf_hof_wand",
}


class OutdoorFallbackTests(unittest.TestCase):
    def test_both_disabled_with_identical_exact_three(self):
        for path in FILES:
            with self.subTest(path=path.name):
                obj = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIs(obj["initial_state"], False)
                self.assertEqual(obj["conditions"], [] if "sunset" in path.name
                                 else obj["conditions"])
                self.assertEqual(len(obj["actions"]), 1)
                act = obj["actions"][0]
                self.assertEqual(set(act["target"]), {"entity_id"})
                ids = act["target"]["entity_id"]
                self.assertEqual(len(ids), 3)
                self.assertEqual(set(ids), EXPECTED)
                self.assertFalse(set(ids) & EXCLUDED)
                self.assertEqual(obj["mode"], "single")
                self.assertNotIn("area_id", repr(obj))
                self.assertNotIn("device_id", repr(obj))
                self.assertNotIn("brightness", repr(obj))
                self.assertNotIn("rgbw_color", repr(obj))

    def test_only_sunset_turns_on(self):
        obj = yaml.safe_load(FILES[0].read_text(encoding="utf-8"))
        self.assertEqual(obj["triggers"], [{"trigger": "sun", "event": "sunset", "enabled": False}])
        self.assertEqual(obj["actions"][0]["action"], "light.turn_on")

    def test_off_has_night_restart_guard_and_never_turns_on(self):
        obj = yaml.safe_load(FILES[1].read_text(encoding="utf-8"))
        self.assertEqual(obj["actions"][0]["action"], "light.turn_off")
        self.assertEqual(obj["triggers"], [
            {"trigger": "time", "at": "23:00:00", "id": "scheduled_off", "enabled": False},
            {"trigger": "homeassistant", "event": "start",
             "id": "restart_after_missed_off", "enabled": False},
        ])
        expr = obj["conditions"][0]["value_template"]
        self.assertIn("trigger.id == 'scheduled_off'", expr)
        self.assertIn("is_state('sun.sun', 'below_horizon')", expr)
        self.assertIn("now().hour >= 23", expr)
        self.assertNotIn("light.turn_on", repr(obj))


if __name__ == "__main__":
    unittest.main()
