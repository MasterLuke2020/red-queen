"""Persistent watering history for semantic Plant Care."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant

from .helpers.async_file import AsyncFileHelper


@dataclass(frozen=True, slots=True)
class WateringEvent:
    event_id: str
    plant_id: str
    recorded_at: datetime
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "plant_id": self.plant_id,
            "recorded_at": self.recorded_at.astimezone(UTC).isoformat(),
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WateringEvent":
        recorded_at = datetime.fromisoformat(str(payload["recorded_at"]))
        if recorded_at.tzinfo is None:
            raise ValueError("Watering event recorded_at must be timezone-aware")
        return cls(
            event_id=str(payload["event_id"]),
            plant_id=str(payload["plant_id"]),
            recorded_at=recorded_at.astimezone(UTC),
            source=str(payload.get("source") or "manual"),
        )


class PlantWateringHistoryStore:
    """Schema-versioned, atomic event history owned by Red Queen."""

    STORE_VERSION = "1.0-stage4.7.15.0"
    SCHEMA_VERSION = "1.0"

    def __init__(self, path: Path) -> None:
        self.path = path
        self._events: list[WateringEvent] = []
        self.loaded = False
        self.load_error: str | None = None
        self.write_error: str | None = None
        self.last_write_at: str | None = None

    async def async_load(self, hass: HomeAssistant) -> None:
        await AsyncFileHelper(hass).run(self.load)

    def load(self) -> None:
        self._events.clear()
        self.load_error = None
        if not self.path.exists():
            self.loaded = True
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != self.SCHEMA_VERSION:
                raise ValueError(
                    "Unsupported plant watering history schema_version: "
                    f"{payload.get('schema_version')!r}"
                )
            events = payload.get("events", [])
            if not isinstance(events, list):
                raise ValueError("Plant watering history events must be a list")
            self._events.extend(WateringEvent.from_dict(item) for item in events)
            self._events.sort(key=lambda item: item.recorded_at)
            self.last_write_at = payload.get("last_write_at")
            self.loaded = True
        except Exception as err:  # noqa: BLE001
            self.loaded = False
            self.load_error = f"{type(err).__name__}: {err}"

    def events_for(self, plant_id: str) -> tuple[WateringEvent, ...]:
        return tuple(item for item in self._events if item.plant_id == plant_id)

    def last_for(self, plant_id: str) -> WateringEvent | None:
        events = self.events_for(plant_id)
        return events[-1] if events else None

    def append(self, plant_id: str, recorded_at: datetime) -> WateringEvent:
        event = WateringEvent(
            event_id=f"watering_{uuid4().hex}",
            plant_id=plant_id,
            recorded_at=recorded_at.astimezone(UTC),
            source="manual",
        )
        self._events.append(event)
        self._events.sort(key=lambda item: item.recorded_at)
        return event

    def persist(self, *, last_write_at: str) -> None:
        self.write_error = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "store_version": self.STORE_VERSION,
            "schema_version": self.SCHEMA_VERSION,
            "persistent": True,
            "last_write_at": last_write_at,
            "count": len(self._events),
            "events": [item.as_dict() for item in self._events],
        }
        temp_path: Path | None = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=self.path.name + ".",
                suffix=".tmp",
                delete=False,
            ) as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = Path(handle.name)
            os.replace(temp_path, self.path)
            self.last_write_at = last_write_at
        except Exception as err:  # noqa: BLE001
            self.write_error = f"{type(err).__name__}: {err}"
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    def snapshot(self) -> dict[str, Any]:
        return {
            "store_version": self.STORE_VERSION,
            "schema_version": self.SCHEMA_VERSION,
            "persistent": True,
            "path": str(self.path),
            "loaded": self.loaded,
            "load_error": self.load_error,
            "write_error": self.write_error,
            "last_write_at": self.last_write_at,
            "count": len(self._events),
        }
