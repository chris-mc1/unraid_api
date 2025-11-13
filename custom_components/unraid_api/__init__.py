"""The Unraid Homeassistant integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo

from .api import IncompatibleApiError, UnraidAuthError, UnraidGraphQLError, get_api_client
from .const import DOMAIN, PLATFORMS
from .coordinator import UnraidDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass
class UnraidData:
    """Dataclass for runtime data."""

    coordinator: UnraidDataUpdateCoordinator
    device_info: DeviceInfo


type UnraidConfigEntry = ConfigEntry[UnraidData]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: UnraidConfigEntry,
) -> bool:
    """Set up this integration using config entry."""
    _LOGGER.debug("Setting up %s", config_entry.data[CONF_HOST])
    try:
        api_client = await get_api_client(
            host=config_entry.data[CONF_HOST],
            api_key=config_entry.data[CONF_API_KEY],
            session=async_get_clientsession(hass, config_entry.data[CONF_VERIFY_SSL]),
        )

        server_info = await api_client.query_server_info()
    except ClientConnectorSSLError as exc:
        _LOGGER.debug("Init: SSL error: %s", str(exc))
        raise ConfigEntryError(translation_domain=DOMAIN, translation_key="ssl_error") from exc
    except (ClientConnectionError, TimeoutError) as exc:
        _LOGGER.debug("Init: Connection error: %s", str(exc))
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="cannot_connect"
        ) from exc
    except UnraidAuthError as exc:
        _LOGGER.debug("Init: Auth failed")
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="auth_failed",
            translation_placeholders={"error_msg": exc.args[0]},
        ) from exc
    except UnraidGraphQLError as exc:
        _LOGGER.debug("Init: GraphQL Error response: %s", exc.response)
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="error_response",
            translation_placeholders={"error_msg": exc.args[0]},
        ) from exc
    except IncompatibleApiError as exc:
        _LOGGER.debug("Init: Incompatible API, %s < %s", exc.version, exc.min_version)
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="api_incompatible",
            translation_placeholders={"min_version": exc.min_version, "version": exc.version},
        ) from exc

    # Log the localurl value for debugging
    _LOGGER.debug(
        "Server info: name=%s, version=%s, localurl='%s'",
        server_info.name,
        server_info.unraid_version,
        server_info.localurl,
    )

    # Only include configuration_url if localurl is valid
    device_info_kwargs = {
        "identifiers": {(DOMAIN, config_entry.entry_id)},
        "sw_version": server_info.unraid_version,
        "name": server_info.name,
    }
    if server_info.localurl and "://" in server_info.localurl:
        _LOGGER.debug("Adding configuration_url: %s", server_info.localurl)
        device_info_kwargs["configuration_url"] = server_info.localurl
    else:
        _LOGGER.warning(
            "Invalid or empty localurl from Unraid API: '%s'. Device will not have configuration_url",
            server_info.localurl,
        )

    device_info = DeviceInfo(**device_info_kwargs)
    coordinator = UnraidDataUpdateCoordinator(hass, config_entry, api_client)
    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = UnraidData(
        coordinator,
        device_info,
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Unload qBittorrent config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        del entry.runtime_data
    return unload_ok
