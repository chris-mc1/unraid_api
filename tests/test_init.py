"""Tests for integration init."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from aiohttp import ClientConnectionError, ClientConnectorSSLError
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.api import IncompatibleApiError, UnraidApiClient, UnraidAuthError
from homeassistant.config_entries import ConfigEntryState

from . import add_config_entry, setup_config_entry
from .api_states import API_STATES, ApiState
from .const import DEFAULT_HOST

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .conftest import MockApiClient


@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_load_unload_entry(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test setup and unload config entry."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    entry = await setup_config_entry(hass)

    assert entry.state is ConfigEntryState.LOADED
    mock_api_client.assert_called_once_with(host=DEFAULT_HOST, api_key="test_key", session=ANY)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_load_failure(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test setup and unload failure."""
    mock_call_api = AsyncMock()
    monkeypatch.setattr(UnraidApiClient, "call_api", mock_call_api, raising=True)
    entry = add_config_entry(hass)

    mock_call_api.side_effect = ClientConnectorSSLError(MagicMock(), MagicMock())
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)
    mock_call_api.reset_mock()

    mock_call_api.side_effect = TimeoutError()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    await hass.config_entries.async_unload(entry.entry_id)
    mock_call_api.reset_mock()

    mock_call_api.side_effect = ClientConnectionError()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    await hass.config_entries.async_unload(entry.entry_id)
    mock_call_api.reset_mock()


async def test_load_failure_2(
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test setup and unload failure."""
    mock_api_client.side_effect = UnraidAuthError(response={"errors": []})
    entry = add_config_entry(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)

    mock_api_client.side_effect = UnraidAuthError(response={"errors": []})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)

    mock_api_client.side_effect = IncompatibleApiError(
        AwesomeVersion("4.10.0"), AwesomeVersion("4.20.0")
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)
