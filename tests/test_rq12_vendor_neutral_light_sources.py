"""No Home Assistant runtime: vendor-neutral light capability safety tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/red_queen/smart_lighting_sources.py"
SPEC = importlib.util.spec_from_file_location("rq12_sources", SOURCE)
assert SPEC and SPEC.loader
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)


def entity(entity_id, platform):
    return SimpleNamespace(entity_id=entity_id, platform=platform,
                           disabled_by=None, config_entry_id="device1")


def state(modes, name="Generic", status="on"):
    return SimpleNamespace(state=status, attributes={
        "supported_color_modes": modes, "friendly_name": name,
    })


class VendorNeutralSourceTests(unittest.TestCase):
    def setUp(self):
        self.entries = [
            entity("light.dali_eg_rgbw", "asyncua"),
            entity("light.shelly_strip_rgbw", "shelly"),
            entity("light.zigbee_strip", "mqtt"),
            entity("light.wled_strip", "wled"),
            entity("light.hof_wohn", "red_queen"),
            entity("light.old_proxy", "wnhf"),
            entity("light.template_proxy", "template"),
            entity("light.living_group", "group"),
            entity("light.shelly_relay", "shelly"),
        ]
        self.states = {
            "light.dali_eg_rgbw": state(["rgbw"], "DALI"),
            "light.shelly_strip_rgbw": state(["rgbw"], "Shelly LED"),
            "light.zigbee_strip": state(["rgb", "brightness"]),
            "light.wled_strip": state(["rgbww"]),
            "light.hof_wohn": state(["onoff"]),
            "light.old_proxy": state(["onoff"]),
            "light.template_proxy": state(["rgbw"]),
            "light.living_group": state(["rgbw"]),
            "light.shelly_relay": state(["onoff"]),
        }

    def test_direct_sources_from_any_vendor(self):
        catalog = source.eligible_ha_light_sources(
            self.entries, self.states.get,
            integration_domain="red_queen", integration_entry_id="rq_entry",
        )
        self.assertEqual(set(catalog), {
            "light.dali_eg_rgbw", "light.shelly_strip_rgbw",
            "light.zigbee_strip", "light.wled_strip", "light.shelly_relay",
        })
        self.assertEqual(catalog["light.shelly_strip_rgbw"], "Shelly LED")

    def test_offline_disabled_missing_capability_or_same_entry_excluded(self):
        self.entries[0].disabled_by = "user"
        self.entries[1].config_entry_id = "rq_entry"
        self.states["light.zigbee_strip"].state = "unavailable"
        self.states["light.wled_strip"].attributes.pop("supported_color_modes")
        catalog = source.eligible_ha_light_sources(
            self.entries, self.states.get,
            integration_domain="red_queen", integration_entry_id="rq_entry",
        )
        self.assertEqual(set(catalog), {"light.shelly_relay"})

    def test_editor_controls_based_on_capabilities(self):
        cases = [
            ("onoff", (False, False, False)),
            ("brightness", (True, False, False)),
            ("rgb", (True, True, False)),
            ("rgbw", (True, True, True)),
            ("rgbww", (True, True, True)),
            ("color_temp", (True, False, False)),
        ]
        for mode, expected in cases:
            with self.subTest(mode=mode):
                features = source.scene_form_features(
                    {"supported_color_modes": [mode]},
                )
                self.assertEqual(tuple(features.values()), expected)
        self.assertEqual(source.scene_form_features(
            {"supported_color_modes": ["rgbw"]}, semantic=True,
        ), {"brightness": False, "rgb": False, "rgbw": False})
        self.assertEqual(source.scene_form_features({"color_mode": "rgbw"}), {
            "brightness": False, "rgb": False, "rgbw": False,
        })


if __name__ == "__main__":
    unittest.main()
