#!/usr/bin/env python3
"""Read-only HA entity registry inventory for Red Queen 1.2 Smart Lighting.

No Home Assistant API calls, no network, no writes, no secrets. Run on the
server with a path to the existing HA config directory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

KEYWORDS = (
    "aussen", "außen", "outside", "outdoor", "garten", "terrasse",
    "balkon", "eingang", "auffahrt", "fassade", "hof", "carport",
    "garage", "vorplatz", "wege", "weglicht",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", required=True,
        help="Home Assistant config directory, only .storage/core.entity_registry read",
    )
    args = parser.parse_args()
    config = Path(args.config).resolve()
    path = config / ".storage" / "core.entity_registry"
    if not path.is_file():
        print(f"ERROR: Entity registry not found: {path}", file=sys.stderr)
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data["data"]["entities"]
        if not isinstance(entries, list):
            raise ValueError("Wrong entity registry shape")
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"ERROR: Cannot parse entity registry: {type(exc).__name__}", file=sys.stderr)
        return 2
    all_lights, outside, outside_switches, legacy = [], [], [], []
    for item in entries:
        if not isinstance(item, dict):
            continue
        entity_id = item.get("entity_id", "")
        if not isinstance(entity_id, str):
            continue
        enabled = item.get("disabled_by") is None
        platform = str(item.get("platform") or "unknown")
        name = str(item.get("name") or item.get("original_name") or "—")
        text = (entity_id + " " + name).lower()
        info = (
            f"{entity_id:<58} | {platform:<16} | "
            f"{'ACTIVE' if enabled else 'DISABLED':<8} | {name[:52]}"
        )
        if entity_id.startswith("light."):
            all_lights.append(info)
            if any(word in text for word in KEYWORDS):
                outside.append(info)
        elif entity_id.startswith(("switch.", "button.")) and any(
            word in text for word in KEYWORDS
        ):
            outside_switches.append(info)
        if platform in {"wnhf", "red_queen"} and (
            "wnhf" in entity_id or "redqueen" in entity_id
        ):
            legacy.append((entity_id, name))

    print("=== RED QUEEN 1.2 – NUR LESEN / AUSSENBELEUCHTUNG ===")
    print("Hauptquelle: .storage/core.entity_registry")
    print(f"HA light entities : {len(all_lights)}")
    print(f"Exterior candidates: {len(outside)}")
    print()
    print("--- AUSSENLICHT-KANDIDATEN (light.*) ---")
    if outside:
        print("\n".join(sorted(outside)))
    else:
        print("Keine nach Namen/ID passenden Leuchten.")
    print()
    print("--- AUSSEN-SCHALTER (switch.* / button.*) ---")
    if outside_switches:
        print("\n".join(sorted(outside_switches)))
    else:
        print("Keine nach Namen/ID passenden Schalter.")
    print()
    print("--- ALLE LIGHT-ENTITAETEN ---")
    if all_lights:
        print("\n".join(sorted(all_lights)))
    else:
        print("Keine light.* Entitaeten in der HA Registry.")
    print()
    print(f"--- RED QUEEN WNHF-NAMEN: {len(legacy)} ---")
    for entity_id, name in sorted(legacy)[:100]:
        print(f"{entity_id} | {name}")
    if len(legacy) > 100:
        print(f"... plus {len(legacy)-100} weitere")
    print()
    print("Hinweis: Hier werden NUR Registry-Eintraege gelesen.")
    print("Kein aktueller Geraetestatus, keine SPS-/DALI-Befehle.")
    print("Automatik 1.2 akzeptiert aktuell native, allowlistete light.*")
    print("WNHF-Light-Proxys und switch/button-Entitaeten nicht direkt erlaubt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
