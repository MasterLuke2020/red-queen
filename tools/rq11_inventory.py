#!/usr/bin/env python3
"""Read-only inventory for Red Queen 1.1.0.

Run INSIDE the Home Assistant container, where /config is mounted and PyYAML
is already installed. This script never calls an HA service, writes files,
reads credentials/config entries, or sends data over the network.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml


ROOT = Path("/config")
REGISTRY_DIR = Path("wnhf/house/registry")
ENTITY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z0-9_]+$")
DISCOVERY_TERMS = re.compile(
    r"rgbw?|dali|led|light|licht|farbe|colour|color|dim|helligkeit|"
    r"weiss|weiß|white|ruhe|quiet|nacht|night|anwes|presence|scene|szene",
    re.IGNORECASE,
)
MAX_DISCOVERY_ENTITIES = 750
SAFE_ENTITY_DOMAINS = {"light", "media_player", "notify", "tts"}
OPCUA_PLATFORMS = {"asyncua", "opcua", "wago"}


def entity_id(value: Any) -> str | None:
    """Include only syntactically valid HA entity identifiers."""
    return value if isinstance(value, str) and ENTITY_RE.fullmatch(value) else None


def load_json(path: Path, warnings: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        warnings.append(label + ": not found")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("not an object")
        return data
    except (OSError, UnicodeError, ValueError) as exc:
        warnings.append(label + ": unreadable (" + type(exc).__name__ + ")")
        return {}


def load_yaml(path: Path, warnings: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("not a mapping")
        return data
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        warnings.append(label + ": unreadable (" + type(exc).__name__ + ")")
        return {}


def yaml_collection(
    root: Path, filename: str, key: str, warnings: list[str]
) -> dict[str, Any]:
    path = root / REGISTRY_DIR / filename
    raw = load_yaml(path, warnings, filename)
    items = raw.get(key, [])
    if not isinstance(items, list):
        warnings.append(filename + ": expected list '" + key + "'")
        items = []
    return {"present": path.is_file(), "count": len(items), "items": items}


def light_summary(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    command = item.get("command")
    state = item.get("state")
    states = item.get("states")
    refs = []
    if isinstance(state, dict):
        refs.append(entity_id(state.get("entity_id")))
    if isinstance(states, list):
        refs.extend(
            entity_id(source.get("entity_id"))
            for source in states
            if isinstance(source, dict)
        )
    return {
        "id": item.get("id") if isinstance(item.get("id"), str) else None,
        "name": item.get("name") if isinstance(item.get("name"), str) else None,
        "room": item.get("room") if isinstance(item.get("room"), str) else None,
        "enabled": item.get("enabled", True) is True,
        "control_mode": item.get("control_mode", "monitor_only"),
        "command_entity_id": (
            entity_id(command.get("entity_id"))
            if isinstance(command, dict)
            else None
        ),
        "state_entity_ids": sorted({ref for ref in refs if ref}),
    }


def notification_summary(root: Path, warnings: list[str]) -> dict[str, Any]:
    path = root / REGISTRY_DIR / "notification_targets.yaml"
    raw = load_yaml(path, warnings, "notification_targets.yaml")
    result: dict[str, Any] = {
        "present": path.is_file(), "notification_targets": [],
        "announcement_targets": [], "routes": [],
    }
    for item in raw.get("notification_targets", []):
        if isinstance(item, dict):
            result["notification_targets"].append({
                "id": item.get("id"),
                "enabled": item.get("enabled", True) is True,
                "entity_id": entity_id(item.get("entity_id")),
            })
    for item in raw.get("announcement_targets", []):
        if not isinstance(item, dict):
            continue
        levels = item.get("levels", {})
        result["announcement_targets"].append({
            "id": item.get("id"),
            "enabled": item.get("enabled", True) is True,
            "provider": item.get("provider"),
            "tts_entity_id": entity_id(item.get("tts_entity_id")),
            "levels": {
                key: {
                    "speakers": [
                        valid for ref in value.get("speakers", [])
                        if (valid := entity_id(ref)) is not None
                    ] if isinstance(value.get("speakers"), list) else [],
                    "volume": value.get("volume") if isinstance(
                        value.get("volume"), (int, float)
                    ) else None,
                }
                for key, value in (levels.items() if isinstance(levels, dict) else [])
                if isinstance(key, str) and isinstance(value, dict)
            },
        })
    for item in raw.get("notification_routes", []):
        if not isinstance(item, dict):
            continue
        context = item.get("context")
        context = context if isinstance(context, dict) else {}
        result["routes"].append({
            "id": item.get("id"),
            "enabled": item.get("enabled", True) is True,
            "notification_target_ids": item.get("notification_target_ids", []),
            "announcement_target_id": item.get("announcement_target_id"),
            "quiet_mode_entity_id": entity_id(context.get("quiet_mode_entity_id")),
            "house_state_entity_id": entity_id(context.get("house_state_entity_id")),
            "voice_blocked_states": context.get("voice_blocked_states", []),
        })
    return result


def configurations_summary(root: Path, warnings: list[str]) -> dict[str, Any]:
    result = {}
    for key, folder in {
        "custom_context_rules": "wnhf/contexts/rules",
        "policies": "wnhf/policies",
        "decisions": "wnhf/decisions",
    }.items():
        directory = root / folder
        entries = []
        if directory.is_dir():
            for file in sorted((*directory.glob("*.yaml"), *directory.glob("*.yml"))):
                raw = load_yaml(file, warnings, key + "/" + file.name)
                if key == "policies" and file.name == "settings.yaml":
                    entries.append({
                        "file": file.name, "mode": raw.get("mode", "monitor")
                    })
                    continue
                ids = []
                for field in ("rules", "policies", "decisions"):
                    values = raw.get(field)
                    if isinstance(values, list):
                        ids.extend(
                            value["id"] for value in values
                            if isinstance(value, dict)
                            and isinstance(value.get("id"), str)
                        )
                for field in ("rule", "policy", "decision"):
                    value = raw.get(field)
                    if isinstance(value, dict) and isinstance(value.get("id"), str):
                        ids.append(value["id"])
                entries.append({"file": file.name, "ids": ids})
        result[key] = entries
    return result


def entity_registry_summary(
    root: Path, mapped_entities: set[str], warnings: list[str]
) -> dict[str, Any]:
    raw = load_json(
        root / ".storage/core.entity_registry",
        warnings, "core.entity_registry"
    )
    data = raw.get("data")
    items = data.get("entities", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        warnings.append("core.entity_registry: malformed entities list")
        items = []

    by_domain: Counter[str] = Counter()
    by_platform: Counter[str] = Counter()
    candidates = []
    for item in items:
        if not isinstance(item, dict):
            continue
        eid = entity_id(item.get("entity_id"))
        if eid is None:
            continue
        domain = eid.split(".", 1)[0]
        platform = item.get("platform", "")
        platform = platform if isinstance(platform, str) else ""
        by_domain[domain] += 1
        by_platform[platform] += 1
        interesting = (
            domain in SAFE_ENTITY_DOMAINS
            or eid in mapped_entities
            or platform.lower() in OPCUA_PLATFORMS
            or (domain in {"number", "select", "button", "sensor", "binary_sensor",
                           "input_boolean", "input_select"}
                and DISCOVERY_TERMS.search(eid) is not None)
        )
        if interesting:
            candidates.append({
                "entity_id": eid,
                "platform": platform,
                "disabled": item.get("disabled_by") is not None,
            })

    candidates.sort(key=lambda item: item["entity_id"])
    return {
        "total": sum(by_domain.values()),
        "by_domain": dict(sorted(by_domain.items())),
        "by_platform": dict(by_platform.most_common(30)),
        "selected_count": len(candidates),
        "selected_truncated": len(candidates) > MAX_DISCOVERY_ENTITIES,
        "selected_entities": candidates[:MAX_DISCOVERY_ENTITIES],
        "note": "Static entity registry only. Live states and supported_color_modes "
                "are NOT collected.",
    }


def build_report(root: Path = ROOT) -> dict[str, Any]:
    """Produce a structured, local-only report without modifying installation."""
    warnings: list[str] = []
    manifest = load_json(
        root / "custom_components/wnhf/manifest.json",
        warnings, "Red Queen manifest"
    )
    collections = {
        name: yaml_collection(root, name + ".yaml", name, warnings)
        for name in ("rooms", "lights", "covers", "openings", "plants")
    }
    rooms = [
        {
            "id": room.get("id"), "name": room.get("name"),
            "floor": room.get("floor"), "enabled": room.get("enabled", True) is True
        }
        for room in collections["rooms"]["items"]
        if isinstance(room, dict)
    ]
    lights = [
        summary for item in collections["lights"]["items"]
        if (summary := light_summary(item)) is not None
    ]
    notifications = notification_summary(root, warnings)
    mapped = set()
    for light in lights:
        mapped.update(light["state_entity_ids"])
        if light["command_entity_id"]:
            mapped.add(light["command_entity_id"])
    for target in notifications["notification_targets"]:
        if target["entity_id"]:
            mapped.add(target["entity_id"])
    for target in notifications["announcement_targets"]:
        if target["tts_entity_id"]:
            mapped.add(target["tts_entity_id"])
        for level in target["levels"].values():
            mapped.update(level["speakers"])

    try:
        ha_version = version("homeassistant")
    except PackageNotFoundError:
        ha_version = "not available"
    return {
        "schema": "redqueen.inventory.1.1.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "home_assistant_version": ha_version,
            "red_queen_version": manifest.get("version", "unknown"),
            "inside_home_assistant_container": (root / ".storage").is_dir(),
        },
        "registries": {
            "rooms": rooms,
            "lights": lights,
            "counts": {
                key: {"present": value["present"], "count": value["count"]}
                for key, value in collections.items()
            },
            "notifications": notifications,
        },
        "rules_and_policies": configurations_summary(root, warnings),
        "entity_registry": entity_registry_summary(root, mapped, warnings),
        "warnings": warnings,
        "not_collected": [
            "passwords, tokens, credentials, and Home Assistant config entries",
            "secrets.yaml, configuration.yaml, logs, network addresses",
            "live entity states, location/presence tracking and device registry",
            "OPC UA unique IDs/node IDs and PLC project source",
        ],
    }


def main() -> int:
    if not (ROOT / "wnhf/house/registry").is_dir():
        print("ERROR: Red Queen registry not found under /config. "
              "Run inside the production Home Assistant container.", file=sys.stderr)
        return 2
    try:
        report = build_report()
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as exc:
        print("ERROR: inventory failed (" + type(exc).__name__ + ")",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
