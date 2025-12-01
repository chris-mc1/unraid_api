"""Tests for integration init."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientConnectionError, ClientConnectorSSLError
from custom_components.unraid_api.api import UnraidApiClient
from homeassistant.config_entries import ConfigEntryState

from . import add_config_entry, setup_config_entry
from .graphql_responses import (
    API_RESPONSES,
    API_RESPONSES_LATEST,
    GraphqlResponses,
    GraphqlResponses410,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant

    from tests.conftest import GraphqlServerMocker


@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_load_unload_entry(
    api_responses: GraphqlResponses,
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test setup and unload config entry."""
    mocker = await mock_graphql_server(api_responses)
    entry = await setup_config_entry(hass, mocker, expect_success=False)

    assert entry.state is ConfigEntryState.LOADED

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
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test setup and unload failure."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    mocker.responses.is_unauthenticated = True
    entry = add_config_entry(hass, mocker)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)

    mocker.responses.all_error = True
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)

    mocker.responses = GraphqlResponses410()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(entry.entry_id)
