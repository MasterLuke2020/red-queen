"""Red Queen 1.1.0 read-only inventory unit tests (standard unittest)."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.rq11_inventory import build_report


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.write("custom_components/wnhf/manifest.json", '{"version":"1.0.0"}')
        self.write("wnhf/house/registry/rooms.yaml", """
rooms:
  - id: house.eg.office
    name: Büro
    floor: eg
""")
        self.write("wnhf/house/registry/lights.yaml", """
lights:
  - id: light.eg.office.main
    name: Bürolicht
    room: house.eg.office
    control_mode: toggle
    command:
      entity_id: button.btwebeglichtbuero
    state:
      entity_id: binary_sensor.office_light_feedback
""")
        for name in ("covers", "openings", "plants"):
            self.write(
                "wnhf/house/registry/" + name + ".yaml",
                name + ": []\n"
            )
        self.write("wnhf/house/registry/notification_targets.yaml", """
notification_targets:
  - id: notification.target.mobile
    entity_id: notify.test_phone
announcement_targets:
  - id: announcement.target.office
    provider: home_assistant_tts_sonos
    tts_entity_id: tts.google_translate_de_at
    levels:
      info:
        speakers: [media_player.office]
        volume: 0.3
notification_routes:
  - id: notification.route.house
    announcement_target_id: announcement.target.office
    notification_target_ids: [notification.target.mobile]
    context:
      quiet_mode_entity_id: input_boolean.quiet_mode
""")
        self.write(".storage/core.entity_registry", json.dumps({
            "data": {
                "entities": [
                    {"entity_id": "button.btwebeglichtbuero",
                     "platform": "asyncua", "disabled_by": None},
                    {"entity_id": "light.rgb_kitchen",
                     "platform": "hue", "disabled_by": None},
                    {"entity_id": "media_player.office",
                     "platform": "sonos", "disabled_by": None},
                    {"entity_id": "person.private",
                     "platform": "person", "disabled_by": None},
                ]
            }
        }))
        self.write("secrets.yaml", "api_password: TOP_SECRET_NOT_FOR_REPORT\n")
        self.write(
            ".storage/core.config_entries",
            '{"secret":"TOP_SECRET_NOT_FOR_REPORT"}'
        )

    def write(self, relpath: str, content: str) -> None:
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_report_collects_semantic_bindings_without_secrets(self) -> None:
        before = {
            str(p.relative_to(self.root)): p.read_bytes()
            for p in self.root.rglob("*") if p.is_file()
        }
        report = build_report(self.root)
        after = {
            str(p.relative_to(self.root)): p.read_bytes()
            for p in self.root.rglob("*") if p.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(report["schema"], "redqueen.inventory.1.1.v1")
        self.assertEqual(report["environment"]["red_queen_version"], "1.0.0")
        self.assertEqual(report["registries"]["counts"]["lights"]["count"], 1)
        self.assertEqual(
            report["registries"]["lights"][0]["command_entity_id"],
            "button.btwebeglichtbuero"
        )
        entities = report["entity_registry"]["selected_entities"]
        ids = {entity["entity_id"] for entity in entities}
        self.assertIn("button.btwebeglichtbuero", ids)
        self.assertIn("light.rgb_kitchen", ids)
        self.assertIn("media_player.office", ids)
        self.assertNotIn("person.private", ids)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("TOP_SECRET_NOT_FOR_REPORT", serialized)

    def test_invalid_yaml_is_reported_without_leaking_content(self) -> None:
        self.write("wnhf/house/registry/lights.yaml", """
lights: !unsafe TOP_SECRET_NOT_FOR_REPORT
""")
        report = build_report(self.root)
        self.assertEqual(report["registries"]["counts"]["lights"]["count"], 0)
        self.assertTrue(any(
            "lights.yaml: unreadable" in warning
            for warning in report["warnings"]
        ))
        self.assertNotIn(
            "TOP_SECRET_NOT_FOR_REPORT",
            json.dumps(report, ensure_ascii=False)
        )

    def test_collector_handles_missing_entity_registry(self) -> None:
        (self.root / ".storage/core.entity_registry").unlink()
        report = build_report(self.root)
        self.assertEqual(report["entity_registry"]["total"], 0)
        self.assertTrue(any(
            "core.entity_registry: not found" in warning
            for warning in report["warnings"]
        ))


if __name__ == "__main__":
    unittest.main()
