"""Canonical execution runtime diagnostics."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class ExecutionRuntimeDiagnostics:
    API_VERSION = "1.1"
    VERSION = "1.1-stage4.7.9.1"

    def __init__(self, *, execution_manager: Any, semantic_router: Any, provider_registry: Any, qualification_service: Any) -> None:
        self._execution_manager = execution_manager
        self._semantic_router = semantic_router
        self._provider_registry = provider_registry
        self._qualification_service = qualification_service
        self._last_result_code: str | None = None
        self._last_execution_id: str | None = None
        self._last_action_id: str | None = None
        self._last_state: str | None = None
        self._last_execution_at: str | None = None

    def record_execution(self, result: dict[str, Any]) -> None:
        self._last_result_code = str((result.get("result_code") or {}).get("code") or "") or None
        self._last_execution_id = str(result.get("execution_id") or "") or None
        self._last_action_id = str((result.get("request") or {}).get("action_id") or "") or None
        self._last_state = str(result.get("state") or "") or None
        self._last_execution_at = str(result.get("finished_at") or "") or None

    async def async_snapshot(self) -> dict[str, Any]:
        manager = await self._execution_manager.async_status()
        qualification = self._qualification_service.snapshot()
        provider_snapshot = self._provider_registry.diagnostics()
        providers = provider_snapshot.get("providers", [])

        invalid: list[str | None] = []
        unavailable: list[str | None] = []
        unhealthy: list[str | None] = []
        for item in providers:
            metadata = item.get("metadata") or {}
            runtime = item.get("runtime") or {}
            contract = item.get("contract") or {}
            provider_id = metadata.get("provider_id")
            if not contract.get("valid", False): invalid.append(provider_id)
            if not runtime.get("available", False): unavailable.append(provider_id)
            if not runtime.get("healthy", False): unhealthy.append(provider_id)

        store = qualification.get("store") or {}
        store_healthy = bool(store.get("loaded")) and store.get("load_error") is None and store.get("write_error") is None

        manager_summary = manager.get("summary") or {}
        all_semantically_ready = bool(manager_summary.get("all_semantically_ready", False))
        enabled_count = int(manager_summary.get("real_execution_enabled", 0) or 0)
        executable_now = int(manager_summary.get("executable_now", 0) or 0)
        manager_healthy = all_semantically_ready and enabled_count > 0 and executable_now == enabled_count
        providers_healthy = not (invalid or unavailable or unhealthy)
        overall_healthy = manager_healthy and providers_healthy and store_healthy

        warnings: list[str] = []
        errors: list[str] = []
        if invalid: errors.append("One or more providers fail the provider contract.")
        if unavailable: warnings.append("One or more providers are unavailable.")
        if unhealthy: warnings.append("One or more providers are unhealthy.")
        if not store_healthy: errors.append("Execution qualification store is not healthy.")
        if not all_semantically_ready:
            warnings.append("Not all declared semantic actions are currently provider-ready.")
        if enabled_count <= 0:
            errors.append("No canonical real-execution action is enabled.")
        elif executable_now != enabled_count:
            warnings.append("Not all real-execution-enabled actions are currently executable.")

        q_summary = qualification.get("summary") or {}
        return {
            "api_version": self.API_VERSION,
            "diagnostics_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "healthy" if overall_healthy else "degraded",
            "healthy": overall_healthy,
            "summary": {
                "declared_actions": manager_summary.get("declared_actions", manager_summary.get("actions", 0)),
                "semantically_ready": manager_summary.get("semantically_ready", manager_summary.get("ready", 0)),
                "semantic_not_ready": manager_summary.get("semantic_not_ready", manager_summary.get("not_ready", 0)),
                "real_execution_enabled": enabled_count,
                "executable_now": executable_now,
                "all_semantically_ready": all_semantically_ready,
                "all_enabled_executable": manager_summary.get("all_enabled_executable", False),
                # Compatibility aliases for existing diagnostics consumers.
                "actions": manager_summary.get("actions", 0),
                "ready": manager_summary.get("ready", 0),
                "not_ready": manager_summary.get("not_ready", 0),
                "all_ready": manager_summary.get("all_ready", False),
                "providers": len(providers),
                "provider_contract_invalid": len(invalid),
                "provider_unavailable": len(unavailable),
                "provider_unhealthy": len(unhealthy),
                "qualification_actions": q_summary.get("actions", 0),
                "qualification_evidence": q_summary.get("evidence", 0),
                "qualification_pass_count": q_summary.get("pass_count", 0),
                "qualification_store_healthy": store_healthy,
            },
            "execution_manager": {
                "manager_version": manager.get("manager_version"),
                "execution_enabled": manager.get("execution_enabled"),
                "read_only": manager.get("read_only"),
                "readiness_semantics": manager.get("readiness_semantics"),
                "summary": manager_summary,
                "supported_actions": manager.get("supported_actions", []),
            },
            "semantic_router": {"version": getattr(self._semantic_router, "VERSION", None), "healthy": True},
            "providers": {
                "healthy": providers_healthy,
                "invalid": [x for x in invalid if x],
                "unavailable": [x for x in unavailable if x],
                "unhealthy": [x for x in unhealthy if x],
            },
            "qualification": {
                "automatic_collection_enabled": qualification.get("automatic_collection_enabled"),
                "persistence_enabled": qualification.get("persistence_enabled"),
                "summary": q_summary,
                "store": {
                    "path": store.get("path"), "loaded": store.get("loaded"),
                    "load_error": store.get("load_error"), "write_error": store.get("write_error"),
                    "last_write_at": store.get("last_write_at"), "count": store.get("count"),
                    "pass_count": store.get("pass_count"), "healthy": store_healthy,
                },
            },
            "last_execution": {
                "execution_id": self._last_execution_id,
                "action_id": self._last_action_id,
                "state": self._last_state,
                "result_code": self._last_result_code,
                "finished_at": self._last_execution_at,
            },
            "warnings": warnings,
            "errors": errors,
        }
