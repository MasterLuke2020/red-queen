"""Small runtime localization helpers for dynamic Red Queen entity names."""

from __future__ import annotations

from homeassistant.core import HomeAssistant


def localized(hass: HomeAssistant, *, de: str, en: str) -> str:
    """Return a dynamic label in the configured Home Assistant backend language."""
    language = str(getattr(hass.config, "language", "en") or "en").lower()
    return de if language.startswith("de") else en
