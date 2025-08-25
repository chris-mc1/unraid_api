"""Config flow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from aiohttp import ClientConnectionError, ClientConnectorSSLError
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)
from homeassistant.helpers.selector import BooleanSelector
from homeassistant.helpers.typing import UNDEFINED, UndefinedType

from . import UnraidConfigEntry
from .api import UnraidApiClient, UnraidGraphQLError
from .const import CONF_DRIVES, CONF_SHARES, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult

    from . import UnraidConfigEntry

_LOGGER = logging.getLogger(__name__)

USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_VERIFY_SSL, default=True): bool,
    }
)
REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DRIVES, default=True): BooleanSelector(),
        vol.Required(CONF_SHARES, default=True): BooleanSelector(),
    }
)


class UnraidConfigFlow(ConfigFlow, domain=DOMAIN):
    """Unraid Config flow."""

    def __init__(self) -> None:
        super().__init__()
        self.errors = {}
        self.data = {}
        self.description_placeholders = {}
        self.title = ""
        self.reauth_entry: UnraidConfigEntry = None

    async def validate_config(self) -> None:
        api_client = UnraidApiClient(
            host=self.data[CONF_HOST],
            api_key=self.data[CONF_API_KEY],
            session=async_get_clientsession(self.hass, self.data[CONF_VERIFY_SSL]),
        )
        try:
            response = await api_client.query_server_info()
            self.title = response.server.name
        except ClientConnectorSSLError:
            self.errors = {"base": "ssl_error"}
        except (ClientConnectionError, TimeoutError):
            self.errors = {"base": "cannot_connect"}
        except UnraidGraphQLError as exc:
            self.errors = {"base": "error_response"}
            self.description_placeholders["error_msg"] = exc.args[0]

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.data[CONF_HOST] = user_input[CONF_HOST].rstrip("/")
            self.data[CONF_API_KEY] = user_input[CONF_API_KEY]
            self.data[CONF_VERIFY_SSL] = user_input[CONF_VERIFY_SSL]
            await self.validate_config()
            if not self.errors:
                return await self.async_step_options()
        schema = self.add_suggested_values_to_schema(USER_DATA_SCHEMA, user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=self.errors,
            description_placeholders=self.description_placeholders,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return await self.async_step_create_entry(self.data, user_input)
        return self.async_show_form(
            step_id="options",
            data_schema=OPTIONS_SCHEMA,
            errors=self.errors,
            description_placeholders=self.description_placeholders,
        )

    async def async_step_reauth(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Reauth flow initialized."""
        self.reauth_entry = self._get_reauth_entry()
        self.data = dict(self.reauth_entry.data)
        return await self.async_step_reauth_key()

    async def async_step_reauth_key(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self.data[CONF_API_KEY] = user_input[CONF_API_KEY]
            await self.validate_config()
            if not self.errors:
                return await self.async_step_create_entry(self.data)

        schema = self.add_suggested_values_to_schema(REAUTH_DATA_SCHEMA, self.data)
        return self.async_show_form(
            step_id="reauth_key",
            data_schema=schema,
            errors=self.errors,
            description_placeholders=self.description_placeholders,
        )

    async def async_step_create_entry(
        self, data: dict | UndefinedType = UNDEFINED, options: dict | UndefinedType = UNDEFINED
    ) -> ConfigFlowResult:
        """Create an config entry or update existing entry for reauth."""
        if self.reauth_entry:
            return self.async_update_reload_and_abort(
                self.reauth_entry,
                data_updates=data,
                options=options,
            )
        return self.async_create_entry(title=self.title, data=data, options=options)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self.reauth_entry = self._get_reconfigure_entry()
        if user_input is not None:
            return await self.async_step_create_entry(options=user_input)
        schema = self.add_suggested_values_to_schema(
            OPTIONS_SCHEMA,
            self.reauth_entry.options,
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
        )
