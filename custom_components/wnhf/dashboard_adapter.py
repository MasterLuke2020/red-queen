"""Home Assistant lifecycle adapter for the Red Queen managed dashboard.

This is the only RC12 module allowed to touch Home Assistant's Lovelace
persistence/runtime registration APIs.  The semantic model, entity binding and
renderer remain side-effect free.

The adapter deliberately does *not* edit ``.storage`` files itself and does not
instantiate a second ``DashboardsCollection``.  Home Assistant keeps the
collection used by the dashboard settings WebSocket private to the Lovelace
integration setup routine; creating a second collection would leave the live
collection stale.  Instead Red Queen owns one LovelaceStorage config directly,
registers its panel through the frontend API, and persists a small ownership
manifest through Home Assistant's Store helper.

The managed dashboard therefore behaves like an integration-owned panel:

* explicit create/update writes the rendered Lovelace config;
* startup only re-attaches an already-owned panel and never regenerates it;
* unload detaches the runtime panel but preserves the stored config/manifest;
* existing foreign panels or Lovelace dashboard paths are never overwritten.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from typing import Any

from homeassistant.components import frontend
from homeassistant.components.lovelace import dashboard as lovelace_dashboard
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .dashboard_renderer import (
    DEFAULT_DASHBOARD_URL_PATH,
    DashboardRenderResult,
)


_LOGGER = logging.getLogger(__name__)

DASHBOARD_ADAPTER_CONTRACT_VERSION = "1.0"
DASHBOARD_MANIFEST_STORAGE_VERSION = 1
DASHBOARD_MANIFEST_STORAGE_KEY = "wnhf.dashboard"
DASHBOARD_OWNER = "red_queen_dashboard_generator"
DASHBOARD_RUNTIME_KEY = "dashboard_adapter"
DEFAULT_DASHBOARD_ID = "red-queen"
DEFAULT_DASHBOARD_TITLE = "Red Queen"
DEFAULT_DASHBOARD_ICON = "mdi:chess-queen"


class DashboardAdapterError(Exception):
    """Raised when Red Queen cannot safely manage its dashboard."""


@dataclass(frozen=True, slots=True)
class DashboardLifecycleStatus:
    """Current ownership, runtime and freshness status of the dashboard."""

    state: str
    managed: bool
    attached: bool
    url_path: str
    config_sha256: str | None
    expected_sha256: str | None
    created_at: str | None
    updated_at: str | None
    message: str

    @property
    def current(self) -> bool:
        """Return whether the persisted dashboard matches the expected render."""
        return (
            self.managed
            and self.config_sha256 is not None
            and self.expected_sha256 is not None
            and self.config_sha256 == self.expected_sha256
        )

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-serializable lifecycle status."""
        return {
            "state": self.state,
            "managed": self.managed,
            "attached": self.attached,
            "url_path": self.url_path,
            "config_sha256": self.config_sha256,
            "expected_sha256": self.expected_sha256,
            "current": self.current,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class DashboardApplyResult:
    """Result of one explicit create/update operation."""

    action: str
    status: DashboardLifecycleStatus
    render_metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-serializable apply result."""
        return {
            "action": self.action,
            "status": self.status.as_dict(),
            "render_metadata": self.render_metadata,
        }


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _panel_config(
    *,
    dashboard_id: str,
    url_path: str,
    title: str,
    icon: str,
) -> dict[str, Any]:
    """Build the LovelaceStorage descriptor used by the frontend panel."""
    return {
        "id": dashboard_id,
        "url_path": url_path,
        "title": title,
        "icon": icon,
        "show_in_sidebar": True,
        "require_admin": False,
        "mode": MODE_STORAGE,
    }


def _lovelace_data(hass: HomeAssistant):
    """Return initialized Lovelace data or raise a controlled adapter error."""
    data = hass.data.get(LOVELACE_DATA)
    if data is None:
        raise DashboardAdapterError(
            "Home Assistant Lovelace is not initialized; Red Queen cannot "
            "attach its managed dashboard yet."
        )
    return data


class RedQueenDashboardAdapter:
    """Own, persist and attach exactly one Red Queen Lovelace dashboard."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._manifest_store = Store[dict[str, Any]](
            hass,
            DASHBOARD_MANIFEST_STORAGE_VERSION,
            DASHBOARD_MANIFEST_STORAGE_KEY,
        )
        self._attached_url_path: str | None = None
        self._storage: lovelace_dashboard.LovelaceStorage | None = None

    async def async_manifest(self) -> dict[str, Any] | None:
        """Load and validate the Red Queen dashboard ownership manifest."""
        raw = await self._manifest_store.async_load()
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise DashboardAdapterError("Red Queen dashboard manifest is invalid.")
        if (
            raw.get("owner") != DASHBOARD_OWNER
            or raw.get("adapter_contract_version")
            != DASHBOARD_ADAPTER_CONTRACT_VERSION
        ):
            raise DashboardAdapterError(
                "Dashboard manifest exists but is not owned by this Red Queen "
                "dashboard contract."
            )
        required = ("dashboard_id", "url_path", "title", "config_sha256")
        if any(not isinstance(raw.get(key), str) or not raw.get(key) for key in required):
            raise DashboardAdapterError(
                "Red Queen dashboard manifest is missing required identity fields."
            )
        return raw

    def _runtime_dashboard(self, url_path: str):
        data = _lovelace_data(self.hass)
        return data.dashboards.get(url_path)

    def _assert_path_available_for_create(self, url_path: str) -> None:
        """Refuse to take ownership of any existing foreign dashboard/panel."""
        runtime = self._runtime_dashboard(url_path)
        if runtime is not None:
            raise DashboardAdapterError(
                f"Dashboard path '{url_path}' is already registered in Lovelace."
            )
        if frontend.async_panel_exists(self.hass, url_path):
            raise DashboardAdapterError(
                f"Frontend panel path '{url_path}' already exists."
            )

    def _attach_storage(
        self,
        *,
        dashboard_id: str,
        url_path: str,
        title: str,
        icon: str,
        allow_existing_owned: bool,
    ) -> lovelace_dashboard.LovelaceStorage:
        """Attach the integration-owned LovelaceStorage object and panel."""
        lovelace_data = _lovelace_data(self.hass)
        existing = lovelace_data.dashboards.get(url_path)

        if existing is not None:
            if allow_existing_owned and existing is self._storage:
                return existing
            raise DashboardAdapterError(
                f"Lovelace dashboard path '{url_path}' is already in use."
            )

        if frontend.async_panel_exists(self.hass, url_path):
            raise DashboardAdapterError(
                f"Frontend panel path '{url_path}' is already in use."
            )

        descriptor = _panel_config(
            dashboard_id=dashboard_id,
            url_path=url_path,
            title=title,
            icon=icon,
        )
        storage = lovelace_dashboard.LovelaceStorage(self.hass, descriptor)
        lovelace_data.dashboards[url_path] = storage

        try:
            frontend.async_register_built_in_panel(
                self.hass,
                "lovelace",
                frontend_url_path=url_path,
                require_admin=False,
                show_in_sidebar=True,
                sidebar_title=title,
                sidebar_icon=icon,
                config={"mode": MODE_STORAGE},
            )
        except ValueError as err:
            lovelace_data.dashboards.pop(url_path, None)
            raise DashboardAdapterError(
                f"Could not register Red Queen dashboard panel '{url_path}': {err}"
            ) from err

        self._storage = storage
        self._attached_url_path = url_path
        return storage

    async def async_restore(self) -> DashboardLifecycleStatus:
        """Re-attach a previously created dashboard without regenerating it."""
        if self.hass.config.recovery_mode:
            return DashboardLifecycleStatus(
                state="recovery_mode",
                managed=False,
                attached=False,
                url_path=DEFAULT_DASHBOARD_URL_PATH,
                config_sha256=None,
                expected_sha256=None,
                created_at=None,
                updated_at=None,
                message="Dashboard restore is disabled in Home Assistant recovery mode.",
            )

        manifest = await self.async_manifest()
        if manifest is None:
            return DashboardLifecycleStatus(
                state="not_created",
                managed=False,
                attached=False,
                url_path=DEFAULT_DASHBOARD_URL_PATH,
                config_sha256=None,
                expected_sha256=None,
                created_at=None,
                updated_at=None,
                message="Red Queen dashboard has not been created yet.",
            )

        url_path = manifest["url_path"]
        if self._attached_url_path == url_path and self._storage is not None:
            return await self.async_status()

        self._attach_storage(
            dashboard_id=manifest["dashboard_id"],
            url_path=url_path,
            title=manifest["title"],
            icon=str(manifest.get("icon") or DEFAULT_DASHBOARD_ICON),
            allow_existing_owned=False,
        )
        return await self.async_status()

    async def async_apply(
        self,
        rendered: DashboardRenderResult,
        *,
        dashboard_id: str = DEFAULT_DASHBOARD_ID,
        url_path: str = DEFAULT_DASHBOARD_URL_PATH,
        title: str = DEFAULT_DASHBOARD_TITLE,
        icon: str = DEFAULT_DASHBOARD_ICON,
        source_registry_sha256: str | None = None,
    ) -> DashboardApplyResult:
        """Explicitly create or update the managed Red Queen dashboard."""
        if self.hass.config.recovery_mode:
            raise DashboardAdapterError(
                "Dashboard writes are disabled in Home Assistant recovery mode."
            )

        dashboard_id = dashboard_id.strip()
        url_path = url_path.strip("/")
        title = title.strip()
        icon = icon.strip()
        if not dashboard_id or not url_path or not title or not icon:
            raise DashboardAdapterError(
                "Dashboard id, URL path, title and icon must not be empty."
            )

        manifest = await self.async_manifest()
        created_at: str
        action: str

        if manifest is None:
            self._assert_path_available_for_create(url_path)
            created_at = _utc_now_iso()
            action = "create"
            storage = self._attach_storage(
                dashboard_id=dashboard_id,
                url_path=url_path,
                title=title,
                icon=icon,
                allow_existing_owned=False,
            )
        else:
            if manifest["dashboard_id"] != dashboard_id:
                raise DashboardAdapterError(
                    "Managed dashboard id differs from the requested dashboard id."
                )
            if manifest["url_path"] != url_path:
                raise DashboardAdapterError(
                    "Managed dashboard URL path is immutable in RC12."
                )
            created_at = str(manifest.get("created_at") or _utc_now_iso())
            action = "update"

            if self._storage is None or self._attached_url_path != url_path:
                storage = self._attach_storage(
                    dashboard_id=dashboard_id,
                    url_path=url_path,
                    title=title,
                    icon=icon,
                    allow_existing_owned=False,
                )
            else:
                storage = self._storage
                # Keep sidebar metadata current without replacing another panel.
                frontend.async_register_built_in_panel(
                    self.hass,
                    "lovelace",
                    frontend_url_path=url_path,
                    require_admin=False,
                    show_in_sidebar=True,
                    sidebar_title=title,
                    sidebar_icon=icon,
                    config={"mode": MODE_STORAGE},
                    update=True,
                )

        # LovelaceStorage uses Home Assistant's Store helper internally.  No
        # Red Queen code edits .storage files directly.
        await storage.async_save(rendered.config)

        updated_at = _utc_now_iso()
        manifest_document: dict[str, Any] = {
            "owner": DASHBOARD_OWNER,
            "adapter_contract_version": DASHBOARD_ADAPTER_CONTRACT_VERSION,
            "dashboard_id": dashboard_id,
            "url_path": url_path,
            "title": title,
            "icon": icon,
            "show_in_sidebar": True,
            "require_admin": False,
            "created_at": created_at,
            "updated_at": updated_at,
            "config_sha256": rendered.metadata.config_sha256,
            "source_registry_sha256": source_registry_sha256,
            "render_metadata": rendered.metadata.as_dict(),
        }
        await self._manifest_store.async_save(manifest_document)

        status = await self.async_status(
            expected_render=rendered,
            expected_source_registry_sha256=source_registry_sha256,
        )
        return DashboardApplyResult(
            action=action,
            status=status,
            render_metadata=rendered.metadata.as_dict(),
        )

    async def async_status(
        self,
        *,
        expected_render: DashboardRenderResult | None = None,
        expected_source_registry_sha256: str | None = None,
    ) -> DashboardLifecycleStatus:
        """Return ownership, attachment and render/source freshness status."""
        expected_sha = (
            expected_render.metadata.config_sha256
            if expected_render is not None
            else None
        )
        expected_source_sha = (
            expected_source_registry_sha256.strip()
            if isinstance(expected_source_registry_sha256, str)
            and expected_source_registry_sha256.strip()
            else None
        )
        manifest = await self.async_manifest()
        if manifest is None:
            return DashboardLifecycleStatus(
                state="not_created",
                managed=False,
                attached=False,
                url_path=DEFAULT_DASHBOARD_URL_PATH,
                config_sha256=None,
                expected_sha256=expected_sha,
                created_at=None,
                updated_at=None,
                message="Red Queen dashboard has not been created yet.",
            )

        url_path = manifest["url_path"]
        runtime = self._runtime_dashboard(url_path)
        panel_exists = frontend.async_panel_exists(self.hass, url_path)
        attached = (
            self._attached_url_path == url_path
            and self._storage is not None
            and runtime is self._storage
            and panel_exists
        )

        current_sha = str(manifest.get("config_sha256") or "") or None
        current_source_sha = (
            str(manifest.get("source_registry_sha256") or "") or None
        )
        render_outdated = expected_sha is not None and current_sha != expected_sha
        source_outdated = (
            expected_source_sha is not None
            and current_source_sha != expected_source_sha
        )
        if render_outdated or source_outdated:
            state = "outdated"
            if render_outdated and source_outdated:
                message = (
                    "Dashboard render and registry-source metadata are outdated."
                )
            elif render_outdated:
                message = "Dashboard exists but does not match the current render."
            else:
                message = (
                    "Dashboard registry-source metadata does not match the "
                    "current Red Queen registry."
                )
        elif attached:
            state = "ready"
            message = "Red Queen dashboard is attached and ready."
        else:
            state = "detached"
            message = "Dashboard is owned by Red Queen but not attached."

        return DashboardLifecycleStatus(
            state=state,
            managed=True,
            attached=attached,
            url_path=url_path,
            config_sha256=current_sha,
            expected_sha256=expected_sha,
            created_at=(
                str(manifest.get("created_at"))
                if manifest.get("created_at") is not None
                else None
            ),
            updated_at=(
                str(manifest.get("updated_at"))
                if manifest.get("updated_at") is not None
                else None
            ),
            message=message,
        )

    async def async_detach(self) -> None:
        """Detach runtime registration while preserving managed persistence."""
        url_path = self._attached_url_path
        storage = self._storage
        if url_path is None or storage is None:
            return

        try:
            lovelace_data = _lovelace_data(self.hass)
        except DashboardAdapterError:
            lovelace_data = None

        if (
            lovelace_data is not None
            and lovelace_data.dashboards.get(url_path) is storage
        ):
            lovelace_data.dashboards.pop(url_path, None)

        if frontend.async_panel_exists(self.hass, url_path):
            frontend.async_remove_panel(
                self.hass,
                url_path,
                warn_if_unknown=False,
            )

        self._storage = None
        self._attached_url_path = None


async def async_setup_dashboard_adapter(hass: HomeAssistant) -> RedQueenDashboardAdapter:
    """Create the runtime adapter and restore an already-owned dashboard."""
    adapter = RedQueenDashboardAdapter(hass)
    hass.data.setdefault(DOMAIN, {})[DASHBOARD_RUNTIME_KEY] = adapter
    try:
        status = await adapter.async_restore()
    except DashboardAdapterError as err:
        _LOGGER.warning("Red Queen dashboard restore skipped: %s", err)
    else:
        if status.managed:
            _LOGGER.info(
                "Red Queen dashboard restore: %s | path=%s | attached=%s",
                status.state,
                status.url_path,
                status.attached,
            )
    return adapter


async def async_unload_dashboard_adapter(hass: HomeAssistant) -> None:
    """Detach the runtime panel without deleting the managed dashboard data."""
    domain_data = hass.data.get(DOMAIN, {})
    adapter = domain_data.pop(DASHBOARD_RUNTIME_KEY, None)
    if isinstance(adapter, RedQueenDashboardAdapter):
        await adapter.async_detach()
