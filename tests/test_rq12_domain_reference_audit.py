"""No-HA regression tests for the read-only domain reference inventory."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / "tools/rq12_domain_reference_audit.py"
SPEC = importlib.util.spec_from_file_location("rq12_domain_reference_audit", SRC)
assert SPEC and SPEC.loader
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


class DomainReferenceAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".storage").mkdir()

    def test_yaml_recognizes_only_service_invocations(self):
        content = (
            "wnhf: {}\n"
            "logger:\n  logs:\n    custom_components.wnhf: info\n"
            "script:\n  - service: wnhf.lighting_all_off\n"
            "  - action: 'wnhf.smart_scene_activate'\n"
            "entity_id: light.wnhf_hof_up_down\n"
            "name: SECRET_TEST_DO_NOT_PRINT\n"
        )
        path = self.root / "configuration.yaml"
        path.write_text(content, encoding="utf-8")
        original = path.read_bytes()
        report = tool.audit(self.root)
        self.assertEqual(report["totals"]["literal_service_calls"], 2)
        self.assertEqual(report["totals"]["root_domain_keys"], 1)
        self.assertEqual(report["totals"]["entity_id_mentions"], 1)
        self.assertEqual(report["totals"]["legacy_logger_keys"], 1)
        self.assertFalse(report["manual_review_required"])
        self.assertNotIn("SECRET_TEST_DO_NOT_PRINT", json.dumps(report))
        self.assertEqual(path.read_bytes(), original)

    def test_five_known_loggers_are_not_service_calls_or_unknowns(self):
        path = self.root / "packages/wnhf/channels.yaml"
        path.parent.mkdir(parents=True)
        path.write_text(
            'logger: wnhf.channel_log\n'
            '  logger: "wnhf.channel_voice"\n'
            "  logger: 'wnhf.notify' # audit\n"
            '  logger: wnhf.channel_router\n'
            '  logger: wnhf.voice_driver\n',
            encoding="utf-8",
        )
        report = tool.audit(self.root)
        self.assertEqual(report["totals"]["logger_channel_mentions"], 5)
        self.assertEqual(report["totals"]["literal_service_calls"], 0)
        self.assertEqual(report["totals"]["unclassified_dotted_mentions"], 0)
        self.assertEqual(report["unclassified_locations"], [])
        self.assertFalse(report["manual_review_required"])

    def test_unknown_logger_channel_still_requires_manual_review(self):
        (self.root / "scripts.yaml").write_text(
            "logger: wnhf.mystery\n", encoding="utf-8"
        )
        report = tool.audit(self.root)
        self.assertTrue(report["manual_review_required"])
        self.assertEqual(report["totals"]["unclassified_dotted_mentions"], 1)
        self.assertEqual(len(report["unclassified_locations"]), 1)

    def test_detect_template_as_review_blocker(self):
        (self.root / "automations.yaml").write_text(
            "- service_template: '{{ \"wnhf.\" ~ states(\"input_text.service\") }}'\n",
            encoding="utf-8"
        )
        report = tool.audit(self.root)
        self.assertTrue(report["manual_review_required"])
        self.assertGreater(report["totals"]["template_or_domain_calls"], 0)

    def test_lovelace_nested_service_vs_entity(self):
        doc = {"data": {"config": {"views": [
            {"cards": [
                {"tap_action": {"action": "call-service",
                                "service": "wnhf.lighting_all_off"},
                 "entity": "light.wnhf_hof"},
                {"hold_action": {"action": "wnhf.smart_scene_activate"},
                 "entity": "binary_sensor.wnhf_house_ready"},
            ]}
        ]}}}
        path = self.root / ".storage/lovelace.red-queen"
        path.write_text(json.dumps(doc), encoding="utf-8")
        report = tool.audit(self.root)
        self.assertEqual(report["totals"]["literal_service_calls"], 2)
        self.assertEqual(report["totals"]["entity_id_mentions"], 2)
        self.assertFalse(report["manual_review_required"])

    def test_ignores_own_component_code_and_store_contents(self):
        cc = self.root / "custom_components/wnhf"
        cc.mkdir(parents=True)
        (cc / "const.py").write_text("SECRET_TOKEN = 'wnhf.internal'\n")
        (self.root / ".storage/wnhf.smart_living").write_text(
            '{"manual_mode":"home","secret":"NEVER_ECHO"}')
        report = tool.audit(self.root)
        self.assertEqual(report["files_examined"], 0)
        self.assertEqual(report["legacy_store_keys"], ["wnhf.smart_living"])
        self.assertNotIn("NEVER_ECHO", json.dumps(report))

    def test_unclassified_details_redact_secret_values(self):
        file = self.root / "packages/wnhf/notify.yaml"
        file.parent.mkdir(parents=True)
        file.write_text(
            "entry:\n"
            "  action: wnhf.valid_service\n"
            "  expression: '{{ wnhf.route_house(SECRET_VALUE_123) }}'\n"
            "  message: SECRET_DO_NOT_LOG\n"
            "  # wnhf.disabled_legacy\n",
            encoding="utf-8",
        )
        result = tool.audit(self.root)
        self.assertTrue(result["manual_review_required"])
        rows = result["unclassified_locations"]
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["line"] for r in rows], [3, 5])
        self.assertEqual(
            [r["reference"] for r in rows],
            ["wnhf.route_house", "wnhf.disabled_legacy"],
        )
        self.assertEqual(rows[0]["yaml_key"], "expression")
        self.assertEqual(rows[1]["classification"], "comment")
        serialized = json.dumps(result)
        self.assertNotIn("SECRET_VALUE_123", serialized)
        self.assertNotIn("SECRET_DO_NOT_LOG", serialized)
        self.assertNotIn("{{", serialized)

    def test_fails_closed_for_unparseable_lovelace(self):
        (self.root / ".storage/lovelace.lovelace").write_text("{bad json")
        with self.assertRaises(tool.ReferenceAuditError):
            tool.audit(self.root)


if __name__ == "__main__":
    unittest.main()
