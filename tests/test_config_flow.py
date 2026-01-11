"""Tests for config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientConnectionError, ClientConnectorSSLError
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.api import (
    IncompatibleApiError,
    UnraidAuthError,
    UnraidGraphQLError,
)
from custom_components.unraid_api.const import CONF_DRIVES, CONF_SHARES, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.data_entry_flow import FlowResultType

from . import add_config_entry
from .api_states import API_STATES, ApiState
from .const import DEFAULT_HOST

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .conftest import MockApiClient


@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_user_init(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_api_client: MagicMock,
) -> None:
    """Test config flow."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: DEFAULT_HOST, CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
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
    assert result["data"][CONF_HOST] == DEFAULT_HOST
    assert result["data"][CONF_VERIFY_SSL] is False
    assert result["options"][CONF_SHARES] is True
    assert result["options"][CONF_DRIVES] is True

    mock_setup_entry.assert_awaited_once()


async def test_user_error_response(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_api_client: MagicMock,
) -> None:
    """Test a config flow flow with GraphQL error response."""
    mock_api_client.side_effect = UnraidGraphQLError(
        response={"errors": [{"message": "Internal Server error"}]}
    )
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: DEFAULT_HOST, CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
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
    mock_api_client: MagicMock,
) -> None:
    """Test a config flow with TimeoutError."""
    mock_api_client.side_effect = TimeoutError()

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
    mock_api_client: MagicMock,
) -> None:
    """Test a config flow with ClientConnectionError."""
    mock_api_client.side_effect = ClientConnectionError()

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
    mock_api_client: MagicMock,
) -> None:
    """Test a config flow with ClientConnectorSSLError."""
    mock_api_client.side_effect = ClientConnectorSSLError(MagicMock(), MagicMock())

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
    mock_api_client: MagicMock,
) -> None:
    """Test a config flow with IncompatibleApiError."""
    mock_api_client.side_effect = IncompatibleApiError(
        AwesomeVersion("4.10.0"), AwesomeVersion("4.20.0")
    )

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: DEFAULT_HOST, CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "api_incompatible"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_user_connection_auth_failed(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_api_client: MagicMock,
) -> None:
    """Test a config flow with UnraidAuthError."""
    mock_api_client.side_effect = UnraidAuthError(response={"errors": []})

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: DEFAULT_HOST,
            CONF_API_KEY: "test_key",
            CONF_VERIFY_SSL: False,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "auth_failed"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_reauth(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_api_client: MagicMock,
) -> None:
    """Test a reauthentication flow."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()

    mock_config = add_config_entry(hass)

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
    assert mock_config.data[CONF_HOST] == DEFAULT_HOST
    assert mock_config.data[CONF_VERIFY_SSL] is False

    await hass.async_block_till_done()
    mock_setup_entry.assert_awaited_once()


async def test_reauth_error_response(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_api_client: MagicMock,
) -> None:
    """Test a reauthentication flow with GraphQL error response."""
    mock_api_client.side_effect = UnraidGraphQLError(
        response={"errors": [{"message": "Internal Server error"}]}
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
    assert result["errors"]["base"] == "error_response"
    assert result["description_placeholders"]["error_msg"] == "Internal Server error"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_reauth_connection_failed_timeout(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_api_client: MagicMock,
) -> None:
    """Test a reauthentication flow with TimeoutError."""
    mock_api_client.side_effect = TimeoutError()

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
    mock_api_client: MagicMock,
) -> None:
    """Test a reauthentication flow with ClientConnectionError."""
    mock_api_client.side_effect = ClientConnectionError()

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
    mock_api_client: MagicMock,
) -> None:
    """Test a reauthentication flow with ClientConnectorSSLError."""
    mock_api_client.side_effect = ClientConnectorSSLError(MagicMock(), MagicMock())

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
    mock_api_client: MagicMock,
) -> None:
    """Test a reauthentication flow with ClientConnectorSSLError."""
    mock_api_client.side_effect = UnraidAuthError(response={"errors": []})

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
    assert result["errors"]["base"] == "auth_failed"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_options(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test Options flow."""
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
