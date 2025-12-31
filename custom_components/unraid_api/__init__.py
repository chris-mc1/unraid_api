"""The Unraid Homeassistant integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from awesomeversion import AwesomeVersion
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo

from .api import IncompatibleApiError, UnraidAuthError, UnraidGraphQLError, get_api_client
from .const import CONF_DOCKER, CONF_DRIVES, CONF_SHARES, DOMAIN, PLATFORMS
from .coordinator import (
    UnraidDataUpdateCoordinator,
    UnraidDisksCoordinator,
    UnraidDockerCoordinator,
    UnraidMetricsCoordinator,
    UnraidSharesCoordinator,
    UnraidUpsCoordinator,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass
class UnraidData:
    """Dataclass for runtime data."""

    metrics_coordinator: UnraidMetricsCoordinator
    disks_coordinator: UnraidDisksCoordinator | None
    shares_coordinator: UnraidSharesCoordinator | None
    docker_coordinator: UnraidDockerCoordinator | None
    ups_coordinator: UnraidUpsCoordinator | None
    device_info: DeviceInfo
    # Legacy coordinator for backward compatibility
    coordinator: UnraidDataUpdateCoordinator


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

    device_info = DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        sw_version=server_info.unraid_version,
        name=server_info.name,
        configuration_url=server_info.localurl,
    )

    # Create separate coordinators for each data type
    metrics_coordinator = UnraidMetricsCoordinator(hass, config_entry, api_client)
    await metrics_coordinator.async_config_entry_first_refresh()

    disks_coordinator = None
    if config_entry.options.get(CONF_DRIVES, True):
        disks_coordinator = UnraidDisksCoordinator(hass, config_entry, api_client)
        await disks_coordinator.async_config_entry_first_refresh()

    shares_coordinator = None
    if config_entry.options.get(CONF_SHARES, True):
        shares_coordinator = UnraidSharesCoordinator(hass, config_entry, api_client)
        await shares_coordinator.async_config_entry_first_refresh()

    docker_coordinator = None
    if config_entry.options.get(CONF_DOCKER, True):
        docker_coordinator = UnraidDockerCoordinator(hass, config_entry, api_client)
        await docker_coordinator.async_config_entry_first_refresh()

    ups_coordinator = None
    if api_client.version >= AwesomeVersion("4.26.0"):
        ups_coordinator = UnraidUpsCoordinator(hass, config_entry, api_client)
        await ups_coordinator.async_config_entry_first_refresh()

    # Legacy coordinator for backward compatibility
    coordinator = UnraidDataUpdateCoordinator(hass, config_entry, api_client)
    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = UnraidData(
        metrics_coordinator=metrics_coordinator,
        disks_coordinator=disks_coordinator,
        shares_coordinator=shares_coordinator,
        docker_coordinator=docker_coordinator,
        ups_coordinator=ups_coordinator,
        device_info=device_info,
        coordinator=coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Unload qBittorrent config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        del entry.runtime_data
    return unload_ok
