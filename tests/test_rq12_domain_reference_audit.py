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

    def test_fails_closed_for_unparseable_lovelace(self):
        (self.root / ".storage/lovelace.lovelace").write_text("{bad json")
        with self.assertRaises(tool.ReferenceAuditError):
            tool.audit(self.root)


if __name__ == "__main__":
    unittest.main()
