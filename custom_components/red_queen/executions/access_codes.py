"""Stable machine-readable Access execution result catalog."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ResultCategory(StrEnum):
    """High-level result category."""

    SUCCESS = "success"
    NO_ACTION = "no_action"
    REJECTED = "rejected"
    FAILURE = "failure"
    INTERNAL = "internal"


class ResultSeverity(StrEnum):
    """Operational severity of one result."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class AccessResultCode:
    """Stable Access execution result definition."""

    code: str
    key: str
    category: ResultCategory
    severity: ResultSeverity
    retryable: bool
    description: str

    @property
    def is_error(self) -> bool:
        """Return whether this result represents an error."""
        return self.category in {
            ResultCategory.REJECTED,
            ResultCategory.FAILURE,
            ResultCategory.INTERNAL,
        }

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable result definition."""
        return {
            "code": self.code,
            "key": self.key,
            "category": self.category.value,
            "severity": self.severity.value,
            "retryable": self.retryable,
            "description": self.description,
        }


class AccessResultCatalog:
    """Stable Access result catalog.

    Existing codes are never reassigned to a different meaning.
    """

    VERSION = "1.0"

    SUCCEEDED = AccessResultCode(
        "ACC-000",
        "succeeded",
        ResultCategory.SUCCESS,
        ResultSeverity.INFO,
        False,
        "Command and all required effects completed successfully.",
    )
    ALREADY_SATISFIED = AccessResultCode(
        "ACC-100",
        "already_satisfied",
        ResultCategory.NO_ACTION,
        ResultSeverity.INFO,
        False,
        "The requested target state was already present.",
    )
    OPTIONAL_EFFECT_NOT_OBSERVED = AccessResultCode(
        "ACC-101",
        "optional_effect_not_observed",
        ResultCategory.SUCCESS,
        ResultSeverity.INFO,
        False,
        "The command succeeded; an optional effect was not observed.",
    )

    CONFIRMATION_REQUIRED = AccessResultCode(
        "ACC-200",
        "confirmation_required",
        ResultCategory.REJECTED,
        ResultSeverity.WARNING,
        False,
        "Explicit confirmation is required before dispatch.",
    )
    CAPABILITY_NOT_PERMITTED = AccessResultCode(
        "ACC-201",
        "capability_not_permitted",
        ResultCategory.REJECTED,
        ResultSeverity.WARNING,
        False,
        "The requested capability is not permitted by this executor.",
    )
    OBJECT_NOT_FOUND = AccessResultCode(
        "ACC-202",
        "object_not_found",
        ResultCategory.REJECTED,
        ResultSeverity.ERROR,
        False,
        "The requested semantic Access object does not exist.",
    )
    OBJECT_DISABLED = AccessResultCode(
        "ACC-203",
        "object_disabled",
        ResultCategory.REJECTED,
        ResultSeverity.WARNING,
        False,
        "The requested Access object is disabled.",
    )
    CAPABILITY_UNQUALIFIED = AccessResultCode(
        "ACC-204",
        "capability_unqualified",
        ResultCategory.REJECTED,
        ResultSeverity.ERROR,
        False,
        "The resolved capability is unsupported, unavailable or unhealthy.",
    )
    FEEDBACK_UNAVAILABLE = AccessResultCode(
        "ACC-205",
        "feedback_unavailable",
        ResultCategory.REJECTED,
        ResultSeverity.ERROR,
        True,
        "Required runtime feedback is unavailable.",
    )
    CONTRADICTORY_FEEDBACK = AccessResultCode(
        "ACC-206",
        "contradictory_feedback",
        ResultCategory.REJECTED,
        ResultSeverity.ERROR,
        True,
        "Runtime feedback is contradictory.",
    )
    TRANSITION_IN_PROGRESS = AccessResultCode(
        "ACC-207",
        "transition_in_progress",
        ResultCategory.REJECTED,
        ResultSeverity.WARNING,
        True,
        "A physical transition is already in progress.",
    )
    INTERMEDIATE_STATE = AccessResultCode(
        "ACC-208",
        "intermediate_state",
        ResultCategory.REJECTED,
        ResultSeverity.WARNING,
        False,
        "The object is in an ambiguous intermediate state.",
    )
    INVALID_INITIAL_STATE = AccessResultCode(
        "ACC-209",
        "invalid_initial_state",
        ResultCategory.REJECTED,
        ResultSeverity.ERROR,
        True,
        "The object does not report a valid initial state.",
    )
    OPEN_DOOR_LOCK_REJECTED = AccessResultCode(
        "ACC-210",
        "open_door_lock_rejected",
        ResultCategory.REJECTED,
        ResultSeverity.WARNING,
        False,
        "Lock or unlock execution is not permitted while the door is open.",
    )

    COMMAND_DISPATCH_FAILED = AccessResultCode(
        "ACC-300",
        "command_dispatch_failed",
        ResultCategory.FAILURE,
        ResultSeverity.ERROR,
        True,
        "The technical command could not be completed.",
    )
    REQUIRED_EFFECT_TIMEOUT = AccessResultCode(
        "ACC-301",
        "required_effect_timeout",
        ResultCategory.FAILURE,
        ResultSeverity.ERROR,
        True,
        "A required physical effect was not confirmed before timeout.",
    )
    TRANSITION_TIMEOUT = AccessResultCode(
        "ACC-302",
        "transition_timeout",
        ResultCategory.FAILURE,
        ResultSeverity.ERROR,
        True,
        "The expected movement transition was not observed before timeout.",
    )
    TERMINAL_STATE_TIMEOUT = AccessResultCode(
        "ACC-303",
        "terminal_state_timeout",
        ResultCategory.FAILURE,
        ResultSeverity.ERROR,
        True,
        "The expected terminal state was not confirmed before timeout.",
    )
    EXECUTOR_EXCEPTION = AccessResultCode(
        "ACC-900",
        "executor_exception",
        ResultCategory.INTERNAL,
        ResultSeverity.ERROR,
        True,
        "The executor failed with an unexpected exception.",
    )

    @classmethod
    def definitions(cls) -> tuple[AccessResultCode, ...]:
        """Return all definitions in stable code order."""
        values = [
            value
            for name, value in vars(cls).items()
            if name.isupper() and isinstance(value, AccessResultCode)
        ]
        return tuple(sorted(values, key=lambda item: item.code))

    @classmethod
    def by_code(cls, code: str) -> AccessResultCode | None:
        """Resolve one result definition by stable code."""
        return next(
            (item for item in cls.definitions() if item.code == code),
            None,
        )

    @classmethod
    def as_dict(cls) -> dict[str, Any]:
        """Return the complete machine-readable catalog."""
        definitions = cls.definitions()
        return {
            "catalog_id": "wnhf.access_result_codes",
            "version": cls.VERSION,
            "count": len(definitions),
            "definitions": [item.as_dict() for item in definitions],
        }
