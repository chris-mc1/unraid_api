"""The Unraid Homeassistant integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiohttp import ClientConnectionError, ClientSSLError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo

from .api import get_api_client
from .const import CONF_DOCKER_MODE, DOCKER_MODE_OFF, DOMAIN, PLATFORMS
from .coordinator import Container, UnraidDataUpdateCoordinator
from .exceptions import (
    GraphQLError,
    GraphQLMultiError,
    GraphQLUnauthorizedError,
    IncompatibleApiError,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceEntry


_LOGGER = logging.getLogger(__name__)


@dataclass
class UnraidData:
    """Dataclass for runtime data."""

    coordinator: UnraidDataUpdateCoordinator
    device_info: DeviceInfo
    containers: dict[str, Container]


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
    except ClientSSLError as exc:
        _LOGGER.debug("Init: SSL error: %s", str(exc))
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="ssl_error",
            translation_placeholders={"error": str(exc)},
        ) from exc
    except (ClientConnectionError, TimeoutError) as exc:
        _LOGGER.debug("Init: Connection error: %s", str(exc))
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"error": str(exc)},
        ) from exc
    except GraphQLUnauthorizedError as exc:
        _LOGGER.debug("Init: Auth failed")
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="auth_failed",
            translation_placeholders={"error_msg": str(exc)},
        ) from exc
    except (GraphQLError, GraphQLMultiError) as exc:
        _LOGGER.debug("Init: GraphQL Error response: %s", str(exc))
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="error_response",
            translation_placeholders={"error_msg": str(exc)},
        ) from exc
    except IncompatibleApiError as exc:
        _LOGGER.debug("Init: Incompatible API, %s < %s", exc.version, exc.min_version)
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="api_incompatible",
            translation_placeholders={"min_version": exc.min_version, "version": exc.version},
        ) from exc

    device_info = DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        sw_version=server_info.unraid_version,
        name=server_info.name,
        configuration_url=server_info.localurl,
    )
    coordinator = UnraidDataUpdateCoordinator(hass, config_entry, api_client)
    config_entry.runtime_data = UnraidData(coordinator, device_info, containers={})
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Unload qBittorrent config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.coordinator.api_client.stop_websocket()
        del entry.runtime_data
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: UnraidConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 1:
        return False

    if config_entry.version == 1:
        new_options = config_entry.options.copy()
        if config_entry.minor_version < 2:  # noqa: PLR2004
            new_options[CONF_DOCKER_MODE] = DOCKER_MODE_OFF

        hass.config_entries.async_update_entry(
            config_entry, data=config_entry.data, options=new_options, minor_version=2, version=1
        )

    _LOGGER.debug(
        "Migration to configuration version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True
