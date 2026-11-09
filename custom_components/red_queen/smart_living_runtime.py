"""Optional Smart Living runtime for Red Queen 1.1.

Preserves all stable 1.0 semantic registry and execution routes. RGBW is a
separate, opt-in HA light adapter with a strict source-entity allowlist.
"""
from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from pathlib import Path
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
import yaml

from .smart_living_logic import (
    HOUSE_MODES, exposed_modes, permission, resolve_mode,
    quiet_restriction, validate_light_request, parse_scenes,
)
from .smart_living_messages import SmartMessageComposer
from .smart_living_automation_logic import parse_automation_rules
from .smart_living_automation import SmartLightingScheduler
from .smart_lighting_semantic import resolve_semantic_light_bindings
from .native_execution import async_execute_canonical
from .const import DATA_ENGINE, DOMAIN
from .smart_living_editor import (
    SmartLightingEditorStore, scenes_to_raw, rules_to_raw,
    validate_editor_document,
)

_LOGGER = logging.getLogger(__name__)
SIGNAL_SMART_LIVING_UPDATED = "wnhf_smart_living_updated"
DATA_SMART_LIVING = "smart_living"
STORAGE_VERSION = 1
STORAGE_KEY = "wnhf.smart_living"
AUTO_DALI_RE = re.compile(r"^light\.dali_[a-z0-9_]+_rgbw$")
ENTITY_RE = re.compile(r"^light\.[a-z0-9_]+$")


