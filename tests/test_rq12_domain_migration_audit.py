"""Safety and regression tests for the Red Queen 1.2 domain migration inventory."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "rq12_domain_migration_audit.py"
spec = importlib.util.spec_from_file_location("rq12_domain_migration_audit", SCRIPT)
assert spec is not None and spec.loader is not None
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def write_registry(root: Path, name: str, data: dict) -> None:
    storage = root / ".storage"
    storage.mkdir(parents=True, exist_ok=True)
    (storage / name).write_text(json.dumps({"data": data}), encoding="utf-8")


class MigrationAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        write_registry(self.root, "core.config_entries", {
            "entries": [{"domain": "wnhf", "entry_id": "entry1",
                         "data": {"token": "SECRET_NOT_FOR_OUTPUT"}}]
        })
        write_registry(self.root, "core.entity_registry", {
            "entities": [{"platform": "wnhf", "config_entry_id": "entry1",
                          "entity_id": "light.wnhf_hof_up_down",
                          "unique_id": "wnhf_hof_up_down"}]
        })
        write_registry(self.root, "core.device_registry", {
            "devices": [{"identifiers": [["wnhf", "framework"]],
                         "config_entries": ["entry1"]}]
        })
        (self.root / "automations.yaml").write_text(
            "- service: wnhf.smart_scene_activate\n"
            "- alias: SECRET_NOT_FOR_OUTPUT\n", encoding="utf-8"
        )

    def test_impact_and_no_mutation_or_secret_output(self) -> None:
        paths = list(self.root.rglob("*"))
        original = {str(p): p.read_bytes() for p in paths if p.is_file()}
        report = audit.inspect(self.root)
        self.assertEqual(report["status"], "inventory_complete")
        self.assertEqual(report["counts"]["old_config_entries"], 1)
        self.assertEqual(report["counts"]["old_platform_entities"], 1)
        self.assertEqual(report["counts"]["old_domain_device_identifiers"], 1)
        self.assertEqual(report["counts"]["entities_linked_to_old_entry"], 1)
        self.assertEqual(report["counts"]["proposed_entity_id_changes"], 1)
        self.assertEqual(report["reference_counts_by_file"]["automations.yaml"], 1)
        self.assertEqual(
            report["sample_proposed_entity_id_changes"][0]["to"],
            "light.red_queen_hof_up_down",
        )
        self.assertNotIn("SECRET_NOT_FOR_OUTPUT", json.dumps(report))
        self.assertEqual(original, {
            str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()
        })

    def test_duplicate_domain_is_blocker(self) -> None:
        write_registry(self.root, "core.config_entries", {
            "entries": [{"domain": "wnhf", "entry_id": "entry1"},
                        {"domain": "red_queen", "entry_id": "entry2"}]
        })
        report = audit.inspect(self.root)
        self.assertEqual(report["status"], "needs_review")
        self.assertTrue(any("red_queen config entry" in x for x in report["blockers"]))

    def test_id_collision_is_blocker(self) -> None:
        write_registry(self.root, "core.entity_registry", {"entities": [
            {"platform": "wnhf", "config_entry_id": "entry1",
             "entity_id": "light.wnhf_hof_up_down"},
            {"platform": "other", "entity_id": "light.red_queen_hof_up_down"},
        ]})
        report = audit.inspect(self.root)
        self.assertEqual(report["counts"]["entity_id_collisions"], 1)
        self.assertEqual(report["status"], "needs_review")

    def test_broken_registry_is_blocker_without_exception_details(self) -> None:
        (self.root / ".storage" / "core.device_registry").write_text(
            "{not json}", encoding="utf-8"
        )
        report = audit.inspect(self.root)
        self.assertEqual(report["status"], "needs_review")
        self.assertEqual(len(report["errors"]), 1)
        self.assertNotIn("{not json}", json.dumps(report))

    def test_missing_root_is_safe(self) -> None:
        report = audit.inspect(self.root / "missing")
        self.assertEqual(report["status"], "invalid_path")
        self.assertTrue(report["blockers"])

    def test_foreign_platform_prefix_is_not_renamed(self) -> None:
        write_registry(self.root, "core.entity_registry", {"entities": [
            {"platform": "wnhf", "config_entry_id": "entry1",
             "entity_id": "light.wnhf_hof_up_down"},
            {"platform": "automation", "config_entry_id": None,
             "entity_id": "automation.wnhf_channel_voice"},
        ]})
        report = audit.inspect(self.root)
        self.assertEqual(report["counts"]["proposed_entity_id_changes"], 1)
        self.assertEqual(report["counts"]["foreign_wnhf_prefix_entity_ids"], 1)
        self.assertEqual(report["sample_foreign_wnhf_prefix_entity_ids"],
                         ["automation.wnhf_channel_voice"])


if __name__ == "__main__":
    unittest.main()
