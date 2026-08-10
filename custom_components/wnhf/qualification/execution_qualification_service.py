"""Read-only execution qualification reporting service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .execution_evidence_store import ExecutionEvidenceStore
from .execution_qualification_collector import (
    ExecutionQualificationCollector,
)


class ExecutionQualificationService:
    """Expose current generic execution qualification state."""

    API_VERSION = "1.0"
    VERSION = "1.1-stage4.7.5B.1"

    def __init__(
        self,
        store: ExecutionEvidenceStore,
        collector: ExecutionQualificationCollector,
    ) -> None:
        self._store = store
        self._collector = collector

    def snapshot(self) -> dict[str, Any]:
        evidence = self._store.values()

        by_action: dict[str, dict[str, Any]] = {}
        for item in evidence:
            entry = by_action.setdefault(
                item.action_id,
                {
                    "action_id": item.action_id,
                    "providers": set(),
                    "real_success": 0,
                    "idempotency": 0,
                    "evidence_count": 0,
                    "pass_count": 0,
                    "hardware_verified": False,
                    "framework_verified": False,
                    "first_verified": None,
                    "last_verified": None,
                },
            )

            entry["providers"].add(item.provider_id)
            entry[item.evidence_type] = (
                entry.get(item.evidence_type, 0)
                + item.pass_count
            )
            entry["evidence_count"] += 1
            entry["pass_count"] += item.pass_count
            entry["hardware_verified"] = (
                entry["hardware_verified"] or item.hardware_verified
            )
            entry["framework_verified"] = (
                entry["framework_verified"] or item.framework_verified
            )

            if (
                entry["first_verified"] is None
                or item.first_verified < entry["first_verified"]
            ):
                entry["first_verified"] = item.first_verified

            if (
                entry["last_verified"] is None
                or item.last_verified > entry["last_verified"]
            ):
                entry["last_verified"] = item.last_verified

        actions: list[dict[str, Any]] = []
        for action_id in sorted(by_action):
            item = by_action[action_id]
            item["providers"] = sorted(item["providers"])
            actions.append(item)

        return {
            "api_version": self.API_VERSION,
            "qualification_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "automatic_collection_enabled": True,
            "persistence_enabled": True,
            "collector": {
                "version": self._collector.VERSION,
                "qualifying_result_codes": sorted(
                    self._collector.QUALIFYING_CODES
                ),
            },
            "summary": {
                "actions": len(actions),
                "evidence": len(evidence),
                "pass_count": sum(
                    item.pass_count for item in evidence
                ),
                "hardware_verified_actions": sum(
                    int(bool(item["hardware_verified"]))
                    for item in actions
                ),
                "framework_verified_actions": sum(
                    int(bool(item["framework_verified"]))
                    for item in actions
                ),
            },
            "actions": actions,
            "store": self._store.snapshot(),
        }
