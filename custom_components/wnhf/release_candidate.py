"""Release-preparation metadata, public API classification and qualification."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .const import (
    MINIMUM_DECISION_SCHEMA_VERSION,
    MINIMUM_POLICY_SCHEMA_VERSION,
    MINIMUM_REGISTRY_SCHEMA_VERSION,
    PUBLIC_API_REGISTRY_VERSION,
    CANONICAL_EXECUTION_API_VERSION,
    CANONICAL_EXECUTION_CONTRACT_VERSION,
    LEGACY_PUBLIC_EXECUTION_API_VERSION,
    PUBLIC_EXECUTION_API_VERSION,
    QUALIFICATION_API_VERSION,
    RELEASE_CANDIDATE,
    RELEASE_CHANNEL,
    RELEASE_PHASE,
    RELEASE_INFO_API_VERSION,
    UPGRADE_CHECK_API_VERSION,
    PRODUCT_NAME,
    DEVELOPMENT_NAME,
    DEVELOPMENT_BASELINE_VERSION,
    RELEASE_BASELINE,
    VERSION,
)
from .release_scope import ReleaseScopeManager


class ReleaseProfile:
    """Immutable product metadata for the Red Queen 1.0 release candidate."""

    VERSION = "2.2-rc1"
    CHANNEL = RELEASE_CHANNEL
    PHASE = RELEASE_PHASE
    CANDIDATE = RELEASE_CANDIDATE

    # Public service classification is deliberately exhaustive.  Every
    # service registered by services.py belongs to exactly one category.
    # Stage-4.7 semantic execution is the canonical execution surface; the
    # Decision-ID based Stage-3 execution service remains available only for
    # compatibility with existing installations.
    STABLE_PUBLIC_SERVICES = (
        "execution_execute",
        "execution_dry_run",
        "system_status",
        "release_scope",
        "release_info",
        "public_api",
        "qualification",
        "upgrade_check",
    )

    DIAGNOSTIC_PUBLIC_SERVICES = (
        "transaction_locks",
        "transaction_queue",
        "execution_audit",
        "house_execution_audit",
        "sequential_room_audit",
        "real_step_audit",
        "executions_snapshot",
        "execution_capabilities_snapshot",
        "capabilities_snapshot",
        "object_capabilities_snapshot",
        "provider_qualification",
        "house_snapshot",
        "access_snapshot",
        "context_snapshot",
        "decisions_snapshot",
        "policies_snapshot",
        "rules_snapshot",
        "validate_registry",
        "registry_recovery_report",
        "access_execution_audit",
        "access_result_catalog",
        "provider_contract",
        "provider_registry",
        "provider_discovery",
        "provider_diagnostics",
        "capability_registry",
        "capability_resolver",
        "capability_manager",
        "capability_list",
        "capability_info",
        "execution_manager",
        "execution_action",
        "execution_qualification",
        "execution_runtime_health",
    )

    LEGACY_OR_DEVELOPMENT_SERVICES = (
        "execute",
        "lighting_all_off",
        "lighting_room_off",
        "lighting_object_off",
        "execution_plan",
        "execution_commit",
        "multi_step_plan",
        "multi_step_simulate",
        "multi_step_simulations_snapshot",
        "generic_transaction_run",
        "generic_transactions_snapshot",
        "real_step_execute",
        "access_object_execute",
        "sequential_room_execute",
        "house_execute",
        "decision_evaluate",
        "policy_check",
        "evaluate_rules",
        "list_registry",
        "get_object",
    )

    MAINTENANCE_SERVICES = (
        "reload_registry",
        "reload_rules",
        "reload_policies",
        "reload_decisions",
    )

    @classmethod
    def _classification_summary(cls) -> dict[str, Any]:
        groups = (
            cls.STABLE_PUBLIC_SERVICES,
            cls.DIAGNOSTIC_PUBLIC_SERVICES,
            cls.MAINTENANCE_SERVICES,
            cls.LEGACY_OR_DEVELOPMENT_SERVICES,
        )
        flattened = [service for group in groups for service in group]
        duplicates = sorted(
            {service for service in flattened if flattened.count(service) > 1}
        )
        return {
            "stable": len(cls.STABLE_PUBLIC_SERVICES),
            "diagnostic": len(cls.DIAGNOSTIC_PUBLIC_SERVICES),
            "maintenance": len(cls.MAINTENANCE_SERVICES),
            "legacy_or_development": len(cls.LEGACY_OR_DEVELOPMENT_SERVICES),
            "classified_total": len(flattened),
            "unique_total": len(set(flattened)),
            "duplicates": duplicates,
            "complete": len(flattened) == len(set(flattened)) == 66,
        }

    @classmethod
    def release_info(cls) -> dict[str, Any]:
        scope = ReleaseScopeManager.snapshot()
        return {
            "api_version": RELEASE_INFO_API_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "framework": {
                "name": PRODUCT_NAME,
                "development_name": DEVELOPMENT_NAME,
                "development_baseline_version": DEVELOPMENT_BASELINE_VERSION,
                "release_baseline": RELEASE_BASELINE,
                "version": VERSION,
                "channel": cls.CHANNEL,
                "phase": cls.PHASE,
                "phase_name": "Release Candidate 1",
                "candidate": cls.CANDIDATE,
                "candidate_assigned": cls.CANDIDATE is not None,
            },
            "public_execution_api_version": PUBLIC_EXECUTION_API_VERSION,
            "canonical_execution": {
                "service": "wnhf.execution_execute",
                "api_version": CANONICAL_EXECUTION_API_VERSION,
                "execution_contract": CANONICAL_EXECUTION_CONTRACT_VERSION,
            },
            "legacy_execution": {
                "service": "wnhf.execute",
                "api_version": LEGACY_PUBLIC_EXECUTION_API_VERSION,
                "recommended_for_new_automations": False,
            },
            "release_manager_version": cls.VERSION,
            "scope": {
                "active_domain_count": scope["active_domain_count"],
                "planned_domain_count": scope["planned_domain_count"],
                "active_domains": [
                    item["domain_id"] for item in scope["active_domains"]
                ],
                "planned_domains": [
                    item["domain_id"] for item in scope["planned_domains"]
                ],
            },
            "compatibility": {
                "minimum_registry_schema": MINIMUM_REGISTRY_SCHEMA_VERSION,
                "minimum_decision_schema": MINIMUM_DECISION_SCHEMA_VERSION,
                "minimum_policy_schema": MINIMUM_POLICY_SCHEMA_VERSION,
                "migration_required": False,
            },
            "release_policy": {
                "public_rc_assigned": cls.CANDIDATE is not None,
                "rc_label_must_not_be_inferred_from_version": True,
                "canonical_execution_entry": "wnhf.execution_execute",
            },
        }

    @classmethod
    def public_api(cls) -> dict[str, Any]:
        return {
            "api_version": PUBLIC_API_REGISTRY_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "framework_name": PRODUCT_NAME,
            "framework_version": VERSION,
            "release_channel": cls.CHANNEL,
            "release_phase": cls.PHASE,
            "candidate": cls.CANDIDATE,
            "candidate_assigned": cls.CANDIDATE is not None,
            "policy": {
                "productive_execution_entry": "wnhf.execution_execute",
                "canonical_execution_architecture": "stage4.7_semantic",
                "legacy_execution_entry": "wnhf.execute",
                "legacy_execution_for_new_automations": False,
                "canonical_execution_api_version": CANONICAL_EXECUTION_API_VERSION,
                "canonical_execution_contract": CANONICAL_EXECUTION_CONTRACT_VERSION,
                "legacy_execution_api_version": LEGACY_PUBLIC_EXECUTION_API_VERSION,
                "stable_contract": True,
                "specialized_executors_for_diagnostics_only": True,
            },
            "classification_summary": cls._classification_summary(),
            "stable": [
                {
                    "service": f"wnhf.{service}",
                    "classification": "stable_public",
                }
                for service in cls.STABLE_PUBLIC_SERVICES
            ],
            "diagnostic": [
                {
                    "service": f"wnhf.{service}",
                    "classification": "diagnostic_public",
                }
                for service in cls.DIAGNOSTIC_PUBLIC_SERVICES
            ],
            "maintenance": [
                {
                    "service": f"wnhf.{service}",
                    "classification": "maintenance_public",
                }
                for service in cls.MAINTENANCE_SERVICES
            ],
            "legacy_or_development": [
                {
                    "service": f"wnhf.{service}",
                    "classification": "legacy_or_development",
                    "recommended_for_new_automations": False,
                    **(
                        {
                            "legacy_execution_entry": True,
                            "canonical_execution_entry": "wnhf.execution_execute",
                            "migration_note": (
                                "The legacy service accepts Decision IDs; the canonical "
                                "Stage-4.7 service accepts semantic action_id/target data. "
                                "Migration is therefore intentional, not argument-compatible."
                            ),
                        }
                        if service == "execute"
                        else {}
                    ),
                }
                for service in cls.LEGACY_OR_DEVELOPMENT_SERVICES
            ],
        }

    @classmethod
    def upgrade_check(cls) -> dict[str, Any]:
        return {
            "api_version": UPGRADE_CHECK_API_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "installed_version": VERSION,
            "target_version": VERSION,
            "release_channel": cls.CHANNEL,
            "release_phase": cls.PHASE,
            "candidate": cls.CANDIDATE,
            "candidate_assigned": cls.CANDIDATE is not None,
            "compatible": True,
            "migration_required": False,
            "restart_required_after_install": True,
            "configuration": {
                "registry_preserved": True,
                "decisions_preserved": True,
                "policies_preserved": True,
                "qualification_evidence_preserved": True,
                "custom_configuration_path": "/config/wnhf",
            },
            "minimum_schema_versions": {
                "registry": MINIMUM_REGISTRY_SCHEMA_VERSION,
                "decisions": MINIMUM_DECISION_SCHEMA_VERSION,
                "policies": MINIMUM_POLICY_SCHEMA_VERSION,
            },
            "instructions": [
                "Stop Home Assistant.",
                "Replace only custom_components/wnhf.",
                "Do not replace /config/wnhf.",
                "Remove wnhf __pycache__ directories.",
                "Start Home Assistant.",
                "Run wnhf.execution_runtime_health.",
            ],
        }

    @classmethod
    def qualification(
        cls,
        *,
        system_status: dict[str, Any],
        execution_qualification: dict[str, Any],
    ) -> dict[str, Any]:
        """Return release-candidate diagnostics from current runtime truth."""
        checks_by_id = {
            item["check_id"]: item
            for item in system_status.get("checks", [])
        }
        runtime_checks = (
            "runtime",
            "registry",
            "validation",
            "decisions",
            "policies",
            "capabilities",
            "release_scope",
            "scheduler",
        )
        runtime_results = []
        for check_id in runtime_checks:
            check = checks_by_id.get(check_id)
            status = (
                "pass"
                if check is not None and check.get("status") == "passed"
                else "fail"
            )
            runtime_results.append({
                "qualification_id": f"runtime.{check_id}",
                "status": status,
                "evidence": (
                    check.get("message")
                    if check is not None
                    else "Required system check is missing."
                ),
            })

        evidence_store = execution_qualification.get("store", {})
        evidence_summary = execution_qualification.get("summary", {})
        canonical_results = [
            {
                "qualification_id": "execution.semantic_routing",
                "status": "implemented",
                "evidence": (
                    "wnhf.execution_execute is the canonical Stage-4.7 semantic "
                    "execution entry point."
                ),
            },
            {
                "qualification_id": "execution.feedback_guard",
                "status": "implemented",
                "evidence": (
                    "Guarded hardware execution requires provider-defined runtime "
                    "feedback where required."
                ),
            },
            {
                "qualification_id": "qualification.automatic_collection",
                "status": (
                    "pass"
                    if execution_qualification.get("automatic_collection_enabled")
                    else "fail"
                ),
                "evidence": (
                    "Canonical execution qualification collection is "
                    f"{('enabled' if execution_qualification.get('automatic_collection_enabled') else 'disabled')}."
                ),
            },
            {
                "qualification_id": "qualification.persistence",
                "status": (
                    "pass"
                    if execution_qualification.get("persistence_enabled")
                    and evidence_store.get("loaded")
                    and evidence_store.get("load_error") is None
                    and evidence_store.get("write_error") is None
                    else "fail"
                ),
                "evidence": (
                    "Canonical execution evidence is persisted at "
                    f"{evidence_store.get('path')}."
                ),
            },
        ]

        runtime_pass = all(
            item["status"] == "pass" for item in runtime_results
        )
        canonical_pass = all(
            item["status"] in {"pass", "implemented"}
            for item in canonical_results
        )
        return {
            "api_version": QUALIFICATION_API_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "framework_name": PRODUCT_NAME,
            "framework_version": VERSION,
            "release_channel": cls.CHANNEL,
            "release_phase": cls.PHASE,
            "candidate": cls.CANDIDATE,
            "candidate_assigned": cls.CANDIDATE is not None,
            "overall": "pass" if runtime_pass and canonical_pass else "fail",
            "runtime_ready": bool(system_status.get("runtime_ready")),
            "health_score": system_status.get("health_score"),
            "runtime_qualification": runtime_results,
            "canonical_architecture_qualification": canonical_results,
            "execution_evidence": {
                "automatic_collection_enabled": execution_qualification.get(
                    "automatic_collection_enabled"
                ),
                "persistence_enabled": execution_qualification.get(
                    "persistence_enabled"
                ),
                "summary": evidence_summary,
                "store": evidence_store,
            },
            "policy": {
                "qualification_is_execution_authorization": False,
                "public_rc_assigned": cls.CANDIDATE is not None,
            },
        }


# Deprecated internal import compatibility only.  New code must use
# ReleaseProfile; this alias is not exposed as release branding.
AlphaReleaseCandidate = ReleaseProfile
