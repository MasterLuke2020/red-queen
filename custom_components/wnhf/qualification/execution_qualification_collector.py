"""Qualification classifier for generic real execution results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .execution_evidence import ExecutionEvidence


@dataclass(frozen=True, slots=True)
class ExecutionQualificationDecision:
    """Collector classification result."""

    qualified: bool
    evidence: ExecutionEvidence | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "qualified": self.qualified,
            "evidence": (
                self.evidence.as_dict()
                if self.evidence is not None
                else None
            ),
            "reason": self.reason,
        }


class ExecutionQualificationCollector:
    """Classify and merge generic real execution qualification evidence."""

    VERSION = "1.1-stage4.7.5B.1"

    QUALIFYING_CODES = {
        "EXE-000": "real_success",
        "EXE-101": "idempotency",
    }

    def classify(
        self,
        result: dict[str, Any],
    ) -> ExecutionQualificationDecision:
        """Create evidence only for hardware-significant successful outcomes."""
        result_code = str(
            (result.get("result_code") or {}).get("code", "")
        )

        evidence_type = self.QUALIFYING_CODES.get(result_code)
        if evidence_type is None:
            return ExecutionQualificationDecision(
                qualified=False,
                evidence=None,
                reason=(
                    "Result code does not currently qualify as execution "
                    "evidence."
                ),
            )

        if not bool(result.get("execution_enabled")):
            return ExecutionQualificationDecision(
                qualified=False,
                evidence=None,
                reason="Execution was not real/enabled.",
            )

        action_id = str(
            (result.get("request") or {}).get("action_id", "")
        )
        provider_id = str(result.get("provider_id") or "")
        execution_id = str(result.get("execution_id") or "")

        if not action_id or not provider_id or not execution_id:
            return ExecutionQualificationDecision(
                qualified=False,
                evidence=None,
                reason=(
                    "Execution result lacks action_id, provider_id or "
                    "execution_id."
                ),
            )

        if result_code == "EXE-000":
            if not bool(result.get("command_sent")):
                return ExecutionQualificationDecision(
                    qualified=False,
                    evidence=None,
                    reason="EXE-000 did not report command_sent=true.",
                )
            if not bool(result.get("feedback_confirmed")):
                return ExecutionQualificationDecision(
                    qualified=False,
                    evidence=None,
                    reason=(
                        "EXE-000 did not report the provider-defined confirmation."
                    ),
                )

        if result_code == "EXE-101":
            if bool(result.get("command_sent")):
                return ExecutionQualificationDecision(
                    qualified=False,
                    evidence=None,
                    reason="EXE-101 unexpectedly sent a command.",
                )
            if not bool(result.get("feedback_confirmed")):
                return ExecutionQualificationDecision(
                    qualified=False,
                    evidence=None,
                    reason="EXE-101 lacks confirmed satisfied feedback.",
                )

        provider_result = result.get("provider_result") or {}
        verification_scope = str(
            provider_result.get("verification_scope") or "effect"
        )
        hardware_verified = verification_scope != "dispatch"

        verified_at = datetime.now(UTC)
        evidence_id = f"auto.execution.{action_id}.{evidence_type}"

        evidence = ExecutionEvidence(
            evidence_id=evidence_id,
            action_id=action_id,
            provider_id=provider_id,
            evidence_type=evidence_type,
            first_verified=verified_at.isoformat(),
            last_verified=verified_at.isoformat(),
            pass_count=1,
            last_execution_id=execution_id,
            last_result_code=result_code,
            hardware_verified=hardware_verified,
            framework_verified=True,
            source="framework_automatic",
            persisted_by_framework=True,
        )

        return ExecutionQualificationDecision(
            qualified=True,
            evidence=evidence,
            reason=(
                "Execution result qualifies as framework-verified "
                f"{evidence_type} evidence "
                f"(verification_scope={verification_scope})."
            ),
        )

    def merge_with_existing(
        self,
        *,
        decision: ExecutionQualificationDecision,
        existing: ExecutionEvidence | None,
    ) -> ExecutionEvidence | None:
        """Merge one qualifying observation into existing evidence."""
        if not decision.qualified or decision.evidence is None:
            return None

        current = decision.evidence
        if existing is None:
            return current

        # Guard against accidental evidence-ID collisions across actions/providers.
        if existing.action_id != current.action_id:
            raise ValueError(
                "Execution evidence action_id mismatch for identical evidence_id."
            )
        if existing.provider_id != current.provider_id:
            raise ValueError(
                "Execution evidence provider_id mismatch for identical evidence_id."
            )
        if existing.evidence_type != current.evidence_type:
            raise ValueError(
                "Execution evidence type mismatch for identical evidence_id."
            )

        return existing.merged(
            verified_at=datetime.fromisoformat(current.last_verified),
            execution_id=current.last_execution_id,
            result_code=current.last_result_code,
        )
