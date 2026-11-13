"""Contract checks for the in-development Red Queen integration-domain package.

These tests do not connect to a running Home Assistant installation.
"""
from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path
import sys
import types
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

    def test_release_candidate_metadata_is_consistent(self) -> None:
        manifest = json.loads((PKG / "manifest.json").read_text(encoding="utf-8"))
        release = json.loads((PKG / "RELEASE.json").read_text(encoding="utf-8"))
        const = (PKG / "const.py").read_text(encoding="utf-8")
        self.assertEqual(manifest["version"], "1.2.0-rc1")
        self.assertEqual(manifest["domain"], "red_queen")
        self.assertEqual(release["version"], manifest["version"])
        self.assertEqual(release["candidate"], manifest["version"])
        self.assertEqual(release["technical_domain"], "red_queen")
        self.assertEqual(release["canonical_execution_service"],
                         "red_queen.execution_execute")
        self.assertEqual(release["candidate_status"], "development")
        self.assertIn('VERSION = "1.2.0-rc1"', const)
        self.assertIn('RELEASE_CHANNEL = "candidate"', const)
        self.assertIn('RELEASE_PHASE = "rc"', const)
        self.assertIn('RELEASE_CANDIDATE = "1.2.0-rc1"', const)

    def test_release_profiles_advertise_real_services_and_safe_migration(self) -> None:
        # Load only the pure release modules, deliberately bypassing the
        # Home Assistant integration __init__ and any runtime/device setup.
        module_name = "_rq12_release_contract_test"
        stub = types.ModuleType(module_name)
        stub.__path__ = [str(PKG)]
        sys.modules[module_name] = stub
        try:
            profile_module = importlib.import_module(module_name + ".release_candidate")
            profile = profile_module.ReleaseProfile
            info = profile.release_info()
            api = profile.public_api()
            upgrade = profile.upgrade_check()
            scope = profile_module.ReleaseScopeManager.snapshot()
        finally:
            for key in tuple(sys.modules):
                if key == module_name or key.startswith(module_name + "."):
                    del sys.modules[key]

        self.assertEqual(info["framework"]["version"], "1.2.0-rc1")
        self.assertEqual(info["framework"]["channel"], "candidate")
        self.assertEqual(info["framework"]["phase"], "rc")
        self.assertEqual(info["framework"]["candidate"], "1.2.0-rc1")
        self.assertEqual(info["framework"]["phase_name"], "Release Candidate 1.2.0-rc1")
        self.assertTrue(info["compatibility"]["migration_required"])
        self.assertEqual(info["canonical_execution"]["service"], "red_queen.execution_execute")
        self.assertEqual(info["legacy_execution"]["service"], "red_queen.execute")
        self.assertEqual(info["release_policy"]["canonical_execution_entry"],
                         "red_queen.execution_execute")

        self.assertEqual((scope["channel"], scope["phase"]), ("candidate", "rc"))
        self.assertEqual((api["release_channel"], api["release_phase"]),
                         ("candidate", "rc"))
        self.assertEqual(api["policy"]["productive_execution_entry"],
                         "red_queen.execution_execute")
        self.assertEqual(api["policy"]["legacy_execution_entry"], "red_queen.execute")
        for category in ("stable", "diagnostic", "maintenance", "legacy_or_development"):
            with self.subTest(category=category):
                self.assertTrue(api[category], "Service category unexpectedly empty")
                self.assertTrue(all(
                    item["service"].startswith("red_queen.") for item in api[category]
                ))

        self.assertEqual((upgrade["release_channel"], upgrade["release_phase"]),
                         ("candidate", "rc"))
        self.assertTrue(upgrade["migration_required"])
        self.assertTrue(upgrade["restart_required_after_install"])
        self.assertEqual(upgrade["configuration"]["custom_configuration_path"],
                         "/config/wnhf")  # Historical data path must survive.
        instructions = " ".join(upgrade["instructions"])
        self.assertIn("docs/RED_QUEEN_1_2_CUTOVER_CHECKLIST.md", instructions)
        self.assertIn("custom_components/red_queen", instructions)
        self.assertIn("stop home assistant", instructions.lower())
        self.assertNotIn("Replace only custom_components/wnhf", instructions)

    def test_python_package_parses(self) -> None:
        for path in PKG.rglob("*.py"):
            with self.subTest(path=path.relative_to(PKG)):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


if __name__ == "__main__":
    unittest.main()