class SmartLivingRuntime:
    """Small resident-override layer; no external polling or presence tracking."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.manual_mode = "home"
        self.auto_away = False
        self.away_entity_id = "binary_sensor.datawebstateabwesenheit"
        self.quiet_entity_id = "binary_sensor.wnhf_quiet_mode_active"
        self.manual_pause_entity_id: str | None = None
        self.rgbw_targets: dict[str, str] = {}
        # Independent allowlist: native Red Queen ON/OFF lights mapped only
        # via registry Unique IDs, never via another light service proxy.
        self.semantic_targets: dict[str, str] = {}
        self.audit: deque[dict[str, Any]] = deque(maxlen=100)
        self._target_locks: dict[str, Any] = {}
        self.composer = SmartMessageComposer(hass, self)
        self.scenes: dict[str, dict[str, Any]] = {}
        self.selected_scene: str | None = None
        self.automation_rules: dict[str, dict[str, Any]] = {}
        self.scheduler = SmartLightingScheduler(hass, self)
        self.editor = SmartLightingEditorStore(hass)

    async def async_setup(self) -> None:
        """Read only settings; persisted mode is saved after explicit user input."""
        persisted = await self.store.async_load()
        if isinstance(persisted, dict) and persisted.get("manual_mode") in HOUSE_MODES:
            self.manual_mode = persisted["manual_mode"]
        config = await self.hass.async_add_executor_job(self._read_config)
        self.auto_away = config["auto_away"]
        self.away_entity_id = config["away_entity_id"]
        self.quiet_entity_id = config["quiet_entity_id"]
        self.manual_pause_entity_id = config["manual_pause_entity_id"]
        self.composer.route_id = config["message_route_id"]
        self._discover_targets(config["rgbw_entity_ids"], config["discover_dali"])
        self._discover_semantic_targets()
        self.scenes = config["scenes"]
        self.selected_scene = next(iter(self.scenes), None)
        self.automation_rules = config["automations"]
        # The GUI store takes precedence ONLY after an explicit edit. Keep
        # existing manual YAML as an untouched recovery baseline.
        stored = await self.editor.async_load()
        if stored is not None:
            try:
                self.scenes, self.automation_rules = validate_editor_document(
                    stored["scenes"], stored["automations"],
                    set(self.scene_targets), require_sources=False,
                )
            except ValueError as err:
                raise HomeAssistantError(
                    "Smart Lighting editor data invalid: " + str(err)
                ) from err
            self.selected_scene = next(iter(self.scenes), None)
        # Report bad bindings without taking the whole integration down;
        # the scheduler skips affected rules and never dispatches their scene.
        for rule in self.automation_rules.values():
            if not rule["enabled"]:
                continue
            scene_sources = set(self.scenes[rule["scene_id"]]["lights"])
            missing = scene_sources - set(self.scene_targets)
            if missing:
                _LOGGER.warning(
                    "Smart Lighting automation %s suspended: missing source(s): %s",
                    rule["id"], ", ".join(sorted(missing)),
                )
        _LOGGER.info(
            "Smart Living ready: %s RGBW bindings; auto-away=%s",
            len(self.rgbw_targets), self.auto_away,
        )

    def _read_config(self) -> dict[str, Any]:
        path = Path(self.hass.config.path("wnhf", "smart_living.yaml"))
        raw: dict[str, Any] = {}
        if path.is_file():
            try:
                result = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except (OSError, UnicodeError, yaml.YAMLError) as err:
                raise HomeAssistantError("Invalid Smart Living configuration") from err
            if not isinstance(result, dict):
                raise HomeAssistantError("Smart Living configuration root must be a mapping")
            raw = result
        config = {
            "auto_away": raw.get("auto_away", False),
            "away_entity_id": raw.get(
                "away_entity_id", "binary_sensor.datawebstateabwesenheit"
            ),
            "quiet_entity_id": raw.get(
                "quiet_entity_id", "binary_sensor.wnhf_quiet_mode_active"
            ),
            "discover_dali": raw.get("discover_dali", True),
            "manual_pause_entity_id": raw.get("manual_pause_entity_id"),
            "rgbw_entity_ids": raw.get("rgbw_entity_ids", []),
            "message_route_id": raw.get("message_route_id", "notification.route.house"),
            "scenes": raw.get("scenes", []),
            "automations": raw.get("automations", []),
        }
        if type(config["auto_away"]) is not bool or type(config["discover_dali"]) is not bool:
            raise HomeAssistantError("auto_away/discover_dali must be boolean")
        if not isinstance(config["rgbw_entity_ids"], list) or any(
            not isinstance(x, str) or not ENTITY_RE.fullmatch(x)
            for x in config["rgbw_entity_ids"]
        ):
            raise HomeAssistantError("rgbw_entity_ids must be valid light entity IDs")
        try:
            config["scenes"] = parse_scenes(config["scenes"])
        except ValueError as err:
            raise HomeAssistantError("Smart Living scenes invalid: " + str(err)) from err
        try:
            config["automations"] = parse_automation_rules(
                config["automations"], config["scenes"],
            )
        except ValueError as err:
            raise HomeAssistantError("Smart Lighting automations invalid: " + str(err)) from err
        if not isinstance(config["message_route_id"], str) or not re.fullmatch(
            r"^notification\.route\.[a-z0-9_]+$", config["message_route_id"]
        ):
            raise HomeAssistantError("message_route_id must be a semantic route ID")
        pause = config["manual_pause_entity_id"]
        if pause is not None and (
            not isinstance(pause, str)
            or not re.fullmatch(r"^input_boolean\.[a-z0-9_]+$", pause)
        ):
            raise HomeAssistantError(
                "manual_pause_entity_id must be an input_boolean or omitted"
            )
        for key in ("away_entity_id", "quiet_entity_id"):
            value = config[key]
            if not isinstance(value, str) or not re.fullmatch(
                r"^binary_sensor\.[a-z0-9_]+$", value
            ):
                raise HomeAssistantError(key + " must be a binary_sensor entity ID")
        return config

    def _discover_targets(self, explicit: list[str], discover_dali: bool) -> None:
        registry = er.async_get(self.hass)
        discovered = {}
        for entry in registry.entities.values():
            entity_id = entry.entity_id
            if not entity_id.startswith("light.") or entry.disabled_by is not None:
                continue
            auto = (
                discover_dali and entry.platform == "asyncua"
                and AUTO_DALI_RE.fullmatch(entity_id) is not None
            )
            if auto or entity_id in explicit:
                if entry.platform == DOMAIN:
                    raise HomeAssistantError("Recursive Red Queen light binding rejected")
                discovered[entity_id] = entity_id.removeprefix("light.").replace("_", " ").title()
        missing = sorted(set(explicit) - set(discovered))
        if missing:
            raise HomeAssistantError(
                "Smart Living light bindings missing/disabled: " + ", ".join(missing)
            )
        self.rgbw_targets = dict(sorted(discovered.items()))

    def _discover_semantic_targets(self) -> None:
        """Use native unique IDs to map existing Red Queen entities to objects."""
        domain_data = self.hass.data.get(DOMAIN, {})
        engine = domain_data.get(DATA_ENGINE)
        entry_id = domain_data.get("config_entry_id")
        if engine is None or not isinstance(entry_id, str):
            self.semantic_targets = {}
            return
        registry = er.async_get(self.hass)
        house = engine._require_house()
        self.semantic_targets = resolve_semantic_light_bindings(
            registry.entities.values(), house.enabled_lights, entry_id,
        )

    @property
    def scene_targets(self) -> dict[str, str]:
        """HA light IDs allowed in configured scenes (native + semantic)."""
        return {
            **self.rgbw_targets,
            **{
                entity_id: f"Red Queen – {object_id}"
                for entity_id, object_id in self.semantic_targets.items()
            },
        }

    def validate_scene_light_request(
        self, entity_id: str, service: str, attributes: dict[str, Any],
        state: Any,
    ) -> dict[str, Any]:
        """Semantic Red Queen lights are strictly ON/OFF, no RGB or dimming."""
        if service not in {"turn_on", "turn_off"}:
            raise HomeAssistantError("Unsupported scene light service")
        if entity_id in self.semantic_targets:
            if attributes:
                raise HomeAssistantError(
                    "Red Queen semantic light supports on/off only: " + entity_id
                )
            return {}
        if entity_id not in self.rgbw_targets:
            raise HomeAssistantError("Scene light source not allowlisted")
        if service == "turn_off":
            return {}
        try:
            return validate_light_request(
                exposed_modes(state.attributes.get("supported_color_modes")),
                attributes,
            )
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

    @property
    def mode(self) -> str:
        value = self.hass.states.get(self.away_entity_id)
        signal = value.state if value is not None else None
        return resolve_mode(self.manual_mode, signal, self.auto_away)[0]

    @property
    def quiet(self) -> bool:
        state = self.hass.states.get(self.quiet_entity_id)
        return quiet_restriction(state.state if state is not None else None)

    def snapshot(self) -> dict[str, Any]:
        state = self.hass.states.get(self.away_entity_id)
        mode, source = resolve_mode(
            self.manual_mode, state.state if state is not None else None,
            self.auto_away,
        )
        questions = ("lighting.manual", "lighting.automatic_scene",
                     "notifications.mobile", "notifications.announce")
        return {
            "mode": mode,
            "mode_source": source,
            "manual_mode": self.manual_mode,
            "quiet": self.quiet,
            "quiet_input_state": (
                self.hass.states.get(self.quiet_entity_id).state
                if self.hass.states.get(self.quiet_entity_id) is not None
                else "missing"
            ),
            "automatic_away_enabled": self.auto_away,
            "away_input_state": state.state if state is not None else "missing",
            "permissions": {
                question: dict(zip(
                    ("allowed", "reason"),
                    permission(mode, quiet=self.quiet, category=question),
                ))
                for question in questions
            },
            "rgbw_targets": [
                {"entity_id": key, "name": name}
                for key, name in self.rgbw_targets.items()
            ],
            "semantic_targets": [
                {"entity_id": key, "object_id": value}
                for key, value in self.semantic_targets.items()
            ],
            "dispatch_audit_count": len(self.audit),
            "message_route_id": self.composer.route_id,
            "message_audit_count": len(self.composer.audit),
            "selected_scene": self.selected_scene,
            "automations": {
                "enabled_count": sum(
                    rule["enabled"] for rule in self.automation_rules.values()
                ),
                "rule_count": len(self.automation_rules),
                "listener_count": len(self.scheduler._listeners),
                "recent": list(self.scheduler.audit),
            },
            "scenes": [{"id": x["id"], "name": x["name"],
                        "target_count": len(x["lights"])}
                       for x in self.scenes.values()],
        }

    def editor_document(self) -> dict[str, list[dict[str, Any]]]:
        """Read-only, normalized view for the Smart Lighting options flow."""
        return {
            "scenes": scenes_to_raw(self.scenes),
            "automations": rules_to_raw(self.automation_rules),
        }

    def async_start_automations(self) -> None:
        """Arm only explicitly enabled rules, never trigger on startup."""
        self.scheduler.async_start(self.automation_rules)

    def async_stop_automations(self) -> None:
        """Remove event listeners on integration unload."""
        self.scheduler.async_stop()

    async def async_set_mode(self, mode: str) -> None:
        if mode not in HOUSE_MODES:
            raise HomeAssistantError("Unsupported Smart Living mode")
        old = self.manual_mode
        self.manual_mode = mode
        try:
            await self.store.async_save({"manual_mode": mode})
        except Exception:
            self.manual_mode = old
            raise
        async_dispatcher_send(self.hass, SIGNAL_SMART_LIVING_UPDATED)

    async def async_light_dispatch(
        self, source_entity_id: str, service: str, attributes: dict[str, Any]
    ) -> None:
        """Only dispatch to verified, allowlisted source lights.

        A successful HA service call proves accepted dispatch, NOT physical
        completion. All light actions are user-initiated through native HA light.
        """
        import asyncio

        if source_entity_id not in self.scene_targets:
            raise HomeAssistantError("Scene light source not allowlisted")
        if service not in {"turn_on", "turn_off"}:
            raise HomeAssistantError("Unsupported RGBW service")
        state = self.hass.states.get(source_entity_id)
        if state is None or state.state not in {"on", "off"}:
            raise HomeAssistantError("Scene light source is unavailable")
        if not self.hass.services.has_service("light", service):
            raise HomeAssistantError("Home Assistant light service unavailable")
        params = self.validate_scene_light_request(
            source_entity_id, service, attributes, state,
        )
        lock = self._target_locks.setdefault(source_entity_id, asyncio.Lock())
        async with lock:
            stamp = datetime.now(UTC).isoformat()
            outcome = {
                "timestamp": stamp,
                "target": source_entity_id,
                "action": service,
                "status": "rejected",
            }
            try:
                if source_entity_id in self.semantic_targets:
                    # Exactly the same canonical guarded path as the native
                    # Red Queen LightEntity, without any proxy recursion.
                    await async_execute_canonical(
                        self.hass,
                        action_id=(
                            "lighting.turn_on" if service == "turn_on"
                            else "lighting.turn_off"
                        ),
                        object_id=self.semantic_targets[source_entity_id],
                    )
                else:
                    await self.hass.services.async_call(
                        "light", service, {"entity_id": source_entity_id, **params},
                        blocking=True,
                    )
                outcome["status"] = "accepted_dispatch_not_verified"
            except Exception as err:
                outcome["reason"] = type(err).__name__
                raise
            finally:
                self.audit.append(outcome)

    async def async_all_rgbw_off(self) -> dict[str, Any]:
        """Turn off native Smart Living RGBW lights for the whole-house off action.

        Unlike comfort scenes, manual all-off is intentionally allowed in every
        house/quiet mode. Restrict writes to already-approved source entities
        and leave the existing Red Queen semantic light workflow untouched.
        An accepted HA service call is not a physical completion guarantee.
        """
        outcomes: list[dict[str, str]] = []
        for entity_id in tuple(self.rgbw_targets):
            state = self.hass.states.get(entity_id)
            if state is None or state.state in {"unknown", "unavailable"}:
                outcomes.append({"entity_id": entity_id, "status": "unavailable"})
                continue
            if state.state == "off":
                outcomes.append({"entity_id": entity_id, "status": "already_off"})
                continue
            if state.state != "on":
                outcomes.append({"entity_id": entity_id, "status": "skipped_unknown_state"})
                continue
            try:
                await self.async_light_dispatch(entity_id, "turn_off", {})
                outcomes.append({
                    "entity_id": entity_id,
                    "status": "accepted_dispatch_not_verified",
                })
            except Exception as err:
                _LOGGER.warning(
                    "Smart Living all-off: %s failed for %s",
                    type(err).__name__, entity_id,
                )
                outcomes.append({
                    "entity_id": entity_id,
                    "status": "failed",
                    "reason": type(err).__name__,
                })
                # Continue with the other lights; do not leave them all on
                # because one particular native DALI source is unavailable.
        failed = sum(
            entry["status"] in {"failed", "unavailable", "skipped_unknown_state"}
            for entry in outcomes
        )
        return {
            "target_count": len(outcomes),
            "dispatched_count": sum(
                item["status"] == "accepted_dispatch_not_verified"
                for item in outcomes
            ),
            "failed_count": failed,
            "status": "partial" if failed else "dispatched",
            "results": outcomes,
            "physically_verified": False,
        }

    async def async_activate_scene(
        self, scene_id: str,
    ) -> dict[str, Any]:
        """Preflight every light before issuing sequential writes.

        Batch scenes are always comfort automations regardless of which
        Home Assistant caller presses a button. Neither button.press nor a
        service caller may bypass away/vacation/quiet-time policy. Individual
        resident light control remains independent and available in HA.
        Sequential service calls are not atomic.
        """
        scene = self.scenes.get(scene_id)
        if scene is None:
            raise HomeAssistantError("Unknown configured Smart Living scene")
        allowed, reason = permission(
            self.mode, quiet=self.quiet, category="lighting.automatic_scene",
        )
        if not allowed:
            raise HomeAssistantError(reason)

        plan: list[tuple[str, str, dict[str, Any]]] = []
        for entity_id, entry in scene["lights"].items():
            if entity_id not in self.scene_targets:
                raise HomeAssistantError("Scene source not allowlisted: " + entity_id)
            state = self.hass.states.get(entity_id)
            if state is None or state.state in {"unknown", "unavailable"}:
                raise HomeAssistantError("Scene source unavailable: " + entity_id)
            action = "turn_on" if entry["state"] == "on" else "turn_off"
            attrs = self.validate_scene_light_request(
                entity_id, action,
                entry["attributes"] if action == "turn_on" else {}, state,
            )
            plan.append((entity_id, action, attrs))
        results: list[dict[str, Any]] = []
        for entity_id, action, attrs in plan:
            # A batch may span multiple awaited HA service calls. Re-check
            # resident mode and quiet state before EACH further dispatch so
            # switching to away/quiet cannot start another light command.
            still_allowed, stop_reason = permission(
                self.mode, quiet=self.quiet,
                category="lighting.automatic_scene",
            )
            if not still_allowed:
                results.append({
                    "entity_id": entity_id, "status": "suppressed",
                    "reason": stop_reason,
                })
                return {
                    "scene_id": scene_id, "status": "partial",
                    "results": results, "physically_verified": False,
                }
            try:
                await self.async_light_dispatch(entity_id, action, attrs)
            except Exception as err:
                results.append({"entity_id": entity_id, "status": "failed",
                                "reason": type(err).__name__})
                # Do not hide partially applied scene or continue blindly.
                return {"scene_id": scene_id, "status": "partial",
                        "results": results, "physically_verified": False}
            results.append({"entity_id": entity_id, "status": "dispatched"})
        return {"scene_id": scene_id, "status": "dispatched",
                "results": results, "physically_verified": False}

    def audit_snapshot(self) -> dict[str, Any]:
        return {"entries": list(self.audit), "limit": self.audit.maxlen}
