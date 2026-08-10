"""Framework and registry validation for WNHF."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from time import perf_counter

from homeassistant.core import HomeAssistant

from ..domain.house import House
from ..domain.cover_state import CoverState
from .report import ValidationIssue, ValidationReport


class WNHFValidator:
    """Validate the loaded house model against Home Assistant."""

    def __init__(self, hass: HomeAssistant, engine) -> None:
        self.hass = hass
        self.engine = engine

    def validate(self, house: House) -> ValidationReport:
        """Run all non-destructive validation checks."""
        started = perf_counter()
        issues: list[ValidationIssue] = []

        self._check_structure(house, issues)
        self._check_entity_references(house, issues)
        self._check_duplicate_bindings(house, issues)
        self._check_capability_contracts(house, issues)
        self._check_runtime(house, issues)

        checks = {
            "structure": self._status_for_domains(
                issues, {"structure", "rooms", "lights", "covers", "openings"}
            ),
            "references": self._status_for_domains(
                issues, {"references"}
            ),
            "entities": self._status_for_domains(
                issues, {"entities"}
            ),
            "duplicates": self._status_for_domains(
                issues, {"duplicates"}
            ),
            "capabilities": self._status_for_domains(
                issues, {"capabilities"}
            ),
            "runtime": self._status_for_domains(
                issues, {"runtime"}
            ),
        }

        return ValidationReport(
            generated_at=datetime.now(UTC),
            duration_ms=round((perf_counter() - started) * 1000, 2),
            summary={
                "rooms": len(house.rooms),
                "lights": len(house.lights),
                "enabled_lights": len(house.enabled_lights),
                "covers": len(house.covers),
                "enabled_covers": len(house.enabled_covers),
                "openings": len(house.openings),
                "enabled_openings": len(house.enabled_openings),
                "objects": (
                    len(house.rooms)
                    + len(house.lights)
                    + len(house.covers)
                    + len(house.openings)
                ),
            },
            checks=checks,
            issues=tuple(issues),
        )

    @staticmethod
    def _status_for_domains(
        issues: list[ValidationIssue],
        domains: set[str],
    ) -> str:
        selected = [item for item in issues if item.domain in domains]
        if any(item.severity == "error" for item in selected):
            return "error"
        if any(item.severity == "warning" for item in selected):
            return "warning"
        return "passed"

    def _check_structure(
        self,
        house: House,
        issues: list[ValidationIssue],
    ) -> None:
        """Check object IDs, room membership and basic completeness."""
        collections = (
            ("rooms", house.rooms),
            ("lights", house.lights),
            ("covers", house.covers),
            ("openings", house.openings),
        )

        all_ids: dict[str, str] = {}
        for object_type, objects in collections:
            for object_id, obj in objects.items():
                if object_id in all_ids:
                    issues.append(
                        ValidationIssue(
                            "error",
                            "duplicate_object_id",
                            (
                                f"Object ID is used by both {all_ids[object_id]} "
                                f"and {object_type}."
                            ),
                            object_id=object_id,
                            domain="structure",
                        )
                    )
                all_ids[object_id] = object_type

                if not getattr(obj, "name", ""):
                    issues.append(
                        ValidationIssue(
                            "error",
                            "missing_name",
                            "Object has no display name.",
                            object_id=object_id,
                            domain=object_type,
                        )
                    )

        for room in house.rooms.values():
            if not room.enabled:
                issues.append(
                    ValidationIssue(
                        "info",
                        "object_disabled",
                        "Room is intentionally disabled.",
                        object_id=room.object_id,
                        domain="rooms",
                    )
                )

        for light in house.lights.values():
            if light.room_id not in house.rooms:
                issues.append(
                    ValidationIssue(
                        "error",
                        "unknown_room",
                        f"Referenced room does not exist: {light.room_id}",
                        object_id=light.object_id,
                        domain="lights",
                    )
                )
            if not light.enabled:
                issues.append(
                    ValidationIssue(
                        "info",
                        "object_disabled",
                        "Light is intentionally disabled.",
                        object_id=light.object_id,
                        domain="lights",
                    )
                )
                continue
            if light.control_mode == "toggle":
                if not light.command_entity_id:
                    issues.append(
                        ValidationIssue(
                            "error",
                            "missing_command",
                            "Impulse-controlled light has no command entity.",
                            object_id=light.object_id,
                            domain="lights",
                        )
                    )
                if not light.state_entity_ids:
                    issues.append(
                        ValidationIssue(
                            "error",
                            "missing_feedback",
                            "Impulse-controlled light has no feedback entity.",
                            object_id=light.object_id,
                            domain="lights",
                        )
                    )

        required_cover_capabilities = {
            "open", "close", "blades_open", "blades_close"
        }
        for cover in house.covers.values():
            if cover.room_id not in house.rooms:
                issues.append(
                    ValidationIssue(
                        "error",
                        "unknown_room",
                        f"Referenced room does not exist: {cover.room_id}",
                        object_id=cover.object_id,
                        domain="covers",
                    )
                )
            if not cover.enabled:
                issues.append(
                    ValidationIssue(
                        "info",
                        "object_disabled",
                        "Cover is intentionally disabled.",
                        object_id=cover.object_id,
                        domain="covers",
                    )
                )
            missing = required_cover_capabilities - set(cover.capabilities)
            if missing:
                issues.append(
                    ValidationIssue(
                        "error",
                        "missing_capability",
                        f"Missing capabilities: {', '.join(sorted(missing))}.",
                        object_id=cover.object_id,
                        domain="covers",
                    )
                )

        for opening in house.openings.values():
            if opening.room_id not in house.rooms:
                issues.append(
                    ValidationIssue(
                        "error",
                        "unknown_room",
                        f"Referenced room does not exist: {opening.room_id}",
                        object_id=opening.object_id,
                        domain="openings",
                    )
                )
            if not opening.enabled:
                issues.append(
                    ValidationIssue(
                        "info",
                        "object_disabled",
                        "Opening is intentionally disabled.",
                        object_id=opening.object_id,
                        domain="openings",
                    )
                )
            if opening.garage_door is not None:
                # A dedicated garage door derives its runtime state from two
                # end-position sensors. It deliberately has no single
                # state_entity_id and therefore requires no open_states list.
                if opening.opening_type != "garage_door":
                    issues.append(
                        ValidationIssue(
                            "error",
                            "invalid_garage_configuration",
                            "Dedicated garage configuration is allowed only "
                            "for garage_door openings.",
                            object_id=opening.object_id,
                            domain="openings",
                        )
                    )
            else:
                # Windows, sliding doors, normal doors and legacy garage-door
                # entries use the common single-state feedback model.
                if not opening.state_entity_id:
                    issues.append(
                        ValidationIssue(
                            "error",
                            "missing_state_entity",
                            "Opening has no configured state entity.",
                            object_id=opening.object_id,
                            domain="openings",
                        )
                    )
                if not opening.open_states:
                    issues.append(
                        ValidationIssue(
                            "error",
                            "missing_open_states",
                            "Opening has no configured open states.",
                            object_id=opening.object_id,
                            domain="openings",
                        )
                    )

    def _check_entity_references(
        self,
        house: House,
        issues: list[ValidationIssue],
    ) -> None:
        """Check expected entity domains, existence and availability."""
        references: list[tuple[str, str, str, bool]] = []

        for light in house.lights.values():
            if not light.enabled:
                continue
            if light.command_entity_id:
                references.append(
                    (light.object_id, light.command_entity_id, "button", True)
                )
            for entity_id in light.state_entity_ids:
                references.append(
                    (light.object_id, entity_id, "binary_sensor", True)
                )

        for cover in house.covers.values():
            if not cover.enabled:
                continue
            for entity_id in (
                cover.open_command_entity_id,
                cover.close_command_entity_id,
                cover.blades_open_command_entity_id,
                cover.blades_close_command_entity_id,
            ):
                references.append(
                    (cover.object_id, entity_id, "button", True)
                )
            for entity_id in (
                cover.open_feedback_entity_id,
                cover.closed_feedback_entity_id,
                cover.opening_feedback_entity_id,
                cover.closing_feedback_entity_id,
            ):
                references.append(
                    (cover.object_id, entity_id, "binary_sensor", True)
                )

        for opening in house.openings.values():
            if not opening.enabled:
                continue

            if opening.state_entity_id:
                references.append(
                    (
                        opening.object_id,
                        opening.state_entity_id,
                        ("binary_sensor", "sensor"),
                        True,
                    )
                )

            if opening.lock is not None:
                references.append(
                    (
                        opening.object_id,
                        opening.lock.feedback_entity_id,
                        "binary_sensor",
                        True,
                    )
                )
                if opening.lock.lock_command_entity_id:
                    references.append(
                        (
                            opening.object_id,
                            opening.lock.lock_command_entity_id,
                            "button",
                            True,
                        )
                    )
                if opening.lock.unlock_command_entity_id:
                    references.append(
                        (
                            opening.object_id,
                            opening.lock.unlock_command_entity_id,
                            "button",
                            True,
                        )
                    )

            if opening.door_opener is not None:
                references.append(
                    (
                        opening.object_id,
                        opening.door_opener.command_entity_id,
                        "button",
                        True,
                    )
                )

            if opening.garage_door is not None:
                references.extend(
                    (
                        (
                            opening.object_id,
                            opening.garage_door.open_feedback_entity_id,
                            "binary_sensor",
                            True,
                        ),
                        (
                            opening.object_id,
                            opening.garage_door.closed_feedback_entity_id,
                            "binary_sensor",
                            True,
                        ),
                        (
                            opening.object_id,
                            opening.garage_door.toggle_command_entity_id,
                            "button",
                            True,
                        ),
                    )
                )
                if opening.garage_door.stop_command_entity_id:
                    references.append(
                        (
                            opening.object_id,
                            opening.garage_door.stop_command_entity_id,
                            "button",
                            True,
                        )
                    )

        for object_id, entity_id, expected_domain, required in references:
            actual_domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
            allowed_domains = (
                expected_domain
                if isinstance(expected_domain, tuple)
                else (expected_domain,)
            )
            if actual_domain not in allowed_domains:
                expected_text = " or ".join(
                    f"'{domain}'" for domain in allowed_domains
                )
                issues.append(
                    ValidationIssue(
                        "error",
                        "wrong_entity_domain",
                        (
                            f"Expected domain {expected_text}, "
                            f"found '{actual_domain or 'none'}'."
                        ),
                        object_id=object_id,
                        entity_id=entity_id,
                        domain="references",
                    )
                )
                continue

            state = self.hass.states.get(entity_id)
            if state is None:
                issues.append(
                    ValidationIssue(
                        "error" if required else "warning",
                        "entity_missing",
                        "Referenced Home Assistant entity does not exist.",
                        object_id=object_id,
                        entity_id=entity_id,
                        domain="entities",
                    )
                )
                continue

            if state.state == "unavailable":
                issues.append(
                    ValidationIssue(
                        "warning",
                        "entity_unavailable",
                        "Referenced Home Assistant entity is unavailable.",
                        object_id=object_id,
                        entity_id=entity_id,
                        domain="entities",
                    )
                )
            elif state.state == "unknown" and actual_domain != "button":
                issues.append(
                    ValidationIssue(
                        "warning",
                        "entity_unknown",
                        "Referenced Home Assistant entity is unknown.",
                        object_id=object_id,
                        entity_id=entity_id,
                        domain="entities",
                    )
                )

    def _check_duplicate_bindings(
        self,
        house: House,
        issues: list[ValidationIssue],
    ) -> None:
        """Detect entity IDs assigned to multiple WNHF objects."""
        command_usage: dict[str, list[str]] = defaultdict(list)
        feedback_usage: dict[str, list[str]] = defaultdict(list)

        for light in house.lights.values():
            if not light.enabled:
                continue
            if light.command_entity_id:
                command_usage[light.command_entity_id].append(light.object_id)
            for entity_id in light.state_entity_ids:
                feedback_usage[entity_id].append(light.object_id)

        for cover in house.covers.values():
            if not cover.enabled:
                continue
            for entity_id in (
                cover.open_command_entity_id,
                cover.close_command_entity_id,
                cover.blades_open_command_entity_id,
                cover.blades_close_command_entity_id,
            ):
                command_usage[entity_id].append(cover.object_id)
            for entity_id in (
                cover.open_feedback_entity_id,
                cover.closed_feedback_entity_id,
                cover.opening_feedback_entity_id,
                cover.closing_feedback_entity_id,
            ):
                feedback_usage[entity_id].append(cover.object_id)

        for opening in house.openings.values():
            if not opening.enabled:
                continue

            if opening.state_entity_id:
                feedback_usage[opening.state_entity_id].append(
                    opening.object_id
                )

            if opening.lock is not None:
                feedback_usage[opening.lock.feedback_entity_id].append(
                    opening.object_id
                )
                if opening.lock.lock_command_entity_id:
                    command_usage[
                        opening.lock.lock_command_entity_id
                    ].append(opening.object_id)
                if opening.lock.unlock_command_entity_id:
                    command_usage[
                        opening.lock.unlock_command_entity_id
                    ].append(opening.object_id)

            if opening.door_opener is not None:
                command_usage[
                    opening.door_opener.command_entity_id
                ].append(opening.object_id)

            if opening.garage_door is not None:
                feedback_usage[
                    opening.garage_door.open_feedback_entity_id
                ].append(opening.object_id)
                feedback_usage[
                    opening.garage_door.closed_feedback_entity_id
                ].append(opening.object_id)
                command_usage[
                    opening.garage_door.toggle_command_entity_id
                ].append(opening.object_id)
                if opening.garage_door.stop_command_entity_id:
                    command_usage[
                        opening.garage_door.stop_command_entity_id
                    ].append(opening.object_id)

        for entity_id, object_ids in command_usage.items():
            unique_ids = sorted(set(object_ids))
            if len(unique_ids) > 1:
                issues.append(
                    ValidationIssue(
                        "error",
                        "duplicate_command_binding",
                        f"Command is shared by: {', '.join(unique_ids)}.",
                        entity_id=entity_id,
                        domain="duplicates",
                    )
                )

        for entity_id, object_ids in feedback_usage.items():
            unique_ids = sorted(set(object_ids))
            if len(unique_ids) > 1:
                issues.append(
                    ValidationIssue(
                        "warning",
                        "duplicate_feedback_binding",
                        f"Feedback is shared by: {', '.join(unique_ids)}.",
                        entity_id=entity_id,
                        domain="duplicates",
                    )
                )

    def _check_capability_contracts(
        self,
        house: House,
        issues: list[ValidationIssue],
    ) -> None:
        """Validate generic semantic capability declarations."""
        catalog = self.engine.capability_catalog
        objects = [*house.lights.values(), *house.openings.values()]

        for item in objects:
            for declaration in item.object_capabilities():
                definition = catalog.get(declaration.capability_id)
                if definition is None:
                    issues.append(ValidationIssue(
                        "error",
                        "unknown_capability",
                        "Object declares an unknown capability.",
                        object_id=declaration.object_id,
                        entity_id=None,
                        domain="capabilities",
                    ))
                    continue

                if (
                    definition.requires_command
                    and not declaration.command_entity_ids
                ):
                    issues.append(ValidationIssue(
                        "error",
                        "missing_capability_command",
                        (
                            f"Capability '{definition.capability_id}' "
                            "requires a command entity."
                        ),
                        object_id=declaration.object_id,
                        entity_id=None,
                        domain="capabilities",
                    ))

                if (
                    definition.requires_feedback
                    and not declaration.feedback_entity_ids
                ):
                    issues.append(ValidationIssue(
                        "error",
                        "missing_capability_feedback",
                        (
                            f"Capability '{definition.capability_id}' "
                            "requires feedback."
                        ),
                        object_id=declaration.object_id,
                        entity_id=None,
                        domain="capabilities",
                    ))

    def _check_runtime(
        self,
        house: House,
        issues: list[ValidationIssue],
    ) -> None:
        """Check contradictory runtime feedback combinations."""
        for cover in house.enabled_covers:
            snapshot = self.engine.cover_snapshot(cover.object_id)
            if snapshot.state is CoverState.ERROR:
                issues.append(
                    ValidationIssue(
                        "error",
                        "cover_runtime_error",
                        (
                            "Contradictory cover feedback: "
                            f"{', '.join(snapshot.errors)}."
                        ),
                        object_id=cover.object_id,
                        domain="runtime",
                    )
                )

        for light in house.enabled_lights:
            snapshot = self.engine.light_snapshot(light.object_id)
            if not snapshot.available:
                # Entity-specific details are already reported by entity checks.
                continue
            if light.control_mode == "toggle" and not light.controllable:
                issues.append(
                    ValidationIssue(
                        "error",
                        "light_not_controllable",
                        "Enabled impulse-controlled light is not controllable.",
                        object_id=light.object_id,
                        domain="runtime",
                    )
                )
