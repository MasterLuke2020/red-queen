"""Dependency-free operational tests for the combined Red Queen / DALI all-off."""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/red_queen"


def load_runtime_method():
    """Extract only the async method; no HA test backend or hardware required."""
    tree = ast.parse((ROOT / "smart_living_runtime.py").read_text(encoding="utf-8"))
    runtime = next(
        obj for obj in tree.body
        if isinstance(obj, ast.ClassDef) and obj.name == "SmartLivingRuntime"
    )
    method = next(
        obj for obj in runtime.body
        if isinstance(obj, ast.AsyncFunctionDef)
        and obj.name == "async_all_rgbw_off"
    )
    code = compile(
        ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
        str(ROOT / "smart_living_runtime.py"),
        "exec",
    )
    scope: dict[str, object] = {
        "Any": Any,
        "_LOGGER": SimpleNamespace(warning=lambda *args: None),
    }
    exec(code, scope)
    return scope["async_all_rgbw_off"]


class FakeSmartLiving:
    """Small test double for native HA light state and write acceptance."""

    def __init__(self, statuses: dict[str, str | None], failures=()) -> None:
        self.rgbw_targets = dict.fromkeys(statuses, "Test DALI")
        self.hass = SimpleNamespace(states=SimpleNamespace(get=self._get))
        self.states = statuses
        self.failures = set(failures)
        self.calls: list[tuple[str, str, dict]] = []
        # All-off must remain available during absence or quiet-hours.
        self.mode = "away"
        self.quiet = True

    def _get(self, entity_id: str):
        state = self.states.get(entity_id)
        return SimpleNamespace(state=state) if state is not None else None

    async def async_light_dispatch(self, entity_id: str, action: str, data: dict):
        self.calls.append((entity_id, action, data))
        if entity_id in self.failures:
            raise OSError("Simulated HA provider failure")


class SmartLivingAllOffTests(unittest.TestCase):
    def test_only_on_allowlisted_sources_are_dispatched_in_any_mode(self):
        subject = FakeSmartLiving({
            "light.dali_first_rgbw": "on",
            "light.dali_second_rgbw": "off",
            "light.dali_unavailable_rgbw": "unavailable",
            "light.dali_unknown_rgbw": "unknown",
            "light.dali_missing_rgbw": None,
        })
        result = asyncio.run(load_runtime_method()(subject))
        self.assertEqual(subject.calls, [
            ("light.dali_first_rgbw", "turn_off", {}),
        ])
        self.assertEqual(result["target_count"], 5)
        self.assertEqual(result["dispatched_count"], 1)
        self.assertEqual(result["failed_count"], 3)
        self.assertEqual(result["status"], "partial")
        self.assertFalse(result["physically_verified"])

    def test_one_failed_dali_does_not_block_other_lights(self):
        subject = FakeSmartLiving({
            "light.dali_bad_rgbw": "on",
            "light.dali_good_rgbw": "on",
        }, failures={"light.dali_bad_rgbw"})
        result = asyncio.run(load_runtime_method()(subject))
        self.assertEqual(len(subject.calls), 2)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(result["dispatched_count"], 1)
        self.assertEqual([x["status"] for x in result["results"]],
                         ["failed", "accepted_dispatch_not_verified"])

    def test_existing_all_off_service_and_dashboard_action_share_path(self):
        tree = ast.parse((ROOT / "services.py").read_text(encoding="utf-8"))
        handler = next(x for x in ast.walk(tree)
                       if isinstance(x, ast.AsyncFunctionDef)
                       and x.name == "handle_all_off")
        source = ast.unparse(handler)
        self.assertIn("engine.async_lighting_all_off()", source)
        self.assertIn("runtime.async_all_rgbw_off()", source)
        self.assertLess(source.index("engine.async_lighting_all_off()"),
                        source.index("runtime.async_all_rgbw_off()"))
        self.assertNotIn("async_activate_scene", source)

        renderer = (ROOT / "dashboard_renderer.py").read_text(encoding="utf-8")
        self.assertIn('action=f"{DOMAIN}.lighting_all_off"', renderer)
        self.assertIn("if model.features.lights or bindings.smart_lights:", renderer)
        self.assertIn("item.entity_id\n                for item in bindings.smart_lights", renderer)


if __name__ == "__main__":
    unittest.main()
