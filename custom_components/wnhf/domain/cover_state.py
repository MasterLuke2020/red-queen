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
    feedback_open: bool
    feedback_closed: bool
    feedback_opening: bool
    feedback_closing: bool
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
    def is_not_fully_open(self) -> bool:
        """Return the PLC's safety-oriented not-fully-open feedback."""
        return self.feedback_closed

    @property
    def message(self) -> str:
        if self.is_error:
            return f"{self.cover.name}: Fehler ({', '.join(self.errors)})."
        return f"{self.cover.name}: {self.state.value}."

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.cover.object_id,
            "name": self.cover.name,
            "room_id": self.cover.room_id,
            "state": self.state.value,
            "is_open": self.is_open,
            "is_closed": self.is_closed,
            "is_opening": self.is_opening,
            "is_closing": self.is_closing,
            "is_moving": self.is_moving,
            "is_intermediate": self.is_intermediate,
            "is_error": self.is_error,
            "is_not_fully_open": self.is_not_fully_open,
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
    """Evaluate normalized cover states from objective feedback bits."""

    @staticmethod
    def evaluate(
        cover: Cover,
        *,
        feedback_open: bool,
        feedback_closed: bool,
        feedback_opening: bool,
        feedback_closing: bool,
    ) -> CoverSnapshot:
        errors: list[str] = []

        # The PLC uses the "closed" signal as a safety-oriented
        # "not fully open" indication. It may therefore remain active while
        # the blind is opening. Movement always has priority over static
        # position feedback.
        if feedback_open and feedback_closed:
            errors.append("open_and_not_open")
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

        return CoverSnapshot(
            cover=cover,
            state=state,
            feedback_open=feedback_open,
            feedback_closed=feedback_closed,
            feedback_opening=feedback_opening,
            feedback_closing=feedback_closing,
            errors=tuple(errors),
        )
