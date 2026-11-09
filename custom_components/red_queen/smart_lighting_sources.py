"""Vendor-independent Home Assistant light capability and source selection.

External light devices are controlled via HA's light service contract, never
Shelly/DALI/MQTT/Zigbee-specific paths. Pure testable helpers.
"""
from __future__ import annotations

import re
from typing import Any, Callable

_LIGHT_ID = re.compile(r"^light\.[a-z0-9_]+$")
COLOR_MODES = frozenset({
    "onoff", "brightness", "rgb", "rgbw", "rgbww",
    "hs", "xy", "color_temp",
})
BRIGHTNESS_MODES = COLOR_MODES - {"onoff"}
RGB_MODES = frozenset({"rgb", "rgbw", "rgbww", "hs", "xy"})
RGBW_MODES = frozenset({"rgbw", "rgbww"})
# Such sources may proxy to Red Queen or fan out to multiple physical lights.
PROXY_PLATFORMS = frozenset({"red_queen", "wnhf", "template", "group"})


def supported_modes(attributes: Any) -> set[str]:
    """Use supported_color_modes (not the current active color_mode)."""
    if not isinstance(attributes, dict):
        return set()
    raw = attributes.get("supported_color_modes")
    if not isinstance(raw, (list, tuple, set, frozenset)):
        return set()
    return {str(mode) for mode in raw if str(mode) in COLOR_MODES}


def scene_form_features(attributes: Any, *, semantic: bool = False) -> dict[str, bool]:
    modes = set() if semantic else supported_modes(attributes)
    return {
        "brightness": bool(modes & BRIGHTNESS_MODES),
        "rgb": bool(modes & RGB_MODES),
        "rgbw": bool(modes & RGBW_MODES),
    }


def eligible_ha_light_sources(
    entries: Any,
    state_get: Callable[[str], Any],
    *,
    integration_domain: str,
    integration_entry_id: str | None = None,
) -> dict[str, str]:
    """Build GUI candidates, not an automatic dispatch/whole-house-off list.

    Any directly registered, enabled, available light from any manufacturer
    may be selected. Explicit scene selection is necessary for authorization.
    """
    result: dict[str, str] = {}
    forbidden = PROXY_PLATFORMS | {integration_domain}
    for entry in entries:
        entity_id = getattr(entry, "entity_id", None)
        platform = getattr(entry, "platform", None)
        if not isinstance(entity_id, str) or not _LIGHT_ID.fullmatch(entity_id):
            continue
        if not isinstance(platform, str) or platform in forbidden:
            continue
        if getattr(entry, "disabled_by", None) is not None:
            continue
        if integration_entry_id is not None and (
            getattr(entry, "config_entry_id", None) == integration_entry_id
        ):
            continue
        state = state_get(entity_id)
        if state is None or getattr(state, "state", None) not in {"on", "off"}:
            continue
        attrs = getattr(state, "attributes", None)
        if not supported_modes(attrs):
            continue
        name = attrs.get("friendly_name")
        result[entity_id] = (
            name.strip() if isinstance(name, str) and name.strip()
            else entity_id
        )
    return dict(sorted(result.items()))
