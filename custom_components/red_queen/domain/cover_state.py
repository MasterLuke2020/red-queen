"""Runtime state model for WNHF covers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .cover import Cover


class CoverState(StrEnum):
    """Normalized WNHF cover states."""

    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"
    INTERMEDIATE = "intermediate"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class CoverSnapshot:
    """Immutable runtime snapshot of one cover."""

    cover: Cover
    state: CoverState
    available: bool
    feedback_open: bool
    feedback_closed: bool
    feedback_opening: bool
    feedback_closing: bool
    closed_percent: float | None
    current_position: int | None
    position_available: bool
    position_warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_open(self) -> bool:
        return self.state is CoverState.OPEN

    @property
    def is_closed(self) -> bool:
        return self.state is CoverState.CLOSED

    @property
    def is_opening(self) -> bool:
        return self.state is CoverState.OPENING

    @property
    def is_closing(self) -> bool:
        return self.state is CoverState.CLOSING

    @property
    def is_moving(self) -> bool:
        return self.state in {CoverState.OPENING, CoverState.CLOSING}

    @property
    def is_intermediate(self) -> bool:
        return self.state is CoverState.INTERMEDIATE

    @property
    def is_error(self) -> bool:
        return self.state is CoverState.ERROR

    @property
    def message(self) -> str:
        if self.is_error:
            return f"{self.cover.name}: Fehler ({', '.join(self.errors)})."
        if self.current_position is not None:
            return (
                f"{self.cover.name}: {self.state.value}, "
                f"Position {self.current_position}%."
            )
        return f"{self.cover.name}: {self.state.value}."

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.cover.object_id,
            "name": self.cover.name,
            "room_id": self.cover.room_id,
            "state": self.state.value,
            "available": self.available,
            "is_open": self.is_open,
            "is_closed": self.is_closed,
            "is_opening": self.is_opening,
            "is_closing": self.is_closing,
            "is_moving": self.is_moving,
            "is_intermediate": self.is_intermediate,
            "is_error": self.is_error,
            "closed_percent": self.closed_percent,
            "current_position": self.current_position,
            "position_available": self.position_available,
            "position_warnings": list(self.position_warnings),
            "errors": list(self.errors),
            "feedback": {
                "open": self.feedback_open,
                "closed": self.feedback_closed,
                "opening": self.feedback_opening,
                "closing": self.feedback_closing,
            },
            "message": self.message,
        }


class CoverStateMachine:
    """Evaluate normalized cover state from objective PLC feedback."""

    @staticmethod
    def evaluate(
        cover: Cover,
        *,
        available: bool = True,
        feedback_open: bool,
        feedback_closed: bool,
        feedback_opening: bool,
        feedback_closing: bool,
        closed_percent: float | None = None,
        position_available: bool = False,
    ) -> CoverSnapshot:
        errors: list[str] = []
        position_warnings: list[str] = []

        if feedback_open and feedback_closed:
            errors.append("open_and_closed")
        if feedback_opening and feedback_closing:
            errors.append("opening_and_closing")

        if errors:
            state = CoverState.ERROR
        elif feedback_opening:
            state = CoverState.OPENING
        elif feedback_closing:
            state = CoverState.CLOSING
        elif feedback_open:
            state = CoverState.OPEN
        elif feedback_closed:
            state = CoverState.CLOSED
        else:
            state = CoverState.INTERMEDIATE

        current_position: int | None = None
        normalized_closed_percent: float | None = None

        if position_available and closed_percent is not None:
            normalized_closed_percent = float(closed_percent)
            if 0.0 <= normalized_closed_percent <= 100.0:
                # Home Assistant cover position uses 0=closed, 100=open.
                current_position = int(round(100.0 - normalized_closed_percent))
                if state is CoverState.OPEN and normalized_closed_percent > 1.0:
                    position_warnings.append("open_position_mismatch")
                if state is CoverState.CLOSED and normalized_closed_percent < 99.0:
                    position_warnings.append("closed_position_mismatch")
            else:
                position_warnings.append("closed_percent_out_of_range")

        return CoverSnapshot(
            cover=cover,
            state=state,
            available=available,
            feedback_open=feedback_open,
            feedback_closed=feedback_closed,
            feedback_opening=feedback_opening,
            feedback_closing=feedback_closing,
            closed_percent=normalized_closed_percent,
            current_position=current_position,
            position_available=(
                position_available and current_position is not None
            ),
            position_warnings=tuple(position_warnings),
            errors=tuple(errors),
        )
