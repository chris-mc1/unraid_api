"""Tests for config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientConnectionError, ClientConnectorSSLError
from custom_components.unraid_api.api import UnraidApiClient
from custom_components.unraid_api.const import CONF_DRIVES, CONF_SHARES, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.data_entry_flow import FlowResultType

from . import add_config_entry
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
async def test_user_init(
    api_responses: GraphqlResponses,
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test config flow."""
    mocker = await mock_graphql_server(api_responses)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: mocker.host, CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_SHARES: True, CONF_DRIVES: True},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Server"
    assert result["data"][CONF_API_KEY] == "test_key"
    assert result["data"][CONF_HOST] == mocker.host
    assert result["data"][CONF_VERIFY_SSL] is False
    assert result["options"][CONF_SHARES] is True
    assert result["options"][CONF_DRIVES] is True

    mock_setup_entry.assert_awaited_once()


async def test_user_error_response(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test a config flow flow with GraphQL error response."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    mocker.responses.all_error = True
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: mocker.host, CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "error_response"
    assert result["description_placeholders"]["error_msg"] == "Internal Server error"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_user_connection_failed_timeout(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a config flow with TimeoutError."""
    monkeypatch.setattr(
        UnraidApiClient, "call_api", AsyncMock(side_effect=TimeoutError()), raising=True
    )
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "cannot_connect"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_user_connection_failed_connection_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a config flow with ClientConnectionError."""
    monkeypatch.setattr(
        UnraidApiClient, "call_api", AsyncMock(side_effect=ClientConnectionError()), raising=True
    )
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "cannot_connect"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_user_connection_failed_ssl_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a config flow with ClientConnectorSSLError."""
    monkeypatch.setattr(
        UnraidApiClient,
        "call_api",
        AsyncMock(side_effect=ClientConnectorSSLError(MagicMock(), MagicMock())),
        raising=True,
    )
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "ssl_error"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_user_connection_incompatible(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test a config flow with ClientConnectorSSLError."""
    mocker = await mock_graphql_server(GraphqlResponses410)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: mocker.host, CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "api_incompatible"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_user_connection_auth_failed(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test a config flow with ClientConnectorSSLError."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    mocker.responses.is_unauthenticated = True
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: mocker.host,
            CONF_API_KEY: "test_key",
            CONF_VERIFY_SSL: False,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "auth_failed"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_reauth(
    api_responses: GraphqlResponses,
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test a reauthentication flow."""
    mocker = await mock_graphql_server(api_responses)
    mock_config = add_config_entry(hass, mocker)

    result = await mock_config.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_key"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "new_key",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config.data[CONF_API_KEY] == "new_key"
    assert mock_config.data[CONF_HOST] == mocker.host
    assert mock_config.data[CONF_VERIFY_SSL] is False

    await hass.async_block_till_done()
    mock_setup_entry.assert_awaited_once()


async def test_reauth_error_response(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test a reauthentication flow with GraphQL error response."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    mocker.responses.all_error = True
    mock_config = add_config_entry(hass, mocker)

    result = await mock_config.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "new_key",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_key"
    assert result["errors"]["base"] == "error_response"
    assert result["description_placeholders"]["error_msg"] == "Internal Server error"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_reauth_connection_failed_timeout(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a reauthentication flow with TimeoutError."""
    monkeypatch.setattr(
        UnraidApiClient, "call_api", AsyncMock(side_effect=TimeoutError()), raising=True
    )
    mock_config = add_config_entry(hass)

    result = await mock_config.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "new_key",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_key"
    assert result["errors"]["base"] == "cannot_connect"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_reauth_connection_failed_connection_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a reauthentication flow with ClientConnectionError."""
    monkeypatch.setattr(
        UnraidApiClient, "call_api", AsyncMock(side_effect=ClientConnectionError()), raising=True
    )
    mock_config = add_config_entry(hass)

    result = await mock_config.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "new_key",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_key"
    assert result["errors"]["base"] == "cannot_connect"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_reauth_connection_failed_ssl_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a reauthentication flow with ClientConnectorSSLError."""
    monkeypatch.setattr(
        UnraidApiClient,
        "call_api",
        AsyncMock(side_effect=ClientConnectorSSLError(MagicMock(), MagicMock())),
        raising=True,
    )
    mock_config = add_config_entry(hass)

    result = await mock_config.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "new_key",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_key"
    assert result["errors"]["base"] == "ssl_error"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_reauth_connection_auth_failed(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test a reauthentication flow with ClientConnectorSSLError."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    mocker.responses.is_unauthenticated = True
    mock_config = add_config_entry(hass, mocker)

    result = await mock_config.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "new_key",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_key"
    assert result["errors"]["base"] == "auth_failed"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_options(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test Reconfigure flow."""
    mock_config = add_config_entry(hass)

    result = await hass.config_entries.options.async_init(mock_config.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert not result["errors"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SHARES: False, CONF_DRIVES: False},
    )

    assert mock_config.options[CONF_SHARES] is False
    assert mock_config.options[CONF_DRIVES] is False

    await hass.async_block_till_done()
    mock_setup_entry.assert_awaited_once()
