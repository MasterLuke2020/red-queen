"""Offline staging cutover regression tests; no HA runtime or hardware."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/rq12_domain_stage.py"
spec = importlib.util.spec_from_file_location("rq12_domain_stage", SCRIPT)
assert spec and spec.loader
# The stage tool imports the pure domain transformer from tools/.
import sys
sys.path.insert(0, str(ROOT / "tools"))
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def store(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


class StageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.target = self.root / "target"
        self.old_package = self.source / "custom_components/wnhf"
        self.old_package.mkdir(parents=True)
        store(self.old_package / "manifest.json", {"domain": "wnhf"})
        self.new_package = self.root / "new_package"
        self.new_package.mkdir()
        store(self.new_package / "manifest.json", {"domain": "red_queen"})
        (self.new_package / "services.yaml").write_text(
            "smart_scene_activate:\n  fields: {}\nlighting_all_off:\n  fields: {}\nsmart_message_send:\n  fields: {}\n"
        )
        store(self.source / ".storage/core.config_entries", {
            "data": {"entries": [{"domain": "wnhf", "entry_id": "entry1",
                                  "data": {"token": "KEEP_SECRET"}}]}})
        store(self.source / ".storage/core.entity_registry", {
            "data": {"entities": [{"platform": "wnhf", "config_entry_id": "entry1",
                                   "entity_id": "light.wnhf_hof", "unique_id": "wnhf_hof"}]}})
        store(self.source / ".storage/core.device_registry", {
            "data": {"devices": [{"id": "dev1", "identifiers": [["wnhf", "framework"]]}]}})
        store(self.source / ".storage/wnhf.smart_living", {
            "version": 1, "key": "wnhf.smart_living",
            "data": {"manual_mode": "away"}})
        store(self.source / ".storage/lovelace.red-queen", {
            "data": {"config": {"views": [
                {"cards": [{"tap_action": {"action": "call-service",
                                          "service": "wnhf.lighting_all_off"},
                            "entity": "light.wnhf_hof"}]}]}}})
        (self.source / "configuration.yaml").write_text(
            "homeassistant:\n  name: House\nwnhf: {}\nlogger:\n  logs:\n"
            "    custom_components.wnhf: info\n", encoding="utf-8")
        (self.source / "scripts.yaml").write_text(
            "night:\n  sequence:\n    - service: wnhf.smart_scene_activate\n"
            "      data:\n        entity_id: light.wnhf_hof\n"
            "    - service: system_log.write\n      data:\n"
            "        logger: 'wnhf.voice_driver'  # internal channel\n",
            encoding="utf-8")
        (self.source / "automations.yaml").write_text(
            "- action: 'wnhf.smart_message_send'\n", encoding="utf-8")
        self.before = {str(p.relative_to(self.source)): p.read_bytes()
                       for p in self.source.rglob("*") if p.is_file()}

    def test_creates_stage_without_changing_source(self):
        result = tool.stage(self.source, self.target, self.new_package)
        self.assertEqual(result["state"], "STAGING_ONLY_NOT_PRODUCTION")
        self.assertFalse((self.target / "custom_components/wnhf").exists())
        self.assertTrue((self.target / "custom_components/red_queen").exists())
        self.assertIn("red_queen: {}", (self.target / "configuration.yaml").read_text())
        self.assertIn("custom_components.red_queen: info",
                      (self.target / "configuration.yaml").read_text())
        self.assertIn("red_queen.smart_scene_activate",
                      (self.target / "scripts.yaml").read_text())
        self.assertIn("logger: 'red_queen.voice_driver'  # internal channel",
                      (self.target / "scripts.yaml").read_text())
        self.assertEqual(result["stats"]["logger_channel_renames"], 1)
        self.assertIn("red_queen.smart_message_send",
                      (self.target / "automations.yaml").read_text())
        dashboard = json.loads((self.target / ".storage/lovelace.red-queen").read_text())
        card = dashboard["data"]["config"]["views"][0]["cards"][0]
        self.assertEqual(card["tap_action"]["service"], "red_queen.lighting_all_off")
        self.assertEqual(card["entity"], "light.wnhf_hof")
        self.assertEqual(json.loads((self.target / ".storage/wnhf.smart_living")
                                    .read_text())["data"]["manual_mode"], "away")
        entities = json.loads((self.target / ".storage/core.entity_registry").read_text())
        self.assertEqual(entities["data"]["entities"][0]["entity_id"], "light.wnhf_hof")
        self.assertEqual(entities["data"]["entities"][0]["platform"], "red_queen")
        self.assertEqual(self.before, {
            str(p.relative_to(self.source)): p.read_bytes()
            for p in self.source.rglob("*") if p.is_file()
        })
        with self.assertRaises(tool.StageError):
            tool.stage(self.source, self.target, self.new_package)
        self.assertFalse(any(p.name.startswith(".rq12-staging-")
                             for p in self.root.iterdir()))

    def test_abort_on_duplicate_root_without_stage(self):
        path = self.source / "configuration.yaml"
        path.write_text("wnhf: {}\nred_queen: {}\n")
        with self.assertRaises(tool.StageError):
            tool.stage(self.source, self.target, self.new_package)
        self.assertFalse(self.target.exists())

    def test_abort_on_symlink(self):
        (self.source / "external").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(tool.StageError):
            tool.stage(self.source, self.target, self.new_package)
        self.assertFalse(self.target.exists())

    def test_preserves_hidden_backup_yaml_unchanged(self):
        archive = self.source / ".historical_ha_backup/20261103/configuration.yaml"
        archive.parent.mkdir(parents=True)
        archive.write_text(
            "wnhf: {}\n"
            "script:\n  - service: wnhf.smart_scene_activate\n",
            encoding="utf-8",
        )
        backup_contents = archive.read_bytes()
        tool.stage(self.source, self.target, self.new_package)
        copied = self.target / ".historical_ha_backup/20261103/configuration.yaml"
        self.assertEqual(copied.read_bytes(), backup_contents)

    def test_no_blind_substitution_of_entity_ids(self):
        source = "service: wnhf.lighting_all_off\nentity_id: light.wnhf_hof\n"
        rewritten, root_count, svc_count = tool.rewrite_yaml_source(source)
        self.assertEqual(root_count, 0)
        self.assertEqual(svc_count, 1)
        self.assertIn("entity_id: light.wnhf_hof", rewritten)

    def test_known_logger_channels_are_exact_and_do_not_touch_entities(self):
        source = (
            "  logger: wnhf.channel_log\n"
            "    logger: 'wnhf.channel_voice' # detail\n"
            '    logger: "wnhf.notify"\n'
            "    logger: wnhf.channel_router\n"
            "    logger: wnhf.voice_driver\n"
            "    entity_id: light.wnhf_hof\n"
            "    logger: unrelated.component\n"
        )
        updated, count = tool.rewrite_logger_channels(source)
        self.assertEqual(count, 5)
        for name in ("channel_log", "channel_voice", "notify",
                     "channel_router", "voice_driver"):
            self.assertIn("red_queen." + name, updated)
        self.assertIn("entity_id: light.wnhf_hof", updated)
        self.assertIn("logger: unrelated.component", updated)

    def test_unknown_or_dynamic_logger_channel_blocks_stage(self):
        for line in (
            "logger: wnhf.unexpected_new_channel\n",
            'logger: "{{ wnhf.some_expression }}"\n',
        ):
            with self.subTest(line=line), self.assertRaises(tool.StageError):
                tool.rewrite_logger_channels(line)

    def test_unrecognized_template_fails_closed(self):
        with self.assertRaises(tool.StageError):
            tool.rewrite_yaml_source("service: '{{ wnhf.dynamic }}'\n")

    def test_unknown_service_rejected(self):
        with self.assertRaises(tool.StageError):
            tool.rewrite_yaml_source(
                "service: wnhf.removed_service\n",
                allowed_services={"lighting_all_off"},
            )
        with self.assertRaises(tool.StageError):
            tool.rewrite_lovelace_json(
                {"service": "wnhf.removed_service"},
                allowed_services={"lighting_all_off"},
            )

    def test_unnamed_service_lovelace_unmodified(self):
        doc, count = tool.rewrite_lovelace_json({
            "action": "call-service", "service": "wnhf.smart_message_send",
            "entity": "sensor.wnhf_state"
        })
        self.assertEqual(count, 1)
        self.assertEqual(doc["action"], "call-service")
        self.assertEqual(doc["service"], "red_queen.smart_message_send")
        self.assertEqual(doc["entity"], "sensor.wnhf_state")


if __name__ == "__main__":
    unittest.main()
