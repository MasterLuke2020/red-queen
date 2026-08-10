"""Persistent atomic store for generic execution qualification evidence."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from homeassistant.core import HomeAssistant

from ..helpers.async_file import AsyncFileHelper

from .execution_evidence import ExecutionEvidence


class ExecutionEvidenceStore:
    """Schema-versioned persistent evidence store."""

    STORE_VERSION = "1.2-stage4.7.7.1"
    SCHEMA_VERSION = "1.0"

    def __init__(self, path: Path) -> None:
        self.path = path
        self._evidence: dict[str, ExecutionEvidence] = {}
        self.loaded = False
        self.load_error: str | None = None
        self.write_error: str | None = None
        self.last_write_at: str | None = None

    async def async_load(self, hass: HomeAssistant) -> None:
        """Restore evidence without blocking Home Assistant's event loop."""
        helper = AsyncFileHelper(hass)
        await helper.run(self.load)

    def load(self) -> None:
        """Restore evidence from disk when present."""
        self._evidence.clear()
        self.load_error = None

        if not self.path.exists():
            self.loaded = True
            return

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != self.SCHEMA_VERSION:
                raise ValueError(
                    "Unsupported execution evidence schema_version: "
                    f"{payload.get('schema_version')!r}"
                )

            for item in payload.get("evidence", []):
                evidence = ExecutionEvidence.from_dict(item)
                self._evidence[evidence.evidence_id] = evidence

            self.last_write_at = payload.get("last_write_at")
            self.loaded = True
        except Exception as err:  # noqa: BLE001
            self.loaded = False
            self.load_error = f"{type(err).__name__}: {err}"

    def get(self, evidence_id: str) -> ExecutionEvidence | None:
        return self._evidence.get(evidence_id)

    def values(self) -> tuple[ExecutionEvidence, ...]:
        return tuple(
            self._evidence[key]
            for key in sorted(self._evidence)
        )

    def upsert(self, evidence: ExecutionEvidence) -> None:
        self._evidence[evidence.evidence_id] = evidence

    def persist(self, *, last_write_at: str) -> None:
        """Atomically write the complete store to disk."""
        self.write_error = None
        self.path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "store_version": self.STORE_VERSION,
            "schema_version": self.SCHEMA_VERSION,
            "persistent": True,
            "last_write_at": last_write_at,
            "count": len(self._evidence),
            "pass_count": sum(
                item.pass_count
                for item in self._evidence.values()
            ),
            "evidence": [
                item.as_dict()
                for item in self.values()
            ],
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
                json.dump(
                    payload,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
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
            "count": len(self._evidence),
            "pass_count": sum(
                item.pass_count
                for item in self._evidence.values()
            ),
            "evidence": [
                item.as_dict()
                for item in self.values()
            ],
        }
