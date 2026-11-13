"""No hardware: isolated restoration and guardrail checks for real-site preflight."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location(
    "rq12_site_preflight", ROOT / "tools/rq12_site_stage_preflight.py",
)
assert spec and spec.loader
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def doc(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


class SiteRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.live = self.root / "production"
        self.live.mkdir()
        self.source = self.root / "snapshot"
        self.stage = self.root / "staging"
        self.rollback = self.root / "restore"
        self.package = self.root / "package"
        self.package.mkdir()
        doc(self.package / "manifest.json", {"domain": "red_queen"})
        (self.package / "services.yaml").write_text(
            "smart_scene_activate:\n  description: test\n"
        )
        (self.source / "custom_components/wnhf").mkdir(parents=True)
        doc(self.source / "custom_components/wnhf/manifest.json",
            {"domain": "wnhf"})
        (self.source / "configuration.yaml").write_text("wnhf: {}\n")
        doc(self.source / ".storage/core.config_entries", {
            "data": {"entries": [{
                "domain": "wnhf", "entry_id": "a",
                "data": {"secret": "NEVER_SHOW_THIS"},
            }]},
        })
        doc(self.source / ".storage/core.entity_registry", {
            "data": {"entities": [{
                "platform": "wnhf", "config_entry_id": "a",
                "unique_id": "wnhf_lamp", "entity_id": "light.wnhf_lamp",
            }]},
        })
        doc(self.source / ".storage/core.device_registry", {
            "data": {"devices": [{
                "id": "device-1", "identifiers": [["wnhf", "lamp"]],
            }]},
        })
        doc(self.source / ".storage/wnhf.dashboard", {
            "data": {"private": "SECRET_DASHBOARD"},
        })
        doc(self.source / ".storage/wnhf.smart_living", {
            "data": {"manual_mode": "home"},
        })
        (self.source / "wnhf/house/registry").mkdir(parents=True)
        (self.source / "wnhf/house/registry/lights.yaml").write_text(
            "lights: []\n", encoding="utf-8"
        )

    def run_it(self, **kwargs):
        return tool.rehearse(
            self.source, self.stage, self.rollback, self.live, self.package,
            expected_entities=kwargs.get("entities", 1),
            expected_devices=kwargs.get("devices", 1),
        )

    def test_full_stage_and_exact_copy_rollback(self):
        before = tool._file_inventory(self.source)
        report = self.run_it()
        self.assertEqual(report["state"],
                         "OFFLINE_SITE_REHEARSAL_PASSED_NOT_PRODUCTION")
        self.assertEqual(report["old_domain_entities"], 1)
        self.assertEqual(report["old_domain_devices"], 1)
        self.assertTrue(report["rollback_copy_exact"])
        self.assertFalse(report["home_assistant_started"])
        self.assertFalse(report["release_approved"])
        self.assertEqual(tool._file_inventory(self.source), before)
        self.assertEqual(tool._file_inventory(self.rollback), before)
        self.assertIn("red_queen: {}",
                      (self.stage / "configuration.yaml").read_text())
        self.assertTrue((self.stage / "custom_components/red_queen").is_dir())
        self.assertEqual(json.loads(
            (self.stage / ".storage/core.entity_registry").read_text()
        )["data"]["entities"][0]["entity_id"], "light.wnhf_lamp")
        self.assertNotIn("NEVER_SHOW_THIS", json.dumps(report))
        self.assertNotIn("SECRET_DASHBOARD", json.dumps(report))
        with self.assertRaises(tool.SitePreflightError):
            self.run_it()

    def test_reject_live_source_and_path_overlap(self):
        with self.assertRaises(tool.SitePreflightError):
            tool.rehearse(
                self.live, self.stage, self.rollback, self.live, self.package,
                expected_entities=1, expected_devices=1,
            )
        with self.assertRaises(tool.SitePreflightError):
            tool.rehearse(
                self.source, self.live / "stage", self.rollback,
                self.live, self.package,
                expected_entities=1, expected_devices=1,
            )
        self.assertFalse(self.stage.exists())
        self.assertFalse(self.rollback.exists())

    def test_refuse_shared_output_parent_with_user_secrets(self):
        shared = self.root / "shared"
        shared.mkdir(mode=0o755)
        shared.chmod(0o755)
        with self.assertRaises(tool.SitePreflightError):
            tool.rehearse(
                self.source, shared / "stage", self.rollback,
                self.live, self.package,
                expected_entities=1, expected_devices=1,
            )
        self.assertFalse((shared / "stage").exists())

    def test_reject_count_drift_without_writing_anywhere(self):
        with self.assertRaises(tool.SitePreflightError):
            self.run_it(entities=245)
        with self.assertRaises(tool.SitePreflightError):
            self.run_it(devices=36)
        self.assertFalse(self.stage.exists())
        self.assertFalse(self.rollback.exists())

    def test_missing_legacy_store_is_a_hard_stop(self):
        (self.source / ".storage/wnhf.smart_living").unlink()
        with self.assertRaises(tool.SitePreflightError):
            self.run_it()
        self.assertFalse(self.stage.exists())

    def test_symlink_or_missing_backup_package_is_a_hard_stop(self):
        (self.source / "other").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(tool.SitePreflightError):
            self.run_it()
        self.assertFalse(self.stage.exists())


if __name__ == "__main__":
    unittest.main()
