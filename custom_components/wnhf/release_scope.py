"""Release scope and diagnostic classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .const import RELEASE_CHANNEL, RELEASE_PHASE, RELEASE_SCOPE_API_VERSION


class LifecycleStage(StrEnum):
    """Lifecycle state of one semantic Red Queen domain."""

    ACTIVE = "active"
    PLANNED = "planned"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class DomainReleaseState:
    domain_id: str
    stage: LifecycleStage
    in_release_scope: bool
    description: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "stage": self.stage.value,
            "in_release_scope": self.in_release_scope,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticClassification:
    classification: str
    release_domain: str
    in_release_scope: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "release_domain": self.release_domain,
            "in_release_scope": self.in_release_scope,
            "reason": self.reason,
        }


class ReleaseScopeManager:
    """Central immutable Red Queen release-candidate profile and warning classifier."""

    VERSION = "2.5-rc5"
    CHANNEL = RELEASE_CHANNEL
    PHASE = RELEASE_PHASE

    # "Active" means that the domain is part of the current framework baseline.
    # It does not imply that every possible mutating action for that domain is
    # already part of the stable public execution API.
    DOMAINS = {
        "rooms": DomainReleaseState(
            "rooms",
            LifecycleStage.ACTIVE,
            True,
            "Semantic house and room structure.",
        ),
        "lighting": DomainReleaseState(
            "lighting",
            LifecycleStage.ACTIVE,
            True,
            (
                "Lighting registry/state plus canonical semantic "
                "lighting.turn_on and lighting.turn_off execution."
            ),
        ),
        "openings": DomainReleaseState(
            "openings",
            LifecycleStage.ACTIVE,
            True,
            (
                "Opening registry, normalized state, openings.snapshot and "
                "confirmed feedback-guarded openings.lock/openings.unlock "
                "canonical execution."
            ),
        ),
        "covers": DomainReleaseState(
            "covers",
            LifecycleStage.ACTIVE,
            True,
            (
                "Cover registry, normalized end/movement state, continuous "
                "position feedback and covers.snapshot plus canonical covers.open "
                "and covers.close execution. Blade/slat commands remain native-only "
                "until objective blade-position feedback exists."
            ),
        ),
        "security": DomainReleaseState(
            "security",
            LifecycleStage.ACTIVE,
            True,
            "Security aggregation and security.snapshot.",
        ),
        "providers": DomainReleaseState(
            "providers",
            LifecycleStage.ACTIVE,
            True,
            "Provider contract, internal discovery, registry and diagnostics.",
        ),
        "capabilities": DomainReleaseState(
            "capabilities",
            LifecycleStage.ACTIVE,
            True,
            "Capability contract, registry, resolver and manager.",
        ),
        "qualification": DomainReleaseState(
            "qualification",
            LifecycleStage.ACTIVE,
            True,
            "Persistent canonical execution evidence and provider qualification.",
        ),
        "validation": DomainReleaseState(
            "validation",
            LifecycleStage.ACTIVE,
            True,
            "Registry validation and runtime diagnostics.",
        ),
        "rules": DomainReleaseState(
            "rules",
            LifecycleStage.ACTIVE,
            True,
            "Rule registry and context evaluation support.",
        ),
        "context": DomainReleaseState(
            "context",
            LifecycleStage.ACTIVE,
            True,
            "Semantic context state and scoring.",
        ),
        "policies": DomainReleaseState(
            "policies",
            LifecycleStage.ACTIVE,
            True,
            "Policy evaluation; mutating legacy routes remain compatibility-only.",
        ),
        "decisions": DomainReleaseState(
            "decisions",
            LifecycleStage.ACTIVE,
            True,
            "Decision evaluation; Decision-ID execution is a legacy compatibility path.",
        ),
        "execution": DomainReleaseState(
            "execution",
            LifecycleStage.ACTIVE,
            True,
            "Stage-4.7 semantic execution is the canonical productive path.",
        ),
        "scheduler": DomainReleaseState(
            "scheduler",
            LifecycleStage.ACTIVE,
            True,
            "Transaction locking and FIFO diagnostics for legacy compatibility execution.",
        ),
        "climate": DomainReleaseState(
            "climate",
            LifecycleStage.PLANNED,
            False,
            "Temperature and climate semantics are planned.",
        ),
        "media": DomainReleaseState(
            "media",
            LifecycleStage.PLANNED,
            False,
            "Media control semantics are planned.",
        ),
        "notifications": DomainReleaseState(
            "notifications",
            LifecycleStage.PLANNED,
            False,
            "Announcement and notification semantics are planned.",
        ),
        "garage": DomainReleaseState(
            "garage",
            LifecycleStage.ACTIVE,
            True,
            (
                "Residential garage state plus confirmed, end-position-guarded "
                "canonical open/close execution through OSC control."
            ),
        ),
    }

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        active = [
            item.as_dict()
            for item in cls.DOMAINS.values()
            if item.in_release_scope
        ]
        planned = [
            item.as_dict()
            for item in cls.DOMAINS.values()
            if not item.in_release_scope
        ]
        return {
            "api_version": RELEASE_SCOPE_API_VERSION,
            "manager_version": cls.VERSION,
            "channel": cls.CHANNEL,
            "phase": cls.PHASE,
            "active_domain_count": len(active),
            "planned_domain_count": len(planned),
            "active_domains": active,
            "planned_domains": planned,
            # Compatibility aliases retained until the first public stable API
            # freeze.  "supported" means the same as "active" here.
            "supported_domain_count": len(active),
            "supported_domains": active,
        }

    @classmethod
    def classify_validation_item(
        cls,
        item: dict[str, Any],
    ) -> DiagnosticClassification:
        object_id = str(item.get("object_id") or "")
        entity_id = str(item.get("entity_id") or "")

        if object_id.startswith("opening."):
            domain_id = "openings"
        elif object_id.startswith("cover."):
            domain_id = "covers"
        elif object_id.startswith("light."):
            domain_id = "lighting"
        elif "garage_door" in entity_id or ".garage." in object_id:
            domain_id = "garage"
        else:
            domain_id = "validation"

        domain = cls.DOMAINS.get(domain_id)
        if domain is not None and not domain.in_release_scope:
            return DiagnosticClassification(
                classification="out_of_release_scope",
                release_domain=domain_id,
                in_release_scope=False,
                reason=(
                    f"Diagnostic item belongs to planned domain {domain_id!r}; "
                    "it does not affect current release-candidate readiness."
                ),
            )

        return DiagnosticClassification(
            classification="in_release_warning",
            release_domain=domain_id,
            in_release_scope=True,
            reason=(
                "Diagnostic item affects an active domain in the current "
                "release-candidate scope."
            ),
        )
