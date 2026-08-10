"""Safe dry-run execution planning."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .model import ExecutionPlan, ExecutionStatus, ExecutionStep


class ExecutionPlanner:
    """Turn a read-only DecisionResult into a validated dry-run plan."""

    SUPPORTED_ACTIONS = {
        "lighting.all_off",
        "lighting.room_off",
        "lighting.object_off",
    }

    @staticmethod
    def _light_is_on(snapshot_by_id: dict[str, Any], light_id: str) -> bool:
        snapshot = snapshot_by_id.get(light_id)
        return bool(snapshot is not None and snapshot.is_on)

    @classmethod
    def plan(
        cls,
        *,
        decision,
        house,
        light_snapshots: list,
    ) -> ExecutionPlan:
        errors: list[str] = []
        reasons: list[str] = [decision.reason]
        steps: list[ExecutionStep] = []
        action = decision.action
        target = dict(decision.target)
        snapshots = {item.light.object_id: item for item in light_snapshots}

        if not decision.configured:
            errors.append("Decision is not configured.")
        elif not decision.enabled:
            errors.append("Decision is disabled.")

        if action not in cls.SUPPORTED_ACTIONS:
            errors.append(f"Unsupported execution action: {action!r}")

        selected = []
        if not errors and action == "lighting.all_off":
            selected = sorted(
                house.controllable_lights,
                key=lambda item: (item.room_id, item.object_id),
            )
        elif not errors and action == "lighting.room_off":
            room_id = target.get("room_id")
            if not isinstance(room_id, str) or room_id not in house.rooms:
                errors.append("Target needs a known room_id.")
            else:
                selected = sorted(
                    (
                        item for item in house.controllable_lights
                        if item.room_id == room_id
                    ),
                    key=lambda item: item.object_id,
                )
        elif not errors and action == "lighting.object_off":
            light_id = target.get("light_id")
            if not isinstance(light_id, str) or light_id not in house.lights:
                errors.append("Target needs a known light_id.")
            else:
                light = house.lights[light_id]
                if not light.controllable:
                    errors.append(
                        f"Light '{light_id}' is not safely controllable."
                    )
                else:
                    selected = [light]

        total_object_count = len(selected)
        active_object_count = 0
        skipped_object_count = 0
        invalid_object_count = 0

        for light in selected:
            is_on = cls._light_is_on(snapshots, light.object_id)
            valid = light.controllable and light.command_entity_id is not None

            if not valid:
                invalid_object_count += 1
                continue

            if not is_on:
                skipped_object_count += 1
                continue

            active_object_count += 1
            steps.append(
                ExecutionStep(
                    step=len(steps) + 1,
                    object_id=light.object_id,
                    object_name=light.name,
                    room_id=light.room_id,
                    operation="turn_off",
                    command_entity_id=light.command_entity_id,
                    currently_active=True,
                    valid=True,
                    reason=(
                        "Would pulse command because light currently reports on."
                    ),
                )
            )

        optimization_ratio = (
            round((skipped_object_count / total_object_count) * 100, 1)
            if total_object_count
            else 0.0
        )

        if errors:
            status = ExecutionStatus.INVALID
        elif not decision.recommended:
            status = ExecutionStatus.NOT_RECOMMENDED
            reasons.append("Decision does not recommend execution.")
        elif not decision.policy_allowed:
            status = ExecutionStatus.BLOCKED
            reasons.append("Policy blocks execution.")
        else:
            status = ExecutionStatus.READY
            reasons.append(
                "Plan is valid, but dry-run mode prevents execution."
            )

        return ExecutionPlan(
            generated_at=datetime.now(UTC),
            decision_id=decision.decision_id,
            status=status,
            dry_run=True,
            executed=False,
            executable=False,
            action=action,
            target=target,
            context=decision.context,
            recommended=decision.recommended,
            policy_allowed=decision.policy_allowed,
            decision_status=decision.status.value,
            validation_errors=tuple(errors),
            reasons=tuple(reasons),
            total_object_count=total_object_count,
            active_object_count=active_object_count,
            skipped_object_count=skipped_object_count,
            invalid_object_count=invalid_object_count,
            optimization_ratio=optimization_ratio,
            optimizer_version="1.0",
            steps=tuple(steps),
            decision=decision.as_dict(),
        )
