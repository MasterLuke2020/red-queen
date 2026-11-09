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
# Exactly the application-specific log-channel tags found in the real house
# audit on 2026-11-09. Do not rewrite arbitrary wnhf.* YAML values.
KNOWN_LOGGER_CHANNELS = frozenset({
    "wnhf.channel_log", "wnhf.channel_voice", "wnhf.notify",
    "wnhf.channel_router", "wnhf.voice_driver",
})
LOGGER_CHANNEL_RE = re.compile(
    r"""(?m)^(?P<head>[ \t]*(?:-[ \t]+)?logger[ \t]*:[ \t]*)"""
    r"""(?P<quote>['"]?)(?P<value>wnhf\.[a-z][a-z0-9_]*)"""
    r"""(?P=quote)(?P<tail>[ \t]*(?:#.*)?)$"""
)
LOGGER_CONTAINING_WNHF_RE = re.compile(
    r"(?m)^[ \t]*(?:-[ \t]+)?logger[ \t]*:.*wnhf\."
)



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
    counts["logger_channel_mentions"] = sum(
        1 for match in LOGGER_CHANNEL_RE.finditer(text)
        if match.group("value") in KNOWN_LOGGER_CHANNELS
    )
    counts["root_domain_keys"] = len(ROOT_KEY.findall(text)) if root else 0
    counts["legacy_prefix_mentions"] = len(WNHF_PREFIX.findall(text))
    counts["legacy_dotted_mentions"] = len(DOTTED_DOMAIN.findall(text))
    # This is a conservative approximation, not a parser. Report unclassified
    # references for manual review instead of silently claiming they migrated.
    counts["unclassified_dotted_mentions"] = max(
        0, counts["legacy_dotted_mentions"] - counts["literal_service_calls"]
        - counts["template_or_domain_calls"] - counts["legacy_logger_keys"] - counts["logger_channel_mentions"]
    )
    return counts


# Only safe structural context is emitted. Never print full YAML lines, Jinja
# expressions, credentials, phone numbers, full service payloads, or comments.
YAML_KEY = re.compile(r"^\s*(?:-\s*)?([a-zA-Z_][a-zA-Z_0-9-]{0,63})\s*:")


def _unclassified_yaml_locations(text: str, relative: str) -> list[dict[str, Any]]:
    """Pinpoint dotted references without exposing any surrounding values."""
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        mentions = list(DOTTED_DOMAIN.finditer(line))
        if not mentions:
            continue
        exact_service = SERVICE_LINE.fullmatch(line) is not None
        template_service = TEMPLATE_LINE.fullmatch(line) is not None
        recognized_logger = LOGGER_CHANNEL_RE.fullmatch(line)
        if (exact_service or template_service or
            (recognized_logger is not None and
             recognized_logger.group("value") in KNOWN_LOGGER_CHANNELS)):
            continue
        key = YAML_KEY.match(line)
        classification = (
            "comment" if line.lstrip().startswith("#")
            else "yaml_value_or_expression"
        )
        for match in mentions:
            rows.append({
                "file": relative,
                "line": number,
                "yaml_key": key.group(1) if key else None,
                "reference": match.group(0),
                "classification": classification,
            })
    return rows


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
    unresolved_locations: list[dict[str, Any]] = []
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
            yaml_text = _read_source(path)
            counts = _yaml_counts(
                yaml_text, root=(relative == "configuration.yaml")
            )
            unresolved_locations.extend(
                _unclassified_yaml_locations(yaml_text, relative)
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
        "unclassified_locations": unresolved_locations[:80],
        "unclassified_locations_truncated": len(unresolved_locations) > 80,
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
    p.add_argument("--unclassified-only", action="store_true",
                   help="Print only redacted locations of unresolved wnhf.* references")
    args = p.parse_args()
    try:
        result = audit(args.config)
    except (ReferenceAuditError, OSError) as err:
        print("REFUSED: " + str(err), file=sys.stderr)
        return 2
    if args.unclassified_only:
        result = {
            "mode": result["mode"],
            "manual_review_required": result["manual_review_required"],
            "unclassified_total": result["totals"].get(
                "unclassified_dotted_mentions", 0
            ),
            "locations": result["unclassified_locations"],
            "truncated": result["unclassified_locations_truncated"],
            "note": "No YAML values, Jinja expressions, tokens or credentials printed",
        }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
