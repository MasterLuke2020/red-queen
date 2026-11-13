"""Home Assistant sun/time event tracking for Red Queen Smart Lighting 1.2.

Opt-in only. Trackers are removed on config-entry unload. Startup never
replays or issues an ON command. Trigger callbacks only schedule async work.
"""
from __future__ import annotations

from collections import deque
from datetime import UTC, datetime, timedelta
import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.start import async_at_started
from homeassistant.util import dt as dt_util
from homeassistant.helpers.event import (
    async_track_sunrise,
    async_track_sunset,
    async_track_time_change,
    async_track_state_change_event,
)

from .smart_living_automation_logic import (
    automation_permission, should_reconcile_missed_off,
    active_outdoor_fallback,
)

_LOGGER = logging.getLogger(__name__)


class SmartLightingScheduler:
    """Own schedule subscriptions and serial, allowlisted scene dispatch."""

    def __init__(self, hass: HomeAssistant, runtime: Any) -> None:
        self.hass = hass
        self.runtime = runtime
        self.rules: dict[str, dict[str, Any]] = {}
        self.audit: deque[dict[str, Any]] = deque(maxlen=100)
        self._listeners: list[Any] = []
        self._running_rules: set[str] = set()
        # Serialize all rules to avoid overlapping ON/OFF dispatches from
        # distinct rules touching the same WAGO/HA physical source.
        self._dispatch_lock = asyncio.Lock()
        self._queued_rules: set[str] = set()
        self.blocked_rules: dict[str, str] = {}
        self._started = False

    def async_start(self, rules: dict[str, dict[str, Any]]) -> None:
        """Register rules without firing anything on startup."""
        if self._started:
            raise RuntimeError("Smart Lighting scheduler already started")
        self.blocked_rules.clear()
        for rule in rules.values():
            if not rule["enabled"]:
                continue
            targets = self.runtime.scenes[rule["scene_id"]]["lights"]
            invalid = set(targets) - set(self.runtime.scene_targets)
            if invalid:
                self.blocked_rules[rule["id"]] = (
                    "Missing Smart Living light source(s): "
                    + ", ".join(sorted(invalid))
                )
                _LOGGER.warning(
                    "Red Queen Smart Lighting rule %s suspended: %s",
                    rule["id"], self.blocked_rules[rule["id"]],
                )
        self.rules = rules
        self._started = True
        try:
            for rule in rules.values():
                if not rule["enabled"] or rule["id"] in self.blocked_rules:
                    continue
                rule_id = rule["id"]
                trigger = rule["trigger"]
                if trigger["type"] == "time":
                    hour, minute = map(int, trigger["at"].split(":"))

                    @callback
                    def on_time(_when: datetime, _id: str = rule_id) -> None:
                        self._queue(_id)

                    unsubscribe = async_track_time_change(
                        self.hass, on_time, hour=hour, minute=minute, second=0,
                    )
                elif trigger["type"] == "state":

                    @callback
                    def on_state(event: Any, _id: str = rule_id,
                                 _target: str = trigger["to"]) -> None:
                        previous = event.data.get("old_state")
                        current = event.data.get("new_state")
                        # Ignore restore/initial state and unknown -> on/off;
                        # only real available transitions can start a scene.
                        if previous is None or current is None:
                            return
                        if previous.state not in {"on", "off"}:
                            return
                        if current.state != _target or previous.state == _target:
                            return
                        self._queue(_id)

                    unsubscribe = async_track_state_change_event(
                        self.hass, [trigger["entity_id"]], on_state,
                    )
                else:

                    @callback
                    def on_sun(_when: datetime, _id: str = rule_id) -> None:
                        self._queue(_id)

                    helper = (
                        async_track_sunrise
                        if trigger["event"] == "sunrise"
                        else async_track_sunset
                    )
                    unsubscribe = helper(
                        self.hass, on_sun,
                        offset=timedelta(minutes=trigger["offset_minutes"]),
                    )
                self._listeners.append(unsubscribe)
            if any(
                rule["enabled"] and rule.get("reconcile_missed_off", False)
                and rule["id"] not in self.blocked_rules
                for rule in rules.values()
            ):
                # Also invokes callback immediately when HA is already running
                # (e.g., integration reloaded). Off-only, never an ON replay.
                @callback
                def on_started(_hass: HomeAssistant) -> None:
                    self._reconcile_night_off()

                self._listeners.append(async_at_started(self.hass, on_started))
        except Exception:
            self.async_stop()
            raise

    @callback
    def _queue(self, rule_id: str) -> None:
        if self._started:
            self.hass.async_create_task(
                self.async_fire(rule_id),
                f"Red Queen Smart Lighting rule {rule_id}",
            )

    def _reconcile_night_off(self) -> None:
        if not self._started:
            return
        sun = self.hass.states.get("sun.sun")
        sun_state = sun.state if sun is not None else None
        local_now = dt_util.now()
        for rule in self.rules.values():
            if rule["id"] in self.blocked_rules:
                continue
            if should_reconcile_missed_off(
                rule, local_now=local_now, sun_state=sun_state,
            ):
                self._queue(rule["id"])

    def _permission(self, rule: dict[str, Any]) -> tuple[bool, str]:
        # Operator confirmed both HA 1.1-compatible fallback automations
        # active. Interlock only overlapping outdoor scenes. Never toggle
        # an existing HA automation without explicit operator action.
        if rule["scene_id"] in self.runtime.scenes:
            targets = self.runtime.scenes[rule["scene_id"]]["lights"]
            if active_outdoor_fallback(
                self.hass.states.async_all("automation"), targets,
            ):
                return False, "ha_outdoor_fallback_still_active"
        # A manually operated HA input_boolean pauses automatic ON only.
        # Unknown/unavailable helper state fails closed. Targeted OFF is
        # still allowed, including the opt-in missed-night recovery.
        pause_entity_id = getattr(self.runtime, "manual_pause_entity_id", None)
        if rule["action"] == "on" and pause_entity_id is not None:
            pause = self.hass.states.get(pause_entity_id)
            if pause is None or pause.state not in {"on", "off"}:
                return False, "manual_pause_unavailable"
            if pause.state == "on":
                return False, "manual_pause_active"
        state = self.hass.states.get(self.runtime.quiet_entity_id)
        return automation_permission(
            rule, self.runtime.mode, self.runtime.quiet,
            quiet_state=state.state if state is not None else None,
        )

    def async_stop(self) -> None:
        """Unsubscribe before services and entities are unloaded."""
        self._started = False
        for unsubscribe in self._listeners:
            unsubscribe()
        self._listeners.clear()
        # Queued tasks check _started again before any dispatch.

    def snapshot(self) -> dict[str, Any]:
        return {
            "started": self._started,
            "rules": [
                {
                    "id": rule["id"],
                    "name": rule["name"],
                    "enabled": rule["enabled"],
                    "scene_id": rule["scene_id"],
                    "action": rule["action"],
                    "trigger": dict(rule["trigger"]),
                    "allowed_modes": list(rule["allowed_modes"]),
                    "allow_quiet": rule["allow_quiet"],
                    "reconcile_missed_off": rule.get("reconcile_missed_off", False),
                }
                for rule in self.rules.values()
            ],
            "listener_count": len(self._listeners),
            "manual_pause_entity_id": getattr(
                self.runtime, "manual_pause_entity_id", None
            ),
            "blocked_rules": dict(self.blocked_rules),
            "recent": list(self.audit),
        }

    async def async_fire(self, rule_id: str) -> dict[str, Any]:
        """Serialize light rules, suppressing duplicate events per rule."""
        if rule_id in self._queued_rules:
            return {"status": "already_running", "rule_id": rule_id}
        self._queued_rules.add(rule_id)
        try:
            async with self._dispatch_lock:
                return await self._async_fire_serial(rule_id)
        finally:
            self._queued_rules.discard(rule_id)

    async def _async_fire_serial(self, rule_id: str) -> dict[str, Any]:
        """Handle a real HA event, never from initial setup or scene selection.

        Re-evaluate mode/quiet before every individual HA call, skip disabled
        and overlapping rules, and never call the whole-house lighting off.
        """
        rule = self.rules.get(rule_id)
        if not self._started or rule is None:
            return {"status": "inactive", "rule_id": rule_id}
        if rule_id in self.blocked_rules:
            return {
                "status": "suppressed", "rule_id": rule_id,
                "reason": self.blocked_rules[rule_id],
            }
        if rule_id in self._running_rules:
            return {"status": "already_running", "rule_id": rule_id}
        self._running_rules.add(rule_id)
        results: list[dict[str, str]] = []
        record: dict[str, Any] = {
            "rule_id": rule_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "suppressed",
        }
        try:
            allowed, reason = self._permission(rule)
            if not allowed:
                record["reason"] = reason
                return record
            scene = self.runtime.scenes[rule["scene_id"]]
            # Preflight before the first action to avoid partial application
            # due to missing or deauthorized light bindings.
            plan: list[tuple[str, str, dict[str, Any]]] = []
            for entity_id, item in scene["lights"].items():
                if entity_id not in self.runtime.scene_targets:
                    record["reason"] = "scene_source_not_allowlisted"
                    return record
                state = self.hass.states.get(entity_id)
                if state is None or state.state not in {"on", "off"}:
                    record["reason"] = "scene_source_unavailable"
                    return record
                if rule["action"] == "off":
                    service, params = "turn_off", {}
                else:
                    service = (
                        "turn_on" if item["state"] == "on" else "turn_off"
                    )
                    params = self.runtime.validate_scene_light_request(
                        entity_id, service,
                        item["attributes"] if service == "turn_on" else {},
                        state,
                    )
                plan.append((entity_id, service, params))
            for entity_id, service, params in plan:
                if not self._started:
                    results.append({
                        "entity_id": entity_id, "status": "stopped",
                    })
                    break
                allowed, reason = self._permission(rule)
                if not allowed:
                    results.append({
                        "entity_id": entity_id,
                        "status": "suppressed",
                        "reason": reason,
                    })
                    break
                state = self.hass.states.get(entity_id)
                if state is None or state.state not in {"on", "off"}:
                    results.append({
                        "entity_id": entity_id,
                        "status": "unavailable",
                    })
                    continue
                if service == "turn_off" and state.state == "off":
                    results.append({
                        "entity_id": entity_id,
                        "status": "already_off",
                    })
                    continue
                try:
                    await self.runtime.async_light_dispatch(
                        entity_id, service, params,
                    )
                except Exception as err:
                    _LOGGER.warning(
                        "Red Queen Smart Lighting %s: %s failed for %s",
                        rule_id, type(err).__name__, entity_id,
                    )
                    results.append({
                        "entity_id": entity_id, "status": "failed",
                        "reason": type(err).__name__,
                    })
                    continue
                results.append({
                    "entity_id": entity_id,
                    "status": "accepted_dispatch_not_physically_verified",
                })
            incomplete = any(item["status"] in {
                "suppressed", "stopped", "failed", "unavailable",
            } for item in results)
            record["status"] = "partial" if incomplete else "dispatched"
            record["results"] = results
            record["physically_verified"] = False
            return record
        except Exception as err:
            _LOGGER.exception(
                "Red Queen Smart Lighting rule %s failed", rule_id,
            )
            record["status"] = "failed"
            record["reason"] = type(err).__name__
            return record
        finally:
            self.audit.append(dict(record))
            self._running_rules.discard(rule_id)
