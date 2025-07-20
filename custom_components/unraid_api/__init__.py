"""The Unraid Homeassistant integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)
from homeassistant.helpers.entity import DeviceInfo

from .api import UnraidApiClient
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
    api_client = UnraidApiClient(
        host=config_entry.data[CONF_HOST],
        api_key=config_entry.data[CONF_API_KEY],
        session=async_get_clientsession(hass, config_entry.data[CONF_VERIFY_SSL]),
    )
    server_info = await api_client.query()
    device_info = DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        sw_version=server_info.info.versions.unraid,
        name=server_info.server.name,
        configuration_url=server_info.server.localurl,
    )
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
