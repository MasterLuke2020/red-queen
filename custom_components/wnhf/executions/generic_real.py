"""First real generic semantic execution engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from time import perf_counter
from typing import Any
from uuid import uuid4

from .action_contracts import REAL_EXECUTION_ENABLED_ACTIONS
from .generic_contract import promote_execution_plan


class GenericRealExecutionState(StrEnum):
    SUCCEEDED = "succeeded"
    NO_ACTION = "no_action"
    REJECTED = "rejected"
    FAILED = "failed"


class GenericRealResultCode(StrEnum):
    SUCCEEDED = "EXE-000"
    ALREADY_SATISFIED = "EXE-101"
    ALREADY_IN_PROGRESS = "EXE-102"
    ACTION_NOT_IMPLEMENTED = "EXE-205"
    PLAN_REJECTED = "EXE-206"
    PROVIDER_NOT_FOUND = "EXE-207"
    PROVIDER_REJECTED = "EXE-208"
    COMMAND_FAILED = "EXE-300"
    EFFECT_NOT_CONFIRMED = "EXE-301"
    EXECUTOR_EXCEPTION = "EXE-900"


@dataclass(frozen=True, slots=True)
class GenericRealExecutionResult:
    api_version: str
    execution_contract: str
    execution_id: str
    generated_at: str
    finished_at: str
    duration_ms: float
    state: GenericRealExecutionState
    result_code: GenericRealResultCode
    accepted: bool
    executable: bool
    execution_enabled: bool
    executed: bool
    command_sent: bool
    feedback_confirmed: bool
    request: dict[str, Any]
    plan: dict[str, Any] | None
    provider_id: str | None
    provider_result: dict[str, Any] | None
    reason: str
    error: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "api_version": self.api_version,
            "execution_contract": self.execution_contract,
            "execution_id": self.execution_id,
            "generated_at": self.generated_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "state": self.state.value,
            "result_code": {
                "code": self.result_code.value,
                "key": self.result_code.name.lower(),
            },
            "accepted": self.accepted,
            "executable": self.executable,
            "execution_enabled": self.execution_enabled,
            "executed": self.executed,
            "command_sent": self.command_sent,
            "feedback_confirmed": self.feedback_confirmed,
            "request": self.request,
            "plan": self.plan,
            "provider_id": self.provider_id,
            "provider_result": self.provider_result,
            "reason": self.reason,
            "error": self.error,
        }


class GenericExecutionEngine:
    """Dispatch approved generic plans to the selected provider.

    Provider selection remains owned by the Capability Layer. This engine
    only looks up the provider ID already selected in the dry-run plan.
    """

    API_VERSION = "1.0"
    VERSION = "1.9-rc7"
    ENABLED_ACTIONS = REAL_EXECUTION_ENABLED_ACTIONS

    def __init__(
        self,
        planner: Any,
        semantic_router: Any,
    ) -> None:
        self._planner = planner
        self._semantic_router = semantic_router

    async def async_execute(
        self,
        *,
        action_id: str,
        target: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        confirmed: bool = False,
    ) -> GenericRealExecutionResult:
        started = perf_counter()
        generated_at = datetime.now(UTC)
        execution_id = (
            "exe_"
            + generated_at.strftime("%Y%m%dT%H%M%S_%fZ_")
            + uuid4().hex[:8]
        )

        try:
            dry_run = await self._planner.async_dry_run(
                action_id=action_id,
                target=target,
                parameters=parameters,
                confirmed=confirmed,
            )
            dry_payload = dry_run.as_dict()
            validation_request = dry_payload["request"]
            validation_plan = dry_payload["plan"]

            if not dry_payload["accepted"] or dry_run.plan is None:
                request = dict(validation_request)
                request["dry_run"] = False
                plan = validation_plan
                return self._finish(
                    started=started,
                    generated_at=generated_at,
                    execution_id=execution_id,
                    state=GenericRealExecutionState.REJECTED,
                    code=GenericRealResultCode.PLAN_REJECTED,
                    accepted=False,
                    executable=False,
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    request=request,
                    plan=plan,
                    provider_id=None,
                    provider_result=None,
                    reason=(
                        "Generic dry-run planning rejected the execution "
                        f"request: {dry_payload['reason']}"
                    ),
                    error=None,
                )

            # Promote the validated dry-run plan before any dispatch.
            promoted_plan_obj = promote_execution_plan(dry_run.plan)
            plan = promoted_plan_obj.as_dict()

            # The real execution keeps the same request identity while
            # accurately describing its execution mode.
            request = dict(validation_request)
            request["dry_run"] = False

            if action_id not in self.ENABLED_ACTIONS:
                return self._finish(
                    started=started,
                    generated_at=generated_at,
                    execution_id=execution_id,
                    state=GenericRealExecutionState.REJECTED,
                    code=GenericRealResultCode.ACTION_NOT_IMPLEMENTED,
                    accepted=False,
                    executable=False,
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    request=request,
                    plan=plan,
                    provider_id=None,
                    provider_result=None,
                    reason=(
                        "Canonical real execution is not enabled for this "
                        "semantic action."
                    ),
                    error=None,
                )

            route_result = await self._semantic_router.async_route(
                plan=plan,
            )
            provider_id = route_result.provider_id
            provider_result = route_result.provider_result

            if route_result.status == "rejected":
                return self._finish(
                    started=started,
                    generated_at=generated_at,
                    execution_id=execution_id,
                    state=GenericRealExecutionState.REJECTED,
                    code=GenericRealResultCode.PROVIDER_REJECTED,
                    accepted=False,
                    executable=False,
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    request=request,
                    plan=plan,
                    provider_id=provider_id,
                    provider_result=provider_result,
                    reason=route_result.reason,
                    error=route_result.error,
                )

            if route_result.status == "failed" and provider_result is None:
                return self._finish(
                    started=started,
                    generated_at=generated_at,
                    execution_id=execution_id,
                    state=GenericRealExecutionState.FAILED,
                    code=GenericRealResultCode.COMMAND_FAILED,
                    accepted=True,
                    executable=True,
                    executed=False,
                    command_sent=False,
                    feedback_confirmed=False,
                    request=request,
                    plan=plan,
                    provider_id=provider_id,
                    provider_result=None,
                    reason=route_result.reason,
                    error=route_result.error,
                )

            provider_status = str(provider_result["status"])
            provider_executed = bool(provider_result["executed"])
            provider_command_sent = bool(provider_result["command_sent"])
            provider_feedback_confirmed = bool(
                provider_result["feedback_confirmed"]
            )
            provider_reason = str(provider_result["reason"])
            provider_error = provider_result.get("error")

            if provider_status == "succeeded":
                state = GenericRealExecutionState.SUCCEEDED
                code = GenericRealResultCode.SUCCEEDED
                accepted = True
                executable = True
            elif provider_status == "no_action":
                state = GenericRealExecutionState.NO_ACTION
                code = GenericRealResultCode.ALREADY_SATISFIED
                accepted = True
                executable = True
            elif provider_status == "in_progress":
                state = GenericRealExecutionState.NO_ACTION
                code = GenericRealResultCode.ALREADY_IN_PROGRESS
                accepted = True
                executable = True
            elif provider_status in {
                "unsupported",
                "rejected",
            }:
                state = GenericRealExecutionState.REJECTED
                code = GenericRealResultCode.PROVIDER_REJECTED
                accepted = False
                executable = False
            elif (
                provider_command_sent
                and not provider_feedback_confirmed
            ):
                state = GenericRealExecutionState.FAILED
                code = GenericRealResultCode.EFFECT_NOT_CONFIRMED
                accepted = True
                executable = True
            else:
                state = GenericRealExecutionState.FAILED
                code = GenericRealResultCode.COMMAND_FAILED
                accepted = True
                executable = True

            return self._finish(
                started=started,
                generated_at=generated_at,
                execution_id=execution_id,
                state=state,
                code=code,
                accepted=accepted,
                executable=executable,
                executed=provider_executed,
                command_sent=provider_command_sent,
                feedback_confirmed=(
                    provider_feedback_confirmed
                ),
                request=request,
                plan=plan,
                provider_id=provider_id,
                provider_result=provider_result,
                reason=provider_reason,
                error=provider_error,
            )

        except Exception as err:  # noqa: BLE001
            return self._finish(
                started=started,
                generated_at=generated_at,
                execution_id=execution_id,
                state=GenericRealExecutionState.FAILED,
                code=GenericRealResultCode.EXECUTOR_EXCEPTION,
                accepted=False,
                executable=False,
                executed=False,
                command_sent=False,
                feedback_confirmed=False,
                request={
                    "action_id": action_id,
                    "target": dict(target or {}),
                    "parameters": dict(parameters or {}),
                    "confirmed": bool(confirmed),
                },
                plan=None,
                provider_id=None,
                provider_result=None,
                reason="Generic execution engine failed with an exception.",
                error=f"{type(err).__name__}: {err}",
            )

    def _finish(
        self,
        *,
        started: float,
        generated_at: datetime,
        execution_id: str,
        state: GenericRealExecutionState,
        code: GenericRealResultCode,
        accepted: bool,
        executable: bool,
        executed: bool,
        command_sent: bool,
        feedback_confirmed: bool,
        request: dict[str, Any],
        plan: dict[str, Any] | None,
        provider_id: str | None,
        provider_result: dict[str, Any] | None,
        reason: str,
        error: str | None,
    ) -> GenericRealExecutionResult:
        finished_at = datetime.now(UTC)
        return GenericRealExecutionResult(
            api_version=self.API_VERSION,
            execution_contract=self.VERSION,
            execution_id=execution_id,
            generated_at=generated_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_ms=round((perf_counter() - started) * 1000, 2),
            state=state,
            result_code=code,
            accepted=accepted,
            executable=executable,
            execution_enabled=True,
            executed=executed,
            command_sent=command_sent,
            feedback_confirmed=feedback_confirmed,
            request=request,
            plan=plan,
            provider_id=provider_id,
            provider_result=provider_result,
            reason=reason,
            error=error,
        )
