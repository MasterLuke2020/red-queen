"""Home Assistant Device Registry helpers for WNHF."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN, PRODUCT_NAME, VERSION
from .engine import WNHFEngine


def framework_device_info() -> DeviceInfo:
    """Return the central WNHF framework device descriptor."""
    return DeviceInfo(
        identifiers={(DOMAIN, "framework")},
        name=PRODUCT_NAME,
        manufacturer="Weidner Net",
        model="Red Queen Framework",
        sw_version=VERSION,
        entry_type=DeviceEntryType.SERVICE,
    )


def module_device_info(module_id: str, name: str) -> DeviceInfo:
    """Return a logical WNHF module device descriptor."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"module:{module_id}")},
        name=name,
        manufacturer="Weidner Net",
        model="Red Queen Module",
        sw_version=VERSION,
    )


def room_device_info(engine: WNHFEngine, room_id: str) -> DeviceInfo:
    """Return the logical WNHF device descriptor for one room."""
    room = engine._require_house().room(room_id)
    return DeviceInfo(
        identifiers={(DOMAIN, f"room:{room.object_id}")},
        name=room.name,
        manufacturer="Weidner Net",
        model="Red Queen Room",
        model_id=room.room_type,
        sw_version=VERSION,
        suggested_area=room.name,
    )
