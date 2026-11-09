"""Offline real-house reference acceptance: no HA runtime and no hardware."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SCRIPT = ROOT / "tools/rq12_site_reference_gate.py"
spec = importlib.util.spec_from_file_location("rq12_reference_gate", SCRIPT)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

preflight_path = ROOT / "tools/rq12_site_stage_preflight.py"
ps = importlib.util.spec_from_file_location("rq12_preflight", preflight_path)
assert ps and ps.loader
preflight = importlib.util.module_from_spec(ps)
ps.loader.exec_module(preflight)


def dump(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


class ReferenceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        r = Path(self.temp.name)
        self.src = r / "snapshot"
        self.stg = r / "migrated"
        self.rollback = r / "rolled_back"
        self.live = r / "productive"
        self.live.mkdir()
        self.pkg = r / "component"
        self.pkg.mkdir()
        dump(self.pkg / "manifest.json", {"domain": "red_queen"})
        (self.pkg / "services.yaml").write_text(
            "lighting_all_off:\n  description: sample\n"
        )
        dump(self.src / "custom_components/wnhf/manifest.json", {"domain": "wnhf"})
        dump(self.src / ".storage/core.config_entries", {"data": {
            "entries": [{"domain": "wnhf", "entry_id": "old", "data": {"secret": "hidden"}}],
        }})
        dump(self.src / ".storage/core.entity_registry", {"data": {
            "entities": [{"platform": "wnhf", "config_entry_id": "old",
                          "entity_id": "light.wnhf_house", "unique_id": "wnhf_house"}],
        }})
        dump(self.src / ".storage/core.device_registry", {"data": {
            "devices": [{"id": "old_dev", "identifiers": [["wnhf", "dev"]]}],
        }})
        dump(self.src / ".storage/wnhf.dashboard", {"data": {"secret": "not shown"}})
        dump(self.src / ".storage/wnhf.smart_living", {"data": {"manual_mode": "home"}})
        dump(self.src / ".storage/lovelace.lovelace", {"data": {
            "views": [{"cards": [{"entity": "light.wnhf_house",
                                  "tap_action": {"service": "wnhf.lighting_all_off"}}]}]
        }})
        (self.src / "configuration.yaml").write_text(
            "wnhf: {}\n", encoding="utf-8"
        )
        (self.src / "scripts.yaml").write_text(
            "night:\n  - service: wnhf.lighting_all_off\n"
            "    logger: wnhf.voice_driver\n"
            "    entity_id: light.wnhf_house\n", encoding="utf-8"
        )
        (self.src / "wnhf/house/registry").mkdir(parents=True)
        (self.src / "wnhf/house/registry/lights.yaml").write_text("lights: []\n")
        archived = self.src / ".old-config/configuration.yaml"
        archived.parent.mkdir()
        archived.write_text("wnhf: {}\nservice: wnhf.lighting_all_off\n", encoding="utf-8")

    def migrate(self):
        preflight.rehearse(
            self.src, self.stg, self.rollback, self.live, self.pkg,
            expected_entities=1, expected_devices=1,
        )

    def test_real_reference_gate_accepts_known_legacy_and_archived_source(self):
        self.migrate()
        report = gate.inspect(
            self.src, self.stg, self.live,
            expected_entities=1, expected_devices=1,
        )
        self.assertEqual(report["state"], "OFFLINE_REFERENCE_GATE_PASSED_NOT_PRODUCTION")
        self.assertEqual(report["service_calls_before"], 2)
        self.assertEqual(report["service_calls_after"], 0)
        self.assertEqual(report["logger_channels_before"], 1)
        self.assertEqual(report["logger_channels_after"], 0)
        self.assertEqual(report["active_legacy_reference_blockers"], {})
        self.assertEqual(report["preserved_active_entity_reference_mentions"], 2)
        self.assertEqual(report["historical_hidden_backup_references"]["literal_service_calls"], 1)
        self.assertNotIn("hidden", json.dumps(report))
        self.assertNotIn("not shown", json.dumps(report))
        self.assertFalse(report["release_approved"])

    def test_leftover_real_yaml_reference_blocks_cutover(self):
        self.migrate()
        with (self.stg / "scripts.yaml").open("a", encoding="utf-8") as f:
            f.write("  - action: wnhf.lighting_all_off\n")
        outcome = gate.inspect(
            self.src, self.stg, self.live,
            expected_entities=1, expected_devices=1,
        )
        self.assertEqual(outcome["state"], "OFFLINE_REFERENCE_GATE_BLOCKED")
        self.assertEqual(outcome["active_legacy_reference_blockers"]["literal_service_calls"], 1)

    def test_changed_registry_refused(self):
        self.migrate()
        path = self.stg / ".storage/core.entity_registry"
        data = json.loads(path.read_text())
        data["data"]["entities"][0]["unique_id"] = "changed"
        path.write_text(json.dumps(data))
        with self.assertRaises(gate.AcceptanceError):
            gate.inspect(
                self.src, self.stg, self.live,
                expected_entities=1, expected_devices=1,
            )

    def test_refuse_actual_live_directory(self):
        self.migrate()
        with self.assertRaises(gate.AcceptanceError):
            gate.inspect(
                self.live, self.stg, self.live,
                expected_entities=1, expected_devices=1,
            )


if __name__ == "__main__":
    unittest.main()
