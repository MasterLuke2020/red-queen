"""Pure validation and safety policy for Red Queen 1.2 scheduled scenes.

No Home Assistant imports and no side effects. Intentional explicit opt-in:
all new rules default to disabled and have home/quiet safety defaults.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

_ID = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_HHMM = re.compile(r"(?P<h>[01][0-9]|2[0-3]):(?P<m>[0-5][0-9])\Z")
_MODES = frozenset({"home", "away", "vacation"})
_TRIGGER_ENTITY = re.compile(r"(?:binary_sensor|input_boolean)\.[a-z0-9_]+\Z")
_ALLOWED_KEYS = frozenset({
    "id", "name", "enabled", "scene_id", "action", "trigger",
    "allowed_modes", "allow_quiet", "reconcile_missed_off",
})


def parse_automation_rules(
    raw: Any, scenes: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Validate a narrow, deterministic set of scheduled light operations.

    Only references to existing, separately validated Smart Living scenes may
    be used. Unknown keys and malformed triggers fail validation.
    """
    if raw is None:
        return {}
    if not isinstance(raw, list) or len(raw) > 64:
        raise ValueError("automations must be a list of at most 64 rules")
    result: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict) or set(item) - _ALLOWED_KEYS:
            raise ValueError("automation contains unknown keys or is not a mapping")
        rule_id = item.get("id")
        name = item.get("name")
        if not isinstance(rule_id, str) or not _ID.fullmatch(rule_id):
            raise ValueError("invalid automation id")
        if rule_id in result:
            raise ValueError("duplicate automation id")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError("automation name must contain 1..80 characters")
        enabled = item.get("enabled", False)
        if type(enabled) is not bool:
            raise ValueError("automation enabled must be boolean")
        scene_id = item.get("scene_id")
        if not isinstance(scene_id, str) or scene_id not in scenes:
            raise ValueError("automation references unknown scene")
        action = item.get("action")
        if not isinstance(action, str) or action not in {"on", "off"}:
            raise ValueError("automation action must be on/off")
        trigger = item.get("trigger")
        if not isinstance(trigger, dict) or "type" not in trigger:
            raise ValueError("automation trigger must be a mapping")
        kind = trigger["type"]
        if kind == "time":
            if set(trigger) != {"type", "at"}:
                raise ValueError("time trigger requires only 'type' and 'at'")
            at = trigger["at"]
            if not isinstance(at, str) or not _HHMM.fullmatch(at):
                raise ValueError("time must be a local HH:MM string")
            normalized = {"type": "time", "at": at}
        elif kind == "sun":
            if set(trigger) - {"type", "event", "offset_minutes"} or (
                set(trigger) - {"offset_minutes"} != {"type", "event"}
            ):
                raise ValueError("sun trigger keys invalid")
            event = trigger["event"]
            offset = trigger.get("offset_minutes", 0)
            if not isinstance(event, str) or event not in {"sunrise", "sunset"}:
                raise ValueError("sun event must be sunrise/sunset")
            if type(offset) is not int or not -120 <= offset <= 120:
                raise ValueError("sun offset_minutes must be integer -120..120")
            normalized = {
                "type": "sun", "event": event, "offset_minutes": offset,
            }
        elif kind == "state":
            if set(trigger) != {"type", "entity_id", "to"}:
                raise ValueError("state trigger requires type, entity_id, to")
            entity_id = trigger["entity_id"]
            target = trigger["to"]
            if not isinstance(entity_id, str) or not _TRIGGER_ENTITY.fullmatch(entity_id):
                raise ValueError("state trigger only supports binary_sensor/input_boolean")
            if not isinstance(target, str) or target not in {"on", "off"}:
                raise ValueError("state trigger target must be on/off")
            normalized = {
                "type": "state", "entity_id": entity_id, "to": target,
            }
        else:
            raise ValueError("unsupported trigger type")
        modes = item.get("allowed_modes", ["home"])
        if (
            not isinstance(modes, list) or not modes or len(modes) > 3
            or any(not isinstance(m, str) or m not in _MODES for m in modes)
            or len(modes) != len(set(modes))
        ):
            raise ValueError("allowed_modes must be a nonempty list of unique house modes")
        quiet = item.get("allow_quiet", False)
        if type(quiet) is not bool:
            raise ValueError("allow_quiet must be boolean")
        reconcile_off = item.get("reconcile_missed_off", False)
        if type(reconcile_off) is not bool:
            raise ValueError("reconcile_missed_off must be boolean")
        # Night-time recovery is deliberately restricted to explicitly opted
        # in, evening-clock OFF rules. Never catch up an ON command or a
        # morning/daytime OFF rule from a previous date.
        if reconcile_off and (
            action != "off" or normalized["type"] != "time"
            or int(normalized["at"][:2]) < 18
        ):
            raise ValueError("reconcile_missed_off requires evening time OFF")
        result[rule_id] = {
            "id": rule_id, "name": name.strip(), "enabled": enabled,
            "scene_id": scene_id, "action": action, "trigger": normalized,
            "allowed_modes": tuple(modes), "allow_quiet": quiet,
            "reconcile_missed_off": reconcile_off,
        }
    return result


def automation_permission(
    rule: dict[str, Any], mode: str, quiet: bool,
    *, quiet_state: str | None = None,
) -> tuple[bool, str]:
    """Keep legacy/manual scene guards intact; scheduled off is always safe.

    Scheduled ON requires explicit opt-ins for away, vacation and quiet.
    Scheduled OFF is allowed in any house/quiet mode, but only for the targets
    of its configured scene. It never calls whole-house all-off.
    """
    if not rule["enabled"]:
        return False, "rule_disabled"
    if rule["action"] == "off":
        return True, "targeted_off_allowed"
    if mode not in rule["allowed_modes"]:
        return False, "house_mode_not_allowed"
    if quiet:
        if not rule["allow_quiet"]:
            return False, "quiet_mode_not_allowed"
        # Unknown/unavailable quiet sensor must never silently grant an ON,
        # even when night-time use was explicitly opted in.
        if quiet_state != "on":
            return False, "quiet_sensor_unavailable"
    return True, "scheduled_on_allowed"



def should_reconcile_missed_off(
    rule: dict[str, Any], *, local_now: datetime, sun_state: str | None,
) -> bool:
    """Allow only opted-in targeted night OFF; never replay ON at startup.

    No persistent timestamp is required: the recovery is idempotent because
    the scheduler skips already-off entities. HA must provide an aware local
    datetime and an explicitly below-horizon sun sensor. This purposefully
    does not reissue daytime OFF or ON commands.
    """
    if not rule.get("enabled") or not rule.get("reconcile_missed_off", False):
        return False
    trigger = rule.get("trigger", {})
    if rule.get("action") != "off" or trigger.get("type") != "time":
        return False
    if sun_state != "below_horizon":
        return False
    if local_now.tzinfo is None or local_now.utcoffset() is None:
        return False
    at = trigger.get("at")
    if not isinstance(at, str) or not _HHMM.fullmatch(at):
        return False
    hour, minute = map(int, at.split(":"))
    if hour < 18:
        return False
    cutoff = hour * 60 + minute
    current = local_now.hour * 60 + local_now.minute
    return current >= cutoff or current < 12 * 60
