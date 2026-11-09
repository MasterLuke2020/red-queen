#!/usr/bin/env python3
"""Red Queen 1.2: read-only reference inventory for the old technical domain.

No HA imports, filesystem modifications, external network, or live API calls.
Reports only counts and relative paths; never reproduces configuration values.
This is an impact audit, not proof that every external reference is known.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any

OLD = "wnhf"
NEW = "red_queen"
MAX_FILES = 10000
YAML_SUFFIXES = {".yaml", ".yml"}
IGNORED_PARTS = {"custom_components", "deps", "www", "tts", "media",
                 "backups", ".git", "__pycache__"}
SERVICE_LINE = re.compile(
    r"""(?m)^\s*(?:-\s*)?(?:service|action|perform_action)\s*:\s*"""
    r"""['"]?wnhf\.([a-z][a-z0-9_]*)['"]?(?:\s*(?:#.*)?)$"""
)
TEMPLATE_LINE = re.compile(
    r"(?mi)^\s*(?:-\s*)?(?:service_template|action_template|domain)\s*:.*wnhf\."
)
ROOT_KEY = re.compile(r"(?m)^wnhf\s*:")
LOGGER_KEY = re.compile(r"(?m)^\s*['\"]?custom_components\.wnhf['\"]?\s*:")
ENTITY_ID = re.compile(
    r"(?<![a-z0-9_])(?:light|sensor|binary_sensor|switch|button|"
    r"select|text|lock|cover|automation|number|input_boolean|input_text)"
    r"\.wnhf_[a-z0-9_]+"
)
DOTTED_DOMAIN = re.compile(r"(?<![a-z0-9_])wnhf\.[a-z][a-z0-9_]+")
WNHF_PREFIX = re.compile(r"(?<![a-z0-9_])wnhf_[a-z0-9_]+")
STORE_NAMES = ("wnhf.dashboard", "wnhf.smart_living", "wnhf.smart_lighting_editor")
SERVICE_KEYS = {"service", "action", "perform_action", "service_template",
                "action_template", "domain"}


class ReferenceAuditError(ValueError):
    """Read-only audit cannot reliably examine the selected input."""


def _read_source(path: Path) -> str:
    if path.is_symlink():
        raise ReferenceAuditError("Symlinked configuration file: " + path.name)
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ReferenceAuditError("Cannot read configuration source: " + path.name) from exc


def _yaml_counts(text: str, *, root: bool) -> Counter[str]:
    counts: Counter[str] = Counter()
    counts["literal_service_calls"] = len(SERVICE_LINE.findall(text))
    counts["template_or_domain_calls"] = len(TEMPLATE_LINE.findall(text))
    counts["entity_id_mentions"] = len(ENTITY_ID.findall(text))
    counts["legacy_logger_keys"] = len(LOGGER_KEY.findall(text))
    counts["root_domain_keys"] = len(ROOT_KEY.findall(text)) if root else 0
    counts["legacy_prefix_mentions"] = len(WNHF_PREFIX.findall(text))
    counts["legacy_dotted_mentions"] = len(DOTTED_DOMAIN.findall(text))
    # This is a conservative approximation, not a parser. Report unclassified
    # references for manual review instead of silently claiming they migrated.
    counts["unclassified_dotted_mentions"] = max(
        0, counts["legacy_dotted_mentions"] - counts["literal_service_calls"]
        - counts["template_or_domain_calls"] - counts["legacy_logger_keys"]
    )
    return counts


def _json_counts(obj: Any) -> Counter[str]:
    counts: Counter[str] = Counter()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, value in item.items():
                if key in SERVICE_KEYS and isinstance(value, str):
                    if re.fullmatch(r"wnhf\.[a-z][a-z0-9_]*", value):
                        counts["literal_service_calls"] += 1
                    elif "wnhf." in value:
                        counts["template_or_domain_calls"] += 1
                visit(value)
        elif isinstance(item, list):
            for value in item:
                visit(value)
        elif isinstance(item, str):
            counts["entity_id_mentions"] += len(ENTITY_ID.findall(item))
            counts["legacy_prefix_mentions"] += len(WNHF_PREFIX.findall(item))
            counts["legacy_dotted_mentions"] += len(DOTTED_DOMAIN.findall(item))
            counts["legacy_logger_keys"] += len(LOGGER_KEY.findall(item))
    visit(obj)
    counts["unclassified_dotted_mentions"] = max(
        0, counts["legacy_dotted_mentions"] - counts["literal_service_calls"]
        - counts["template_or_domain_calls"] - counts["legacy_logger_keys"]
    )
    return counts


def _candidate_files(root: Path) -> list[Path]:
    collected: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root)
        if not rel.parts or any(p in IGNORED_PARTS for p in rel.parts):
            continue
        if ".storage" in rel.parts:
            if len(rel.parts) == 2 and rel.name.startswith("lovelace"):
                collected.append(path)
            continue
        if path.suffix.lower() in YAML_SUFFIXES:
            collected.append(path)
    if len(collected) > MAX_FILES:
        raise ReferenceAuditError("Too many configuration sources; audit explicitly")
    return collected


def audit(config: Path) -> dict[str, Any]:
    root = config.resolve()
    if not root.is_dir():
        raise ReferenceAuditError("Home Assistant configuration directory not found")
    summaries: list[dict[str, Any]] = []
    totals: Counter[str] = Counter()
    for path in _candidate_files(root):
        relative = path.relative_to(root).as_posix()
        if path.name.startswith("lovelace") and path.parent == root / ".storage":
            try:
                parsed = json.loads(_read_source(path))
            except ValueError as exc:
                raise ReferenceAuditError(
                    "Malformed Lovelace storage JSON: " + relative
                ) from exc
            counts = _json_counts(parsed)
            kind = "lovelace"
        else:
            counts = _yaml_counts(
                _read_source(path), root=(relative == "configuration.yaml")
            )
            kind = "yaml"
        if any(counts.values()):
            totals.update(counts)
            summaries.append({"file": relative, "kind": kind,
                              "counts": dict(counts)})
    storage = root / ".storage"
    old_stores = sorted(name for name in STORE_NAMES
                        if (storage / name).is_file())
    new_stores = sorted(name.replace("wnhf.", "red_queen.")
                        for name in STORE_NAMES
                        if (storage / name.replace("wnhf.", "red_queen.")).is_file())
    unresolved = sum(
        totals[name] for name in (
            "template_or_domain_calls", "unclassified_dotted_mentions"
        )
    )
    return {
        "schema_version": 1,
        "mode": "READ_ONLY_NO_CHANGES",
        "domain": {"current": OLD, "target": NEW},
        "files_examined": len(_candidate_files(root)),
        "totals": dict(totals),
        "manual_review_required": unresolved > 0,
        "legacy_store_keys": old_stores,
        "new_store_keys": new_stores,
        "legacy_data_directory_exists": (root / "wnhf").is_dir(),
        "new_data_directory_exists": (root / "red_queen").is_dir(),
        "files_with_legacy_references": summaries,
        "limits": [
            "Counts are heuristic, not a full YAML semantic parse",
            "External integrations, scripts outside HA /config and PLC mappings not examined",
            "Existing entity IDs may intentionally retain wnhf_ prefixes",
            "Do not use this report alone to authorize a live domain cutover",
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only domain reference inventory")
    p.add_argument("--config", required=True, type=Path)
    args = p.parse_args()
    try:
        result = audit(args.config)
    except (ReferenceAuditError, OSError) as err:
        print("REFUSED: " + str(err), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
