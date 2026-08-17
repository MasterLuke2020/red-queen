"""Generic execution qualification evidence contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    """Persistent qualification evidence for one semantic action outcome."""

    evidence_id: str
    action_id: str
    provider_id: str
    evidence_type: str
    first_verified: str
    last_verified: str
    pass_count: int
    last_execution_id: str
    last_result_code: str
    hardware_verified: bool
    framework_verified: bool
    source: str = "framework_automatic"
    persisted_by_framework: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "action_id": self.action_id,
            "provider_id": self.provider_id,
            "evidence_type": self.evidence_type,
            "first_verified": self.first_verified,
            "last_verified": self.last_verified,
            "pass_count": self.pass_count,
            "last_execution_id": self.last_execution_id,
            "last_result_code": self.last_result_code,
            "hardware_verified": self.hardware_verified,
            "framework_verified": self.framework_verified,
            "source": self.source,
            "persisted_by_framework": self.persisted_by_framework,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionEvidence":
        return cls(
            evidence_id=str(data["evidence_id"]),
            action_id=str(data["action_id"]),
            provider_id=str(data["provider_id"]),
            evidence_type=str(data["evidence_type"]),
            first_verified=str(data["first_verified"]),
            last_verified=str(data["last_verified"]),
            pass_count=int(data.get("pass_count", 1)),
            last_execution_id=str(data["last_execution_id"]),
            last_result_code=str(data["last_result_code"]),
            hardware_verified=bool(data.get("hardware_verified", True)),
            framework_verified=bool(data.get("framework_verified", True)),
            source=str(data.get("source", "framework_automatic")),
            persisted_by_framework=bool(
                data.get("persisted_by_framework", True)
            ),
        )

    def merged(
        self,
        *,
        verified_at: datetime,
        execution_id: str,
        result_code: str,
    ) -> "ExecutionEvidence":
        """Return a new evidence record with one additional passing observation."""
        return ExecutionEvidence(
            evidence_id=self.evidence_id,
            action_id=self.action_id,
            provider_id=self.provider_id,
            evidence_type=self.evidence_type,
            first_verified=self.first_verified,
            last_verified=verified_at.isoformat(),
            pass_count=self.pass_count + 1,
            last_execution_id=execution_id,
            last_result_code=result_code,
            hardware_verified=self.hardware_verified,
            framework_verified=self.framework_verified,
            source=self.source,
            persisted_by_framework=True,
        )
