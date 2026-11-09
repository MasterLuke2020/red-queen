"""Contract checks for the in-development Red Queen integration-domain package.

These tests do not connect to a running Home Assistant installation.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "red_queen"
LEGACY = ROOT / "custom_components" / "wnhf"


class DomainPackageTests(unittest.TestCase):
    def test_one_registered_integration_package(self) -> None:
        self.assertTrue(PKG.is_dir())
        self.assertFalse(LEGACY.exists(), "Never load both domain packages together")
        manifest = json.loads((PKG / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["domain"], PKG.name)
        self.assertEqual(manifest["name"], "Red Queen")

    def test_domain_is_explicit_and_legacy_identity_is_stable(self) -> None:
        constants = (PKG / "const.py").read_text(encoding="utf-8")
        self.assertIn('DOMAIN = "red_queen"', constants)
        # The old registry path stays intentionally stable during the staged
        # package test; it must be migrated only with a verified data cutover.
        self.assertIn('REGISTRY_ROOT = ("wnhf", "house", "registry")', constants)
        semantic = (PKG / "smart_lighting_semantic.py").read_text(encoding="utf-8")
        self.assertIn('from .const import DOMAIN', semantic)
        self.assertIn('getattr(entry, "platform", None) != DOMAIN', semantic)
        self.assertIn('return "wnhf_"', semantic)
        runtime = (PKG / "smart_living_runtime.py").read_text(encoding="utf-8")
        self.assertIn('entry.platform in {"wnhf", DOMAIN}', runtime)
        self.assertIn('eligible_ha_light_sources(', runtime)

    def test_service_route_and_test_harness_use_new_domain(self) -> None:
        renderer = (PKG / "dashboard_renderer.py").read_text(encoding="utf-8")
        self.assertIn('action=f"{DOMAIN}.lighting_all_off"', renderer)
        self.assertIn("from .const import DOMAIN", renderer)
        script = (ROOT / "tools" / "rq11_ci_ha_smoke.sh").read_text(encoding="utf-8")
        self.assertIn('red_queen: {}', script)
        self.assertIn("custom_components/red_queen", script)
        for script_name in (
            "rq12_ci_editor_flow.py", "rq12_ci_scheduler_flow.py",
            "rq12_ci_semantic_lights.py",
        ):
            source = (ROOT / "tools" / script_name).read_text(encoding="utf-8")
            self.assertNotIn("custom_components.wnhf", source)
            self.assertIn("custom_components.red_queen", source)

    def test_python_package_parses(self) -> None:
        for path in PKG.rglob("*.py"):
            with self.subTest(path=path.relative_to(PKG)):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


if __name__ == "__main__":
    unittest.main()
