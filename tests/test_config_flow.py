"""Tests for config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from custom_components.unraid_api.const import CONF_DRIVES, CONF_SHARES, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import (
    API_VERSION_RESPONSE_INCOMPATIBLE,
    API_VERSION_RESPONSE_UNAUTHENTICATED,
    MOCK_CONFIG_DATA,
    MOCK_OPTION_DATA,
)

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker


async def test_user_init(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_get_api_client: AsyncMock,  # noqa: ARG001
) -> None:
    """Test config flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
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
    assert result["data"][CONF_HOST] == "http://1.2.3.4"
    assert result["data"][CONF_VERIFY_SSL] is False
    assert result["data"][CONF_VERIFY_SSL] is False
    assert result["options"][CONF_SHARES] is True
    assert result["options"][CONF_DRIVES] is True

    mock_setup_entry.assert_awaited_once()


async def test_user_error_response(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a config flow flow with GraphQL error response."""
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json={
            "errors": [
                {
                    "message": "API key validation failed",
                }
            ],
            "data": {"server": None},
        },
        headers={"Content-Type": "application/json"},
    )
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "error_response"
    assert result["description_placeholders"]["error_msg"] == "API key validation failed"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_user_connection_failed_timeout(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a config flow with TimeoutError."""
    aioclient_mock.post("http://1.2.3.4/graphql", exc=TimeoutError())
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
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a config flow with ClientConnectionError."""
    aioclient_mock.post("http://1.2.3.4/graphql", exc=ClientConnectionError())
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
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a config flow with ClientConnectorSSLError."""
    aioclient_mock.post(
        "http://1.2.3.4/graphql", exc=ClientConnectorSSLError(MagicMock(), MagicMock())
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
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a config flow with ClientConnectorSSLError."""
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=API_VERSION_RESPONSE_INCOMPATIBLE,
        headers={"Content-Type": "application/json"},
    )
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "api_incompatible"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_user_connection_auth_failed(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a config flow with ClientConnectorSSLError."""
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=API_VERSION_RESPONSE_UNAUTHENTICATED,
        headers={"Content-Type": "application/json"},
    )
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "auth_failed"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_reauth(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_get_api_client: AsyncMock,  # noqa: ARG001
) -> None:
    """Test a reauthentication flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_DATA,
    )
    mock_config.add_to_hass(hass)

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
    assert mock_config.data[CONF_HOST] == "http://1.2.3.4"
    assert mock_config.data[CONF_VERIFY_SSL] is False

    mock_setup_entry.assert_awaited_once()


async def test_reauth_error_response(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a reauthentication flow with GraphQL error response."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_DATA,
    )
    mock_config.add_to_hass(hass)

    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json={
            "errors": [
                {
                    "message": "API key validation failed",
                }
            ],
            "data": {"server": None},
        },
        headers={"Content-Type": "application/json"},
    )
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
    assert result["description_placeholders"]["error_msg"] == "API key validation failed"

    hass.config_entries.flow.async_abort(result["flow_id"])
    mock_setup_entry.assert_not_awaited()


async def test_reauth_connection_failed_timeout(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a reauthentication flow with TimeoutError."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_DATA,
    )
    mock_config.add_to_hass(hass)

    aioclient_mock.post("http://1.2.3.4/graphql", exc=TimeoutError())

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
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a reauthentication flow with ClientConnectionError."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_DATA,
    )
    mock_config.add_to_hass(hass)

    aioclient_mock.post("http://1.2.3.4/graphql", exc=ClientConnectionError())

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
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a reauthentication flow with ClientConnectorSSLError."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_DATA,
    )
    mock_config.add_to_hass(hass)

    aioclient_mock.post(
        "http://1.2.3.4/graphql", exc=ClientConnectorSSLError(MagicMock(), MagicMock())
    )

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
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a reauthentication flow with ClientConnectorSSLError."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_DATA,
    )
    mock_config.add_to_hass(hass)

    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=API_VERSION_RESPONSE_UNAUTHENTICATED,
        headers={"Content-Type": "application/json"},
    )

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
    mock_get_api_client: AsyncMock,  # noqa: ARG001
) -> None:
    """Test Reconfigure flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA, options=MOCK_OPTION_DATA)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert not result["errors"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SHARES: False, CONF_DRIVES: False},
    )

    assert entry.options[CONF_SHARES] is False
    assert entry.options[CONF_DRIVES] is False

    await hass.async_block_till_done()
    mock_setup_entry.assert_awaited_once()
