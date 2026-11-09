"""Native Home Assistant options-flow editor for Red Queen Smart Lighting.

Scene and rule CRUD uses strongly validated forms. No physical commands from
the configurator. Every successful save triggers the existing options-flow
integration reload, re-creating HA sun/time/state subscriptions without a
Home Assistant process restart.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import voluptuous as vol

from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import DOMAIN
from .smart_living_runtime import DATA_SMART_LIVING
from .smart_living_editor import validate_editor_document


def _select(options: list[dict[str, str]], *, multiple: bool = False):
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=options, multiple=multiple,
        mode=selector.SelectSelectorMode.DROPDOWN,
    ))


def _fixed_options(values: list[str]):
    return _select([{"value": value, "label": value} for value in values])


def _entity_options(targets: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"value": entity_id, "label": f"{name} ({entity_id})"}
        for entity_id, name in sorted(targets.items())
    ]


def _scene_options(scenes: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"value": scene["id"], "label": f"{scene['name']} ({scene['id']})"}
        for scene in scenes
    ]


def _rule_options(rules: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"value": rule["id"], "label": f"{rule['name']} ({rule['id']})"}
        for rule in rules
    ]


def _scene_light_settings(
    data: dict[str, Any], *, semantic: bool = False,
) -> dict[str, Any]:
    if data["state"] == "off":
        return {"state": "off"}
    if semantic:
        # The canonical PLC light adapter supports only ON and OFF.
        # Ignore graphical RGB/brightness fields, never pass them to PLC.
        return {"state": "on"}
    settings = {"state": "on", "brightness": int(data["brightness"])}
    mode = data["color_mode"]
    if mode == "rgbw":
        settings["rgbw_color"] = [
            int(data["red"]), int(data["green"]),
            int(data["blue"]), int(data["white"]),
        ]
    elif mode == "rgb":
        settings["rgb_color"] = [
            int(data["red"]), int(data["green"]), int(data["blue"]),
        ]
    return settings


def _trigger_from_editor(pending: dict[str, Any],
                         inputs: dict[str, Any]) -> dict[str, Any]:
    kind = pending["trigger_kind"]
    if kind == "time":
        # HA TimeSelector may return HH:MM:SS; the schedule contract is HH:MM.
        selected = inputs["at"]
        if len(selected) == 8 and selected.endswith(":00"):
            selected = selected[:5]
        return {"type": "time", "at": selected}
    if kind in {"sunrise", "sunset"}:
        return {"type": "sun", "event": kind,
                "offset_minutes": inputs["offset_minutes"]}
    return {"type": "state",
            "entity_id": inputs["entity_id"], "to": inputs["to"]}


class SmartLightingOptionsMixin:
    """Injected into the existing WNHFOptionsFlow, no second options flow."""

    def _sl_runtime(self):
        return self.hass.data[DOMAIN][DATA_SMART_LIVING]

    def _sl_document(self) -> dict[str, Any]:
        return deepcopy(self._sl_runtime().editor_document())

    async def _sl_commit(self, document: dict[str, Any]):
        runtime = self._sl_runtime()
        await runtime.editor.async_save(
            document["scenes"], document["automations"],
            set(runtime.scene_targets),
        )
        # Reuse OptionsFlowWithReload: this closes the dialogue and triggers
        # a managed integration reload, not a Home Assistant restart.
        return self._finish("smart_lighting_saved")

    async def async_step_smart_lighting(self, user_input=None):
        return self.async_show_menu(
            step_id="smart_lighting",
            menu_options=["smart_scenes", "smart_rules"],
        )

    async def async_step_smart_scenes(self, user_input=None):
        doc = self._sl_document()
        menu = ["smart_scene_add"]
        if doc["scenes"]:
            menu.append("smart_scene_pick")
        return self.async_show_menu(
            step_id="smart_scenes", menu_options=menu,
            description_placeholders={"count": str(len(doc["scenes"]))},
        )

    def _scene_form(self, *, step_id: str, existing: dict | None = None,
                    errors: dict | None = None):
        sources = self._sl_runtime().scene_targets
        if not sources:
            return self.async_abort(reason="smart_lighting_no_sources")
        if existing is None:
            default_light = next(iter(sources))
            defaults = {"state": "on", "brightness": 200,
                        "color_mode": "brightness",
                        "red": 0, "green": 0, "blue": 0, "white": 255}
        else:
            default_light = existing["entity_id"]
            attributes = existing["settings"]
            mode = "rgbw" if "rgbw_color" in attributes else (
                "rgb" if "rgb_color" in attributes else "brightness"
            )
            channels = list(attributes.get("rgbw_color") or (
                list(attributes.get("rgb_color") or [0, 0, 0]) + [0]
            ))
            defaults = {
                "state": attributes.get("state", "on"),
                "brightness": attributes.get("brightness", 200),
                "color_mode": mode,
                "red": channels[0], "green": channels[1],
                "blue": channels[2], "white": channels[3],
            }
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema({
                vol.Required("entity_id", default=default_light):
                    _select(
                        _entity_options(sources) if existing is None else
                        _entity_options({default_light: sources[default_light]})
                    ),
                vol.Required("state", default=defaults["state"]):
                    _fixed_options(["on", "off"]),
                vol.Required("brightness", default=defaults["brightness"]):
                    vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
                vol.Required("color_mode", default=defaults["color_mode"]):
                    _fixed_options(["brightness", "rgb", "rgbw"]),
                vol.Required("red", default=defaults["red"]):
                    vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
                vol.Required("green", default=defaults["green"]):
                    vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
                vol.Required("blue", default=defaults["blue"]):
                    vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
                vol.Required("white", default=defaults["white"]):
                    vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
            }), errors=errors or {},
        )

    async def async_step_smart_scene_add(self, user_input=None):
        errors = {}
        if user_input is not None:
            name = user_input["name"].strip()
            key = slugify(user_input.get("id", "").strip() or name)
            doc = self._sl_document()
            if not name or len(name) > 80:
                errors["name"] = "smart_lighting_invalid_name"
            elif not key or key in {x["id"] for x in doc["scenes"]}:
                errors["id"] = "smart_lighting_duplicate_id"
            else:
                self._sl_scene_new = {"id": key, "name": name}
                return await self.async_step_smart_scene_first_light()
        return self.async_show_form(
            step_id="smart_scene_add",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Optional("id", default=""): str,
            }), errors=errors,
        )

    async def async_step_smart_scene_first_light(self, user_input=None):
        if not hasattr(self, "_sl_scene_new"):
            return self.async_abort(reason="smart_lighting_state_lost")
        if user_input is not None:
            doc = self._sl_document()
            doc["scenes"].append({
                **self._sl_scene_new,
                "lights": {
                    user_input["entity_id"]: _scene_light_settings(
                        user_input, semantic=(
                            user_input["entity_id"] in self._sl_runtime().semantic_targets
                        ),
                    )
                },
            })
            try:
                return await self._sl_commit(doc)
            except (ValueError, OSError):
                return self._scene_form(
                    step_id="smart_scene_first_light",
                    errors={"base": "smart_lighting_save_failed"},
                )
        return self._scene_form(step_id="smart_scene_first_light")

    async def async_step_smart_scene_pick(self, user_input=None):
        doc = self._sl_document()
        if not doc["scenes"]:
            return self.async_abort(reason="smart_lighting_no_scenes")
        if user_input is not None:
            self._sl_scene_id = user_input["scene_id"]
            return await self.async_step_smart_scene_actions()
        return self.async_show_form(
            step_id="smart_scene_pick",
            data_schema=vol.Schema({
                vol.Required("scene_id"):
                    _select(_scene_options(doc["scenes"])),
            }),
        )

    def _sl_scene(self, document: dict[str, Any]):
        target = getattr(self, "_sl_scene_id", None)
        return next((s for s in document["scenes"] if s["id"] == target), None)

    async def async_step_smart_scene_actions(self, user_input=None):
        doc = self._sl_document()
        scene = self._sl_scene(doc)
        if scene is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        return self.async_show_menu(
            step_id="smart_scene_actions",
            menu_options=[
                "smart_scene_rename", "smart_scene_target",
                "smart_scene_target_pick", "smart_scene_target_remove",
                "smart_scene_delete",
            ],
            description_placeholders={
                "name": scene["name"],
                "target_count": str(len(scene["lights"])),
            },
        )

    async def async_step_smart_scene_rename(self, user_input=None):
        doc = self._sl_document()
        scene = self._sl_scene(doc)
        if scene is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        errors = {}
        if user_input is not None:
            name = user_input["name"].strip()
            if not name or len(name) > 80:
                errors["name"] = "smart_lighting_invalid_name"
            else:
                scene["name"] = name
                try:
                    return await self._sl_commit(doc)
                except (ValueError, OSError):
                    errors["base"] = "smart_lighting_save_failed"
        return self.async_show_form(
            step_id="smart_scene_rename",
            data_schema=vol.Schema({
                vol.Required("name", default=scene["name"]): str,
            }), errors=errors,
        )

    async def async_step_smart_scene_target(self, user_input=None):
        doc = self._sl_document()
        scene = self._sl_scene(doc)
        if scene is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        if user_input is not None and user_input["entity_id"] in scene["lights"]:
            return self._scene_form(
                step_id="smart_scene_target",
                errors={"entity_id": "smart_lighting_target_exists"},
            )
        if user_input is not None:
            scene["lights"][user_input["entity_id"]] = (
                _scene_light_settings(
                    user_input, semantic=(
                        user_input["entity_id"] in self._sl_runtime().semantic_targets
                    ),
                )
            )
            try:
                return await self._sl_commit(doc)
            except (ValueError, OSError):
                return self._scene_form(
                    step_id="smart_scene_target",
                    errors={"base": "smart_lighting_save_failed"},
                )
        return self._scene_form(step_id="smart_scene_target")

    async def async_step_smart_scene_target_pick(self, user_input=None):
        doc = self._sl_document()
        scene = self._sl_scene(doc)
        if scene is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        if user_input is not None:
            self._sl_target_id = user_input["entity_id"]
            return await self.async_step_smart_scene_target_edit()
        return self.async_show_form(
            step_id="smart_scene_target_pick",
            data_schema=vol.Schema({
                vol.Required("entity_id"):
                    _fixed_options(list(scene["lights"])),
            }),
        )

    async def async_step_smart_scene_target_edit(self, user_input=None):
        doc = self._sl_document()
        scene = self._sl_scene(doc)
        entity_id = getattr(self, "_sl_target_id", None)
        if scene is None or entity_id not in scene["lights"]:
            return self.async_abort(reason="smart_lighting_state_lost")
        existing = {
            "entity_id": entity_id, "settings": scene["lights"][entity_id],
        }
        errors = {}
        if user_input is not None:
            if user_input["entity_id"] != entity_id:
                errors["entity_id"] = "smart_lighting_target_missing"
            else:
                scene["lights"][entity_id] = _scene_light_settings(
                    user_input,
                    semantic=entity_id in self._sl_runtime().semantic_targets,
                )
                try:
                    return await self._sl_commit(doc)
                except (ValueError, OSError):
                    errors["base"] = "smart_lighting_save_failed"
        return self._scene_form(
            step_id="smart_scene_target_edit",
            existing=existing,
            errors=errors,
        )

    async def async_step_smart_scene_target_remove(self, user_input=None):
        doc = self._sl_document()
        scene = self._sl_scene(doc)
        if scene is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        if len(scene["lights"]) <= 1:
            return self.async_abort(reason="smart_lighting_last_target")
        errors = {}
        if user_input is not None:
            if not user_input["confirm"]:
                errors["confirm"] = "smart_lighting_confirm_required"
            elif user_input["entity_id"] not in scene["lights"]:
                errors["entity_id"] = "smart_lighting_target_missing"
            else:
                del scene["lights"][user_input["entity_id"]]
                try:
                    return await self._sl_commit(doc)
                except (ValueError, OSError):
                    errors["base"] = "smart_lighting_save_failed"
        return self.async_show_form(
            step_id="smart_scene_target_remove",
            data_schema=vol.Schema({
                vol.Required("entity_id"):
                    _fixed_options(list(scene["lights"])),
                vol.Required("confirm", default=False): bool,
            }), errors=errors,
        )

    async def async_step_smart_scene_delete(self, user_input=None):
        doc = self._sl_document()
        scene = self._sl_scene(doc)
        if scene is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        if any(r["scene_id"] == scene["id"] for r in doc["automations"]):
            return self.async_abort(reason="smart_lighting_scene_in_use")
        errors = {}
        if user_input is not None:
            if user_input["confirm"]:
                doc["scenes"] = [
                    s for s in doc["scenes"] if s["id"] != scene["id"]
                ]
                try:
                    return await self._sl_commit(doc)
                except (ValueError, OSError):
                    errors["base"] = "smart_lighting_save_failed"
            else:
                errors["confirm"] = "smart_lighting_confirm_required"
        return self.async_show_form(
            step_id="smart_scene_delete",
            data_schema=vol.Schema({
                vol.Required("confirm", default=False): bool,
            }), errors=errors,
            description_placeholders={"name": scene["name"]},
        )

    async def async_step_smart_rules(self, user_input=None):
        doc = self._sl_document()
        menu = ["smart_rule_add"]
        if doc["automations"]:
            menu.append("smart_rule_pick")
        return self.async_show_menu(
            step_id="smart_rules", menu_options=menu,
            description_placeholders={
                "count": str(len(doc["automations"])),
            },
        )

    def _rule_base_form(self, step: str, old: dict | None,
                        errors: dict | None = None):
        doc = self._sl_document()
        if not doc["scenes"]:
            return self.async_abort(reason="smart_lighting_no_scenes")
        old = old or {}
        trigger = old.get("trigger", {})
        trigger_kind = (
            trigger.get("event") if trigger.get("type") == "sun"
            else trigger.get("type", "time")
        )
        return self.async_show_form(
            step_id=step,
            data_schema=vol.Schema({
                vol.Required("name", default=old.get("name", "")): str,
                vol.Required(
                    "scene_id",
                    default=old.get("scene_id", doc["scenes"][0]["id"]),
                ): _select(_scene_options(doc["scenes"])),
                vol.Required("action", default=old.get("action", "on")):
                    _fixed_options(["on", "off"]),
                vol.Required("trigger_kind", default=trigger_kind):
                    _fixed_options(["sunset", "sunrise", "time", "state"]),
                vol.Required(
                    "allowed_modes",
                    default=list(old.get("allowed_modes", ["home"])),
                ): _select([
                    {"value": "home", "label": "Home"},
                    {"value": "away", "label": "Away"},
                    {"value": "vacation", "label": "Vacation"},
                ], multiple=True),
                vol.Required("allow_quiet", default=old.get("allow_quiet", False)): bool,
                vol.Required("enabled", default=old.get("enabled", False)): bool,
            }), errors=errors or {},
        )

    async def async_step_smart_rule_add(self, user_input=None):
        errors = {}
        if user_input is not None:
            doc = self._sl_document()
            key = slugify(user_input["name"])
            if not user_input["name"].strip() or len(user_input["name"]) > 80:
                errors["name"] = "smart_lighting_invalid_name"
            elif not key or key in {r["id"] for r in doc["automations"]}:
                errors["name"] = "smart_lighting_duplicate_id"
            elif not user_input["allowed_modes"]:
                errors["allowed_modes"] = "smart_lighting_invalid_mode"
            else:
                self._sl_pending_rule = {
                    **user_input, "id": key,
                }
                return await self.async_step_smart_rule_trigger()
        return self._rule_base_form("smart_rule_add", None, errors)

    async def async_step_smart_rule_pick(self, user_input=None):
        doc = self._sl_document()
        if not doc["automations"]:
            return self.async_abort(reason="smart_lighting_no_rules")
        if user_input is not None:
            self._sl_rule_id = user_input["rule_id"]
            return await self.async_step_smart_rule_actions()
        return self.async_show_form(
            step_id="smart_rule_pick",
            data_schema=vol.Schema({
                vol.Required("rule_id"): _select(_rule_options(doc["automations"])),
            }),
        )

    def _sl_rule(self, document: dict[str, Any]):
        key = getattr(self, "_sl_rule_id", None)
        return next((x for x in document["automations"] if x["id"] == key), None)

    async def async_step_smart_rule_actions(self, user_input=None):
        doc = self._sl_document()
        rule = self._sl_rule(doc)
        if rule is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        return self.async_show_menu(
            step_id="smart_rule_actions",
            menu_options=["smart_rule_edit", "smart_rule_toggle", "smart_rule_delete"],
            description_placeholders={
                "name": rule["name"],
                "status": "ON" if rule["enabled"] else "OFF",
            },
        )

    async def async_step_smart_rule_edit(self, user_input=None):
        doc = self._sl_document()
        rule = self._sl_rule(doc)
        if rule is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        errors = {}
        if user_input is not None:
            if not user_input["name"].strip() or len(user_input["name"]) > 80:
                errors["name"] = "smart_lighting_invalid_name"
            elif not user_input["allowed_modes"]:
                errors["allowed_modes"] = "smart_lighting_invalid_mode"
            else:
                self._sl_pending_rule = {**user_input, "id": rule["id"]}
                return await self.async_step_smart_rule_trigger()
        return self._rule_base_form("smart_rule_edit", rule, errors)

    async def async_step_smart_rule_trigger(self, user_input=None):
        pending = getattr(self, "_sl_pending_rule", None)
        if pending is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        kind = pending["trigger_kind"]
        old = self._sl_rule(self._sl_document())
        previous = old["trigger"] if old is not None else {}
        errors = {}
        if user_input is not None:
            trigger = _trigger_from_editor(pending, user_input)
            candidate = {
                key: pending[key] for key in (
                    "id", "name", "scene_id", "action",
                    "enabled", "allowed_modes", "allow_quiet",
                )
            }
            candidate["trigger"] = trigger
            doc = self._sl_document()
            doc["automations"] = [
                rule for rule in doc["automations"] if rule["id"] != candidate["id"]
            ] + [candidate]
            try:
                return await self._sl_commit(doc)
            except (ValueError, OSError):
                errors["base"] = "smart_lighting_save_failed"
        if kind == "time":
            schema = vol.Schema({
                vol.Required(
                    "at", default=previous.get("at", "23:00"),
                ): selector.TimeSelector(),
            })
        elif kind in {"sunrise", "sunset"}:
            schema = vol.Schema({
                vol.Required(
                    "offset_minutes", default=previous.get("offset_minutes", 0),
                ): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
            })
        else:
            schema = vol.Schema({
                vol.Required("entity_id", default=previous.get(
                    "entity_id", "",
                )): selector.EntitySelector(selector.EntitySelectorConfig(
                    domain=["binary_sensor", "input_boolean"],
                )),
                vol.Required("to", default=previous.get("to", "on")):
                    _fixed_options(["on", "off"]),
            })
        return self.async_show_form(
            step_id="smart_rule_trigger",
            data_schema=schema, errors=errors,
        )

    async def async_step_smart_rule_toggle(self, user_input=None):
        doc = self._sl_document()
        rule = self._sl_rule(doc)
        if rule is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        errors = {}
        if user_input is not None:
            if not user_input["confirm"]:
                errors["confirm"] = "smart_lighting_confirm_required"
            else:
                rule["enabled"] = not rule["enabled"]
                try:
                    return await self._sl_commit(doc)
                except (ValueError, OSError):
                    errors["base"] = "smart_lighting_save_failed"
        return self.async_show_form(
            step_id="smart_rule_toggle",
            data_schema=vol.Schema({
                vol.Required("confirm", default=False): bool,
            }), errors=errors,
            description_placeholders={
                "name": rule["name"],
                "next": "ON" if not rule["enabled"] else "OFF",
            },
        )

    async def async_step_smart_rule_delete(self, user_input=None):
        doc = self._sl_document()
        rule = self._sl_rule(doc)
        if rule is None:
            return self.async_abort(reason="smart_lighting_state_lost")
        errors = {}
        if user_input is not None:
            if not user_input["confirm"]:
                errors["confirm"] = "smart_lighting_confirm_required"
            else:
                doc["automations"] = [
                    x for x in doc["automations"] if x["id"] != rule["id"]
                ]
                try:
                    return await self._sl_commit(doc)
                except (ValueError, OSError):
                    errors["base"] = "smart_lighting_save_failed"
        return self.async_show_form(
            step_id="smart_rule_delete",
            data_schema=vol.Schema({
                vol.Required("confirm", default=False): bool,
            }), errors=errors,
            description_placeholders={"name": rule["name"]},
        )
