"""Tests for integration init."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from aiohttp import ClientConnectionError, ClientSSLError
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.api import UnraidApiClient
from custom_components.unraid_api.const import (
    CONF_DOCKER_MODE,
    CONF_DRIVES,
    CONF_SHARES,
    DOCKER_MODE_OFF,
    DOMAIN,
)
from custom_components.unraid_api.exceptions import GraphQLUnauthorizedError, IncompatibleApiError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from pytest_homeassistant_custom_component.common import MockConfigEntry

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

    mock_call_api.side_effect = ClientSSLError(MagicMock(), MagicMock())
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
    mock_api_client.side_effect = GraphQLUnauthorizedError({"message": "API key validation failed"})
    entry = add_config_entry(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)

    mock_api_client.side_effect = GraphQLUnauthorizedError({"message": "API key validation failed"})
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


async def test_migrate_entry(hass: HomeAssistant) -> None:
    """Test Config entry migration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: DEFAULT_HOST,
            CONF_API_KEY: "test_key",
            CONF_VERIFY_SSL: False,
        },
        options={CONF_SHARES: True, CONF_DRIVES: True},
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.minor_version == 2
    assert entry.options == {
        CONF_SHARES: True,
        CONF_DRIVES: True,
        CONF_DOCKER_MODE: DOCKER_MODE_OFF,
    }
