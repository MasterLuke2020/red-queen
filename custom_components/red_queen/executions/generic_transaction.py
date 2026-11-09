"""Generic dry-run transaction state machine."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class GenericTransactionState(StrEnum):
    CREATED="created"
    VALIDATING="validating"
    READY="ready"
    RUNNING="running"
    WAITING_FEEDBACK="waiting_feedback"
    SUCCEEDED="succeeded"
    FAILED="failed"
    ABORTED="aborted"
    NO_ACTION="no_action"
    REJECTED="rejected"


@dataclass(frozen=True, slots=True)
class GenericTransactionTransition:
    sequence:int
    at:datetime
    from_state:str|None
    to_state:GenericTransactionState
    reason:str
    step_id:str|None=None

    def as_dict(self)->dict[str,Any]:
        return {
            "sequence":self.sequence,
            "at":self.at.isoformat(),
            "from_state":self.from_state,
            "to_state":self.to_state.value,
            "reason":self.reason,
            "step_id":self.step_id,
        }


@dataclass(frozen=True, slots=True)
class GenericTransactionResult:
    transaction_id:str
    generated_at:datetime
    finished_at:datetime
    duration_ms:float
    decision_id:str
    plan_id:str
    confirmed:bool
    accepted:bool
    state:GenericTransactionState
    dry_run:bool
    executed:bool
    eligible_for_commit:bool
    total_steps:int
    processed_steps:int
    progress_percent:float
    reason:str
    transitions:tuple[GenericTransactionTransition,...]
    steps:tuple[dict[str,Any],...]
    blueprint:dict[str,Any]
    executor_version:str

    def as_dict(self)->dict[str,Any]:
        return {
            "transaction_id":self.transaction_id,
            "generated_at":self.generated_at.isoformat(),
            "finished_at":self.finished_at.isoformat(),
            "duration_ms":self.duration_ms,
            "decision_id":self.decision_id,
            "plan_id":self.plan_id,
            "confirmed":self.confirmed,
            "accepted":self.accepted,
            "state":self.state.value,
            "dry_run":self.dry_run,
            "executed":self.executed,
            "eligible_for_commit":self.eligible_for_commit,
            "summary":{
                "total_steps":self.total_steps,
                "processed_steps":self.processed_steps,
                "progress_percent":self.progress_percent,
            },
            "reason":self.reason,
            "transitions":[x.as_dict() for x in self.transitions],
            "steps":list(self.steps),
            "blueprint":self.blueprint,
            "versions":{"generic_executor":self.executor_version},
        }
