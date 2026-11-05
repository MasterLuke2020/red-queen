"""Dependency-free Smart Living mode, permission and RGBW validation tests."""
from __future__ import annotations

import importlib.util
from enum import StrEnum
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / (
    "custom_components/wnhf/smart_living_logic.py"
)
spec = importlib.util.spec_from_file_location("redqueen_smart_living_logic", MODULE)
assert spec and spec.loader
logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)


class SmartLivingLogicTests(unittest.TestCase):
    def test_manual_modes_and_automatic_away_opt_in(self):
        self.assertEqual(logic.resolve_mode("away", None, False), ("away", "manual"))
        self.assertEqual(logic.resolve_mode("home", "on", False), ("home", "manual"))
        self.assertEqual(logic.resolve_mode("home", "on", True),
                         ("away", "configured_away_sensor"))
        self.assertEqual(logic.resolve_mode("away", "off", True),
                         ("home", "configured_away_sensor"))
        self.assertEqual(logic.resolve_mode("home", "unavailable", True)[0], "home")
        self.assertEqual(logic.resolve_mode("vacation", "off", True),
                         ("vacation", "manual"))
        with self.assertRaises(ValueError):
            logic.resolve_mode("holiday_unknown", "off", True)

    def test_quiet_restriction_fails_closed_on_missing_signal(self):
        self.assertFalse(logic.quiet_restriction("off"))
        for signal in (None, "on", "unknown", "unavailable", ""):
            with self.subTest(signal=signal):
                self.assertTrue(logic.quiet_restriction(signal))

    def test_permission_rules_preserve_resident_control(self):
        self.assertTrue(logic.permission("vacation", quiet=True,
                                        category="lighting.manual")[0])
        self.assertFalse(logic.permission("away", quiet=False,
                                         category="lighting.automatic_scene")[0])
        self.assertFalse(logic.permission("home", quiet=True,
                                         category="lighting.automatic_scene")[0])
        self.assertTrue(logic.permission("home", quiet=False,
                                        category="lighting.automatic_scene")[0])
        self.assertTrue(logic.permission("vacation", quiet=True,
                                        category="notifications.mobile")[0])
        for mode in ("away", "vacation"):
            self.assertFalse(logic.permission(mode, quiet=False,
                                              category="notifications.announce")[0])
        self.assertFalse(logic.permission("home", quiet=True,
                                          category="notifications.announce",
                                          urgency="warning")[0])
        self.assertFalse(logic.permission("home", quiet=True,
                                          category="notifications.announce",
                                          urgency="alarm")[0])
        self.assertTrue(logic.permission("home", quiet=False,
                                         category="notifications.announce")[0])
        self.assertFalse(logic.permission("home", quiet=False,
                                          category="access.unlock")[0])

    def test_smart_route_voice_never_bypasses_house_or_quiet_mode(self):
        decide = logic.route_voice_decision
        for profile in ("voice", "broadcast", "standard"):
            for mode in ("away", "vacation"):
                for priority in ("info", "warning", "critical"):
                    allowed, reason = decide(
                        profile=profile, legacy_context_allowed=True,
                        smart_living_source=True, mode=mode,
                        quiet=False, priority=priority,
                    )
                    with self.subTest(profile=profile, mode=mode,
                                      priority=priority):
                        self.assertFalse(allowed)
                        self.assertIn("smart_living_policy", reason)
            for priority in ("info", "warning", "critical"):
                allowed, reason = decide(
                    profile=profile, legacy_context_allowed=True,
                    smart_living_source=True, mode="home",
                    quiet=True, priority=priority,
                )
                with self.subTest(profile=profile, priority=priority):
                    self.assertFalse(allowed)
                    self.assertIn("smart_living_policy", reason)
            self.assertEqual(
                decide(profile=profile, legacy_context_allowed=True,
                       smart_living_source=True, mode="home", quiet=False,
                       priority="info"), (True, None),
            )
            self.assertEqual(
                decide(profile=profile, legacy_context_allowed=False,
                       smart_living_source=True, mode="home", quiet=False,
                       priority="info"),
                (False, "quiet_mode_or_house_state"),
            )
        for profile in ("silent", "mobile"):
            self.assertEqual(
                decide(profile=profile, legacy_context_allowed=True,
                       smart_living_source=True, mode="home", quiet=False,
                       priority="info"),
                (False, "profile"),
            )
        self.assertEqual(
            decide(profile="broadcast", legacy_context_allowed=True,
                   smart_living_source=True, mode="unknown", quiet=False,
                   priority="info")[0], False,
        )
        self.assertEqual(
            decide(profile="voice", legacy_context_allowed=True,
                   smart_living_source=True, mode="home", quiet=False,
                   priority="unknown"),
            (False, "unsupported_priority"),
        )

    def test_legacy_route_broadcast_behaviour_remains_unchanged(self):
        decide = logic.route_voice_decision
        # Previously configured alarms may rely on broadcast overriding
        # quiet mode. New Smart Living messages do NOT inherit this override.
        self.assertEqual(
            decide(profile="broadcast", legacy_context_allowed=False,
                   smart_living_source=False, mode="vacation",
                   quiet=True, priority="critical"),
            (True, None),
        )
        self.assertEqual(
            decide(profile="voice", legacy_context_allowed=False,
                   smart_living_source=False, mode="vacation",
                   quiet=True, priority="critical"),
            (False, "quiet_mode_or_house_state"),
        )
        self.assertEqual(
            decide(profile="standard", legacy_context_allowed=True,
                   smart_living_source=False, mode="unknown",
                   quiet=True, priority="info"),
            (True, None),
        )

    def test_rgbw_values_and_modes(self):
        self.assertEqual(
            logic.validate_light_request({"rgbw"}, {
                "rgbw_color": [17, 34, 51, 170], "brightness": 233,
                "transition": 2.5,
            }),
            {"rgbw_color": (17, 34, 51, 170),
             "brightness": 233, "transition": 2.5}
        )
        self.assertEqual(logic.validate_light_request({"onoff"}, {}), {})
        for invalid in (
            {"rgbw_color": [-1, 34, 55, 99]},
            {"rgbw_color": [1, 2, 3]},
            {"rgbw_color": ["1", 2, 3, 4]},
            {"brightness": True},
            {"brightness": 256},
            {"brightness": 7.2},
            {"transition": -1},
            {"transition": 1000000},
            {"entity_id": "light.admin"},
            {"rgbw_color": [1, 2, 3, 4], "rgb_color": [1, 2, 3]},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                logic.validate_light_request({"rgbw"}, invalid)
        with self.assertRaises(ValueError):
            logic.validate_light_request(
                {"onoff"}, {"rgbw_color": [20, 30, 40, 50]}
            )
        self.assertEqual(logic.exposed_modes(["rgbw", "bad", "onoff"]),
                         {"rgbw", "onoff"})
        self.assertEqual(logic.exposed_modes("rgbw"), set())
        # HA reports ColorMode values as StrEnum; the template renders their
        # repr (e.g. <ColorMode.RGBW: 'rgbw'>), even if the light is off.
        class ColorMode(StrEnum):
            RGBW = "rgbw"
        self.assertEqual(logic.exposed_modes([ColorMode.RGBW]), {"rgbw"})
        self.assertEqual(logic.validate_light_request(
            logic.exposed_modes([ColorMode.RGBW]),
            {"rgbw_color": [20, 40, 80, 120], "brightness": 80},
        ), {"rgbw_color": (20, 40, 80, 120), "brightness": 80})



    def test_scene_parse_and_reject_unsafe_configuration(self):
        scenes = logic.parse_scenes([{
            "id": "abend",
            "name": "Abend",
            "lights": {
                "light.dali_test_rgbw": {
                    "state": "on", "brightness": 170,
                    "rgbw_color": [0, 10, 12, 150],
                },
                "light.dali_off_rgbw": {"state": "off"},
            },
        }])
        self.assertEqual(list(scenes), ["abend"])
        self.assertEqual(len(scenes["abend"]["lights"]), 2)
        for invalid in (
            "not-a-list",
            [{"id": "INVALID-ID", "name": "Bad", "lights": {
                "light.dali_a_rgbw": {"brightness": 20},
            }}],
            [{"id": "bad", "name": "Bad", "lights": {
                "switch.unsafe": {"brightness": 20},
            }}],
            [{"id": "bad", "name": "Bad", "lights": {
                "light.dali_a_rgbw": {"state": "off", "brightness": 20},
            }}],
            [{"id": "bad", "name": "Bad", "lights": {
                "light.dali_a_rgbw": {"entity_id": "light.other"},
            }}],
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                logic.parse_scenes(invalid)

if __name__ == "__main__":
    unittest.main()
