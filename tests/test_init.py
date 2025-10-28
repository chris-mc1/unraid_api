"""Tests for integration init."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.api import (
    IncompatibleApiError,
    UnraidAuthError,
    UnraidGraphQLError,
)
from custom_components.unraid_api.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from . import setup_config_entry
from .const import MOCK_CONFIG_DATA, MOCK_OPTION_DATA

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_load_unload_entry(
    hass: HomeAssistant,
    mock_get_api_client: AsyncMock,
) -> None:
    """Test setup and unload config entry."""
    entry = await setup_config_entry(hass, data=MOCK_CONFIG_DATA, options=MOCK_OPTION_DATA)

    assert entry.state is ConfigEntryState.LOADED

    mock_get_api_client.assert_called_once_with(
        host=MOCK_CONFIG_DATA[CONF_HOST],
        api_key=MOCK_CONFIG_DATA[CONF_API_KEY],
        session=ANY,
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_load_failure(
    hass: HomeAssistant,
    mock_get_api_client: AsyncMock,
) -> None:
    """Test setup and unload failure."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA, options=MOCK_OPTION_DATA)

    entry.add_to_hass(hass)

    mock_get_api_client.side_effect = ClientConnectorSSLError(MagicMock(), MagicMock())
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)
    mock_get_api_client.reset_mock()

    mock_get_api_client.side_effect = TimeoutError()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    await hass.config_entries.async_unload(entry.entry_id)
    mock_get_api_client.reset_mock()

    mock_get_api_client.side_effect = ClientConnectionError()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    await hass.config_entries.async_unload(entry.entry_id)
    mock_get_api_client.reset_mock()

    mock_get_api_client.side_effect = UnraidAuthError(
        {"errors": [{"message": "No user session found"}]}
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)
    mock_get_api_client.reset_mock()

    mock_get_api_client.side_effect = UnraidGraphQLError(
        {"errors": [{"message": "No user session found"}]}
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)
    mock_get_api_client.reset_mock()

    mock_get_api_client.side_effect = IncompatibleApiError(
        min_version=AwesomeVersion("1.0.0"), version=AwesomeVersion("0.0.1")
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)
    mock_get_api_client.reset_mock()
