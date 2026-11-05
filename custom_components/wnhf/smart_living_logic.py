"""Pure, dependency-free Smart Living decisions and RGBW validation.

No Home Assistant imports: the policy/colour logic can be tested offline.
"""
from __future__ import annotations

from typing import Any

HOUSE_MODES = ("home", "away", "vacation")
SAFE_COLOR_MODES = frozenset(
    {"onoff", "brightness", "rgb", "rgbw", "rgbww", "hs", "xy", "color_temp"}
)
RGBW_INPUT_KEYS = frozenset({"brightness", "rgbw_color", "rgb_color", "transition"})


def resolve_mode(manual: str, away_signal: str | None, auto_away: bool) -> tuple[str, str]:
    """Never infer absence from a missing/unavailable/ambiguous input."""
    if manual not in HOUSE_MODES:
        raise ValueError("Unsupported manual house mode")
    if manual == "vacation":
        return ("vacation", "manual")
    if not auto_away:
        return (manual, "manual")
    if away_signal == "on":
        return ("away", "configured_away_sensor")
    if away_signal == "off":
        return ("home", "configured_away_sensor")
    return (manual, "manual_fallback_unknown_sensor")


def permission(
    mode: str, *, quiet: bool, category: str, urgency: str = "info",
    automated: bool = False,
) -> tuple[bool, str]:
    """Basic comfort policy; access/security actions are NEVER approved here.

    This policy controls only newly added Smart Living convenience actions.
    Existing canonical access guards always remain authoritative.
    """
    if mode not in HOUSE_MODES:
        return False, "Unknown house mode"
    if category == "lighting.manual":
        return True, "Resident manual lighting remains available"
    if category == "lighting.automatic_scene":
        if mode != "home" or quiet:
            return False, "Automatic scene blocked by house/quiet mode"
        return True, "Automatic comfort scene allowed"
    if category == "notifications.mobile":
        return True, "Mobile notification permitted"
    if category == "notifications.announce":
        if urgency not in {"info", "notice", "warning", "alarm"}:
            return False, "Unknown announcement urgency"
        if mode != "home":
            return False, "Voice announcement suppressed while not home"
        if quiet and urgency != "alarm":
            return False, "Noncritical voice announcement suppressed in quiet mode"
        if quiet and urgency == "alarm":
            return False, "Quiet-time alarm announcement requires separate opt-in"
        return True, "Voice announcement permitted"
    return False, "Unrecognized category; default deny for Smart Living"


def validate_light_request(
    source_modes: set[str], data: dict[str, Any],
) -> dict[str, Any]:
    """Validate native RGBW/brightness requests before delegated HA service."""
    if not data:
        return {}
    unexpected = set(data) - RGBW_INPUT_KEYS
    if unexpected:
        raise ValueError("Unsupported RGBW request parameter(s): " +
                         ", ".join(sorted(unexpected)))
    if not (source_modes & SAFE_COLOR_MODES):
        raise ValueError("Source light has no usable color mode")
    result: dict[str, Any] = {}
    if "brightness" in data:
        value = data["brightness"]
        if type(value) is not int or not 0 <= value <= 255:
            raise ValueError("brightness must be integer 0..255")
        if source_modes == {"onoff"}:
            raise ValueError("Source light does not support brightness")
        result["brightness"] = value
    for key, count, required_mode in (
        ("rgbw_color", 4, "rgbw"),
        ("rgb_color", 3, "rgb"),
    ):
        if key not in data:
            continue
        value = data[key]
        if not isinstance(value, (list, tuple)) or len(value) != count:
            raise ValueError(key + " must contain " + str(count) + " components")
        if any(type(v) is not int or v < 0 or v > 255 for v in value):
            raise ValueError(key + " components must be integers 0..255")
        if key == "rgbw_color" and not (source_modes & {"rgbw", "rgbww"}):
            raise ValueError("Source light does not support RGBW")
        if key == "rgb_color" and not (source_modes & {"rgb", "rgbw", "rgbww", "hs", "xy"}):
            raise ValueError("Source light does not support RGB")
        result[key] = tuple(value)
    if "rgb_color" in result and "rgbw_color" in result:
        raise ValueError("Specify only one color representation")
    if "transition" in data:
        seconds = data["transition"]
        if type(seconds) not in (int, float) or not 0 <= seconds <= 300:
            raise ValueError("transition must be 0..300 seconds")
        result["transition"] = float(seconds)
    return result


def exposed_modes(raw: Any) -> set[str]:
    """Preserve only HA color modes explicitly advertised by the source."""
    if not isinstance(raw, (list, tuple, set)):
        return set()
    return {str(mode) for mode in raw if str(mode) in SAFE_COLOR_MODES}
