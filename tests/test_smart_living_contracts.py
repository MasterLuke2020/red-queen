"""Cross-layer source contracts for Red Queen 1.1 comfort safety.

Pure static regression tests complement the real HA staging startup test and
dependency-free policy tests. They do not simulate actual DALI/Sonos delivery.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/wnhf"


def load_tree(name: str) -> ast.Module:
    return ast.parse((ROOT / name).read_text(encoding="utf-8"))


def find_function(tree: ast.AST, name: str) -> ast.AST:
    matches = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if len(matches) != 1:
        raise AssertionError(f"{name}: expected 1 function, found {len(matches)}")
    return matches[0]


def called_functions(node: ast.AST) -> set[str]:
    functions = set()
    for value in ast.walk(node):
        if not isinstance(value, ast.Call):
            continue
        name = value.func
        if isinstance(name, ast.Name):
            functions.add(name.id)
        elif isinstance(name, ast.Attribute):
            functions.add(name.attr)
    return functions


def literal_strings(node: ast.AST) -> set[str]:
    return {
        value.value for value in ast.walk(node)
        if isinstance(value, ast.Constant) and isinstance(value.value, str)
    }


class SmartLivingContractTests(unittest.TestCase):
    def test_dali_entities_are_not_duplicated_as_red_queen_proxy(self):
        tree = load_tree("light.py")
        names = {
            node.name for node in tree.body
            if isinstance(node, ast.ClassDef)
        }
        self.assertNotIn("WNHFSmartRGBWLight", names)
        binding = (ROOT / "dashboard_binding.py").read_text(encoding="utf-8")
        self.assertIn("entry.entity_id in allowed_sources", binding)
        self.assertIn("entry.platform != DOMAIN", binding)

    def test_all_scene_entrypoints_use_same_non_bypassable_guard(self):
        runtime = load_tree("smart_living_runtime.py")
        activate = find_function(runtime, "async_activate_scene")
        self.assertIn("permission", called_functions(activate))
        self.assertIn("lighting.automatic_scene", literal_strings(activate))
        self.assertNotIn("lighting.manual", literal_strings(activate))
        self.assertNotIn("automated", (ROOT / "services.yaml").read_text(encoding="utf-8").split("smart_scene_activate:", 1)[1].split("house_mode_snapshot:", 1)[0])
        services = load_tree("services.py")
        handler = find_function(services, "handle_smart_scene_activate")
        self.assertIn("async_activate_scene", called_functions(handler))
        self.assertNotIn("automated", literal_strings(handler))
        button = load_tree("button.py")
        scene_cls = next(x for x in button.body if isinstance(x, ast.ClassDef)
                         and x.name == "RedQueenActivateSceneButton")
        self.assertIn("async_activate_scene", called_functions(
            find_function(scene_cls, "async_press"),
        ))

    def test_new_message_route_guard_applies_to_validation_and_execute(self):
        provider = load_tree("providers/notifications.py")
        route = find_function(provider, "_route_plan")
        self.assertIn("route_voice_decision", called_functions(route))
        self.assertIn("smart_living", literal_strings(route))
        self.assertIn("_route_plan", called_functions(
            find_function(provider, "_technical_route"),
        ))
        self.assertIn("_technical_route", called_functions(
            find_function(provider, "_validate_route"),
        ))
        self.assertIn("_route_plan", called_functions(
            find_function(provider, "_execute_route"),
        ))
        for method in ("_technical_route", "_execute_route"):
            node = find_function(provider, method)
            call = next(
                value for value in ast.walk(node)
                if isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute)
                and value.func.attr == "_route_plan"
            )
            self.assertIn("source", {item.arg for item in call.keywords})
            self.assertIn("priority", {item.arg for item in call.keywords})

    def test_quiet_sensor_fail_closed_and_no_direct_light_write_on_setup(self):
        runtime = load_tree("smart_living_runtime.py")
        quiet = find_function(runtime, "quiet")
        self.assertIn("quiet_restriction", called_functions(quiet))
        setup = find_function(runtime, "async_setup")
        self.assertNotIn("async_light_dispatch", called_functions(setup))
        self.assertNotIn("async_activate_scene", called_functions(setup))


if __name__ == "__main__":
    unittest.main()
