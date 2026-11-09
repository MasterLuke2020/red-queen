"""Unit tests of pure domain registry transformation (no Home Assistant writes)."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "rq12_domain_registry_transform.py"
spec = importlib.util.spec_from_file_location("rq12_domain_registry_transform", SCRIPT)
assert spec and spec.loader
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def fixtures():
    return (
        {"version": 1, "data": {"entries": [
            {"domain": "wnhf", "entry_id": "rq-one", "data": {"secret": "keep-me"},
             "options": {"configured": True}},
            {"domain": "sun", "entry_id": "sun-one"},
        ]}},
        {"version": 1, "data": {"entities": [
            {"platform": "wnhf", "config_entry_id": "rq-one",
             "unique_id": "wnhf_room1", "entity_id": "light.wnhf_room1"},
            {"platform": "wnhf", "config_entry_id": "rq-one",
             "unique_id": "wnhf_room2", "entity_id": "light.hof_red_queen_room2"},
            {"platform": "automation", "config_entry_id": None,
             "entity_id": "automation.wnhf_channel_voice"},
        ]}},
        {"version": 1, "data": {"devices": [
            {"identifiers": [["wnhf", "framework"], ["other", "value"]],
             "config_entries": ["rq-one"], "id": "id1"},
            {"identifiers": [["sun", "abc"]], "config_entries": ["sun-one"]},
        ]}},
    )


class TransformTests(unittest.TestCase):
    def test_domain_only_preserves_entity_unique_and_config_ids(self):
        original = fixtures()
        untouched = deepcopy(original)
        transformed, counts = tool.plan_registry_transform(*original)
        self.assertEqual(original, untouched)
        self.assertEqual(counts, {
            "already_migrated": False, "entries": 1, "entities": 2,
            "devices": 1, "entity_ids_renamed": 0,
        })
        entry = transformed["core.config_entries"]["data"]["entries"][0]
        self.assertEqual(entry["domain"], "red_queen")
        self.assertEqual(entry["entry_id"], "rq-one")
        self.assertEqual(entry["data"]["secret"], "keep-me")
        ents = transformed["core.entity_registry"]["data"]["entities"]
        self.assertEqual(ents[0]["platform"], "red_queen")
        self.assertEqual(ents[0]["entity_id"], "light.wnhf_room1")
        self.assertEqual(ents[0]["unique_id"], "wnhf_room1")
        self.assertEqual(ents[1]["entity_id"], "light.hof_red_queen_room2")
        self.assertEqual(ents[2]["entity_id"], "automation.wnhf_channel_voice")
        self.assertEqual(ents[2]["platform"], "automation")
        devices = transformed["core.device_registry"]["data"]["devices"]
        self.assertEqual(devices[0]["identifiers"], [
            ["red_queen", "framework"], ["other", "value"]
        ])
        self.assertEqual(devices[1]["identifiers"], [["sun", "abc"]])

    def test_idempotent_when_fully_migrated(self):
        transformed, _ = tool.plan_registry_transform(*fixtures())
        again, counts = tool.plan_registry_transform(
            transformed["core.config_entries"],
            transformed["core.entity_registry"],
            transformed["core.device_registry"],
        )
        self.assertEqual(again, transformed)
        self.assertTrue(counts["already_migrated"])

    def test_reject_conflicting_config_entries(self):
        a, b, c = fixtures()
        a["data"]["entries"].append({"domain": "red_queen", "entry_id": "other"})
        with self.assertRaises(tool.DomainMigrationError):
            tool.plan_registry_transform(a, b, c)

    def test_reject_entity_wrong_entry(self):
        a, b, c = fixtures()
        b["data"]["entities"][0]["config_entry_id"] = "wrong"
        with self.assertRaises(tool.DomainMigrationError):
            tool.plan_registry_transform(a, b, c)

    def test_reject_device_identifier_collision(self):
        a, b, c = fixtures()
        c["data"]["devices"][1]["identifiers"].append(["red_queen", "framework"])
        with self.assertRaises(tool.DomainMigrationError):
            tool.plan_registry_transform(a, b, c)

    def test_reject_device_not_linked_to_old_entry(self):
        a, b, c = fixtures()
        c["data"]["devices"][0]["config_entries"] = ["other"]
        with self.assertRaises(tool.DomainMigrationError):
            tool.plan_registry_transform(a, b, c)

    def test_reject_partial_previous_migration(self):
        a, b, c = fixtures()
        a["data"]["entries"][0]["domain"] = "red_queen"
        with self.assertRaises(tool.DomainMigrationError):
            tool.plan_registry_transform(a, b, c)


if __name__ == "__main__":
    unittest.main()
