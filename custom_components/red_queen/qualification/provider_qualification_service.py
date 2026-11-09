"""Installation-neutral provider qualification view.

WP-4.7.8.3 removes the former curated, house-specific provider evidence
profiles. Provider qualification is now derived exclusively from the canonical
Stage-4.7 semantic execution evidence store and the currently registered
providers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..providers.registry import WNHFProviderRegistry
from .execution_evidence_store import ExecutionEvidenceStore


class ProviderQualificationService:
    """Build provider-centric qualification from canonical execution evidence."""

    API_VERSION = "1.1"
    VERSION = "2.0-stage4.7.8.3"
    ARCHITECTURE = "stage4.7_execution_evidence"

    def __init__(
        self,
        provider_registry: WNHFProviderRegistry,
        evidence_store: ExecutionEvidenceStore,
        *,
        legacy_store_path: str,
    ) -> None:
        self._providers = provider_registry
        self._store = evidence_store
        self._legacy_store_path = legacy_store_path

    def snapshot(self) -> dict[str, Any]:
        """Return qualification for the providers registered in this runtime."""
        evidence = self._store.values()
        registered_ids = set(self._providers.provider_ids())

        provider_items: list[dict[str, Any]] = []
        for provider in self._providers.providers():
            provider_evidence = tuple(
                item
                for item in evidence
                if item.provider_id == provider.provider_id
            )
            runtime = provider.runtime_state()
            metadata = provider.metadata().as_dict()

            evidence_count = len(provider_evidence)
            pass_count = sum(item.pass_count for item in provider_evidence)
            hardware_verified = any(
                item.hardware_verified for item in provider_evidence
            )
            framework_verified = any(
                item.framework_verified for item in provider_evidence
            )
            first_verified = min(
                (item.first_verified for item in provider_evidence),
                default=None,
            )
            last_verified = max(
                (item.last_verified for item in provider_evidence),
                default=None,
            )

            if framework_verified:
                status = "framework_verified"
            elif evidence_count:
                status = "evidence_present"
            else:
                status = "unverified"

            provider_items.append({
                "provider_id": provider.provider_id,
                "provider_version": metadata["provider_version"],
                "qualification_version": self.VERSION,
                "qualification_status": status,
                "hardware_verified": hardware_verified,
                "framework_verified": framework_verified,
                "supported_capabilities": list(
                    provider.supported_capabilities()
                ),
                "evidence_actions": sorted({
                    item.action_id for item in provider_evidence
                }),
                "statistics": {
                    "evidence": evidence_count,
                    "pass_count": pass_count,
                },
                "first_verified": first_verified,
                "last_verified": last_verified,
                "evidence": [
                    item.as_dict() for item in provider_evidence
                ],
                "runtime": {
                    "loaded": runtime.loaded,
                    "available": runtime.available,
                    "healthy": runtime.healthy,
                    "runtime_validated": runtime.runtime_validated,
                    "lifecycle_state": runtime.lifecycle_state.value,
                    "last_error": runtime.last_error,
                },
                "confidence": {
                    "model": "canonical_execution_evidence",
                    "framework_verification": {
                        "status": (
                            "verified"
                            if framework_verified
                            else "not_verified"
                        ),
                        "verified": framework_verified,
                    },
                    "note": (
                        "Qualification reports observed evidence only; it is "
                        "not an execution authorization or safety override."
                    ),
                },
            })

        orphaned = tuple(
            item for item in evidence
            if item.provider_id not in registered_ids
        )
        store_snapshot = self._store.snapshot()

        return {
            "api_version": self.API_VERSION,
            "qualification_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "architecture": self.ARCHITECTURE,
            "policy": {
                "canonical_evidence_source": (
                    "execution_evidence_store"
                ),
                "automatic_collection_enabled": True,
                "framework_persistence_enabled": True,
                "installation_specific_evidence_bundled": False,
                "curated_manual_profiles_enabled": False,
                "legacy_provider_evidence_consumed": False,
                "qualification_is_execution_authorization": False,
            },
            "summary": {
                "providers": len(provider_items),
                "providers_with_evidence": sum(
                    int(item["statistics"]["evidence"] > 0)
                    for item in provider_items
                ),
                "hardware_verified": sum(
                    int(bool(item["hardware_verified"]))
                    for item in provider_items
                ),
                "framework_verified": sum(
                    int(bool(item["framework_verified"]))
                    for item in provider_items
                ),
                "evidence": len(evidence),
                "pass_count": sum(item.pass_count for item in evidence),
                "orphaned_evidence": len(orphaned),
            },
            "providers": provider_items,
            "orphaned_evidence": [
                item.as_dict() for item in orphaned
            ],
            "store": store_snapshot,
            "legacy_provider_evidence_store": {
                "path": self._legacy_store_path,
                "loaded": False,
                "consumed": False,
                "automatically_deleted": False,
                "note": (
                    "Legacy Stage-4.4 provider evidence is intentionally "
                    "ignored. Existing installation files are left untouched "
                    "for non-destructive migration."
                ),
            },
        }
