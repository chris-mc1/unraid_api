"""Config flow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from aiohttp import (
    ClientConnectionError,
    ClientConnectorSSLError,
    ContentTypeError,
    InvalidUrlClientError,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
)
from homeassistant.helpers.typing import UNDEFINED, UndefinedType

from . import UnraidConfigEntry
from .api import IncompatibleApiError, UnraidAuthError, UnraidGraphQLError, get_api_client
from .const import (
    CONF_DOCKER,
    CONF_DRIVES,
    CONF_PORT,
    CONF_POLL_INTERVAL_DISKS,
    CONF_POLL_INTERVAL_DOCKER,
    CONF_POLL_INTERVAL_METRICS,
    CONF_POLL_INTERVAL_SHARES,
    CONF_POLL_INTERVAL_UPS,
    CONF_PROTOCOL,
    CONF_SHARES,
    DEFAULT_POLL_INTERVAL_DISKS,
    DEFAULT_POLL_INTERVAL_DOCKER,
    DEFAULT_POLL_INTERVAL_METRICS,
    DEFAULT_POLL_INTERVAL_SHARES,
    DEFAULT_POLL_INTERVAL_UPS,
    DOMAIN,
    POLL_INTERVAL_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


def build_url_from_components(host: str, protocol: str, port: int | str | float | None = None) -> str:
    """
    Build a URL from host, protocol, and optional port components.
    
    Handles cases where the host field might contain a full URL (e.g., "http://10.0.97.3:88")
    by extracting just the hostname/IP and port, then using the form's protocol and port values.
    
    Args:
        host: Hostname, IP address, or full URL (e.g., "10.0.97.2" or "http://10.0.97.3:88")
        protocol: Protocol scheme ("http" or "https")
        port: Optional port number (can be int, str, or float). If None, uses default ports (80 for HTTP, 443 for HTTPS)
        
    Returns:
        Full URL string (e.g., "http://10.0.97.2" or "https://10.0.97.3:88")
    """
    from yarl import URL
    
    host = host.strip().rstrip("/")
    
    # If host contains a URL (has ://), parse it to extract just the hostname/IP and port
    # This handles cases where users enter "http://10.0.97.3:88" in the host field
    if "://" in host:
        try:
            parsed = URL(host)
            # Extract just the hostname/IP (without port or scheme)
            extracted_host = parsed.host
            if not extracted_host:
                # If parsing didn't give us a host, fall back to manual extraction
                raise ValueError("No host found in URL")
            
            # Use the extracted hostname/IP (this should be just "10.0.97.3", no scheme, no port)
            host = extracted_host
            
            # If port wasn't provided in the form field, use the port from the URL if present
            if port is None or port == "":
                if parsed.port is not None:
                    port = parsed.port
                # If no port in URL, we'll use default later
        except (ValueError, TypeError):
            # If parsing fails, try to extract host manually
            # Remove scheme if present (e.g., "http://" or "https://")
            if "://" in host:
                # Split on :// and take everything after it
                host_without_scheme = host.split("://", 1)[1]
                # Remove any path (everything after /)
                host_without_scheme = host_without_scheme.split("/")[0]
                
                # Now extract hostname and port
                # Handle format: hostname:port or just hostname
                if ":" in host_without_scheme and not host_without_scheme.startswith("["):  # Not IPv6
                    parts = host_without_scheme.rsplit(":", 1)
                    if len(parts) == 2:
                        try:
                            # Check if the last part is a port number
                            potential_port = int(parts[1])
                            host = parts[0]
                            if port is None or port == "":
                                port = potential_port
                        except (ValueError, IndexError):
                            # Not a port, might be IPv6 or something else
                            host = host_without_scheme
                else:
                    # No port in the URL, just use the hostname
                    host = host_without_scheme
    
    # Determine port - use default if not specified
    if port is None or port == "":
        port = 443 if protocol == "https" else 80
    else:
        # Convert port to integer (handles float strings like "88.0" or actual floats)
        try:
            port = int(float(str(port)))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid port value: {port}. Port must be a number between 1 and 65535.")
        
        # Validate port range
        if not (1 <= port <= 65535):
            raise ValueError(f"Invalid port value: {port}. Port must be between 1 and 65535.")
    
    # Build URL - only include port if it's not the default port
    if (protocol == "http" and port == 80) or (protocol == "https" and port == 443):
        return f"{protocol}://{host}"
    return f"{protocol}://{host}:{port}"


REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)

# Create selector options for polling intervals
_POLL_INTERVAL_OPTIONS = [
    {"value": str(seconds), "label": label}
    for seconds, label in sorted(POLL_INTERVAL_OPTIONS.items())
]

_POLL_INTERVAL_SELECTOR = SelectSelector(
    SelectSelectorConfig(options=_POLL_INTERVAL_OPTIONS)
)

_PROTOCOL_OPTIONS = [
    {"value": "http", "label": "HTTP"},
    {"value": "https", "label": "HTTPS"},
]

_PROTOCOL_SELECTOR = SelectSelector(
    SelectSelectorConfig(options=_PROTOCOL_OPTIONS)
)

# Port selector - use TextSelector for a simple text input field
_PORT_SELECTOR = TextSelector()


def get_user_data_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    """
    Build the user data schema.
    Fields are in order: URL, Port, Protocol, Verify SSL certificate, API key.
    """
    # Build schema with fields in order: URL, Port, Protocol, Verify SSL, API key
    return vol.Schema(
        {
            vol.Required(CONF_HOST): TextSelector(),
            vol.Optional(CONF_PORT): _PORT_SELECTOR,
            vol.Required(CONF_PROTOCOL, default="http"): _PROTOCOL_SELECTOR,
            vol.Optional(CONF_VERIFY_SSL, default=True): BooleanSelector(),
            vol.Required(CONF_API_KEY): str,
        }
    )

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DRIVES, default=True): BooleanSelector(),
        vol.Required(CONF_SHARES, default=True): BooleanSelector(),
        vol.Required(CONF_DOCKER, default=True): BooleanSelector(),
        vol.Required(
            CONF_POLL_INTERVAL_METRICS, default=str(DEFAULT_POLL_INTERVAL_METRICS)
        ): _POLL_INTERVAL_SELECTOR,
        vol.Required(
            CONF_POLL_INTERVAL_DISKS, default=str(DEFAULT_POLL_INTERVAL_DISKS)
        ): _POLL_INTERVAL_SELECTOR,
        vol.Required(
            CONF_POLL_INTERVAL_SHARES, default=str(DEFAULT_POLL_INTERVAL_SHARES)
        ): _POLL_INTERVAL_SELECTOR,
        vol.Required(
            CONF_POLL_INTERVAL_DOCKER, default=str(DEFAULT_POLL_INTERVAL_DOCKER)
        ): _POLL_INTERVAL_SELECTOR,
        vol.Required(
            CONF_POLL_INTERVAL_UPS, default=str(DEFAULT_POLL_INTERVAL_UPS)
        ): _POLL_INTERVAL_SELECTOR,
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
        self.reauth_entry: UnraidConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,  # noqa: ARG004
    ) -> UnraidOptionsFlow:
        """Create the options flow."""
        return UnraidOptionsFlow()

    async def validate_config(self) -> None:
        # Build URL from components
        try:
            host_url = build_url_from_components(
                self.data[CONF_HOST],
                self.data.get(CONF_PROTOCOL, "http"),
                self.data.get(CONF_PORT),
            )
            _LOGGER.debug("Validating connection to: %s", host_url)
        except Exception as exc:
            _LOGGER.error("Error building URL: %s", exc)
            self.errors = {"base": "invalid_url"}
            self.description_placeholders = {"url": str(self.data.get(CONF_HOST, "")), "error": str(exc)}
            return
        
        try:
            api_client = await get_api_client(
                host_url,
                self.data[CONF_API_KEY],
                async_get_clientsession(self.hass, self.data[CONF_VERIFY_SSL]),
            )
            response = await api_client.query_server_info()
            self.title = response.name
            # Store the built URL for use in the config entry (for backward compatibility)
            self.data[CONF_HOST] = host_url
        except ClientConnectorSSLError:
            _LOGGER.exception("SSL error connecting to %s", host_url)
            self.errors = {"base": "ssl_error"}
        except (ClientConnectionError, TimeoutError, ContentTypeError) as exc:
            _LOGGER.exception("Connection error to %s: %s", host_url, exc)
            self.errors = {"base": "cannot_connect"}
            self.description_placeholders = {"url": host_url, "error": str(exc)}
        except UnraidAuthError:
            _LOGGER.exception("Auth failed for %s", host_url)
            self.errors = {"base": "auth_failed"}
        except UnraidGraphQLError as exc:
            _LOGGER.exception("GraphQL Error response from %s: %s", host_url, exc.response)
            self.errors = {"base": "error_response"}
            self.description_placeholders["error_msg"] = exc.args[0]
        except InvalidUrlClientError as exc:
            _LOGGER.error("Invalid URL client error for %s: %s", host_url, exc)
            self.errors = {"base": "invalid_url"}
            self.description_placeholders = {"url": host_url, "error": str(exc)}
        except IncompatibleApiError as exc:
            _LOGGER.exception("Incompatible API for %s, %s < %s", host_url, exc.version, exc.min_version)
            self.errors = {"base": "api_incompatible"}
            self.description_placeholders["min_version"] = exc.min_version
            self.description_placeholders["version"] = exc.version

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.data[CONF_HOST] = user_input[CONF_HOST].strip()
            self.data[CONF_PROTOCOL] = user_input.get(CONF_PROTOCOL, "http")
            self.data[CONF_PORT] = user_input.get(CONF_PORT)
            self.data[CONF_API_KEY] = user_input[CONF_API_KEY]
            # Get verify_ssl value (always shown, but only meaningful for HTTPS)
            self.data[CONF_VERIFY_SSL] = user_input.get(CONF_VERIFY_SSL, True)
            
            await self.validate_config()
            if not self.errors:
                return await self.async_step_options()
        
        # Build schema (SSL checkbox always shown)
        schema = get_user_data_schema(user_input)
        schema = self.add_suggested_values_to_schema(schema, user_input)
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


class UnraidOptionsFlow(OptionsFlowWithReload):
    """Unraid Options Flow."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the Unraid options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = self.add_suggested_values_to_schema(
            OPTIONS_SCHEMA,
            self.config_entry.options,
        )
        return self.async_show_form(step_id="init", data_schema=schema)
