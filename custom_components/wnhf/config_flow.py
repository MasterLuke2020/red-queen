"""Config flow for Red Queen."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, PRODUCT_NAME


class WNHFConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the single Red Queen config entry."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle manual setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title=PRODUCT_NAME,
                data={},
            )

        return self.async_show_form(step_id="user")

    async def async_step_import(
        self,
        import_data: dict[str, Any],
    ) -> FlowResult:
        """Import the legacy configuration.yaml setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title=PRODUCT_NAME,
            data={},
        )
