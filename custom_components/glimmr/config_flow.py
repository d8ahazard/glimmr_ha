"""Config flow the Glimmr integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from glimmr import Glimmr
from glimmr.exceptions import GlimmrConnectionError, GlimmrError
from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import DOMAIN, DEFAULT_NAME, LOGGER

VERSION = 1
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WiZ Light."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        return await self._handle_config_flow(user_input)

    async def async_step_zeroconf(
        self, discovery_info: DiscoveryInfoType
    ) -> FlowResult:
        """Handle zeroconf discovery."""

        LOGGER.debug("Disco Info: ", discovery_info["hostname"])
        host = discovery_info["hostname"].rstrip(".")
        name = host.rsplit(".")[0]

        self.context.update(
            {
                CONF_HOST: discovery_info["host"],
                CONF_NAME: name,
                "title_placeholders": {"name": name},
            }
        )

        # Prepare configuration flow
        return await self._handle_config_flow(discovery_info, True)

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by zeroconf."""
        return await self._handle_config_flow(user_input)

    async def async_step_import(self, import_config):
        """Import from config."""
        return await self.async_step_user(user_input=import_config)

    def _show_setup_form(self, errors: dict | None = None) -> FlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors or {},
        )

    def _show_confirm_dialog(self, errors: dict | None = None) -> FlowResult:
        """Show the confirm dialog to the user."""
        name = self.context.get(CONF_NAME)
        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": name},
            errors=errors or {},
        )

    async def _handle_config_flow(
        self, user_input: dict[str, Any] | None = None, prepare: bool = False
    ) -> FlowResult:
        """Config flow handler for WLED."""
        errors = {}
        source = self.context.get("source")

        # Request user input, unless we are preparing discovery flow
        if user_input is None and not prepare:
            if source == SOURCE_ZEROCONF:
                return self._show_confirm_dialog()
            return self._show_setup_form()
        if user_input is not None:
            if source == SOURCE_ZEROCONF:
                user_input[CONF_HOST] = self.context.get(CONF_HOST)
            try:
                LOGGER.debug("Creating glimmr: " + user_input[CONF_HOST])
                device = Glimmr(user_input[CONF_HOST])
                await device.update()
                LOGGER.debug("Updated...")
                await self.async_set_unique_id(device.system_data.device_name)
                LOGGER.debug("Updated uId: " + device.system_data.device_name)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            except GlimmrConnectionError:
                errors["base"] = "bulb_time_out"
            except ConnectionRefusedError:
                errors["base"] = "cannot_connect"
            except GlimmrError:
                errors["base"] = "no_glimmr_light"
            except AbortFlow:
                return self.async_abort(reason="single_instance_allowed")
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            LOGGER.debug("Showform?")
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
