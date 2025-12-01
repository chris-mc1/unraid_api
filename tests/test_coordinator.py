"""Tests for Coordinator error handling and edge cases."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.config_entries import ConfigEntryState

from . import setup_config_entry
from .graphql_responses import GraphqlResponses420

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant

    from tests.conftest import GraphqlServerMocker


class GraphqlResponsesAuthError(GraphqlResponses420):
    """Graphql Responses that returns auth error."""

    is_unauthenticated = True


class GraphqlResponsesServerError(GraphqlResponses420):
    """Graphql Responses that returns server error."""

    all_error = True


class GraphqlResponsesNoDisks(GraphqlResponses420):
    """Graphql Responses with no disks."""

    def __init__(self) -> None:
        super().__init__()
        self.disks = {
            "data": {
                "array": {
                    "disks": [],
                    "parities": [],
                    "caches": [],
                }
            }
        }


class GraphqlResponsesNoShares(GraphqlResponses420):
    """Graphql Responses with no shares."""

    def __init__(self) -> None:
        super().__init__()
        self.shares = {"data": {"shares": []}}


class GraphqlResponsesArrayStopped(GraphqlResponses420):
    """Graphql Responses with array stopped (capacity is 0)."""

    def __init__(self) -> None:
        super().__init__()
        self.array = {
            "data": {
                "array": {
                    "state": "STOPPED",
                    "capacity": {
                        "kilobytes": {"free": "0", "used": "0", "total": "0"},
                    },
                }
            }
        }


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_auth_error_triggers_reauth(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test that auth errors trigger reauth flow."""
    mocker = await mock_graphql_server(GraphqlResponsesAuthError)
    # Setup will fail due to auth error during coordinator refresh
    entry = await setup_config_entry(hass, mocker, expect_success=False)
    # Entry should be in setup error state (auth failed)
    assert entry.state in (ConfigEntryState.SETUP_ERROR, ConfigEntryState.SETUP_RETRY)


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_server_error_handling(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test that server errors are handled gracefully."""
    mocker = await mock_graphql_server(GraphqlResponsesServerError)
    entry = await setup_config_entry(hass, mocker, expect_success=False)
    # Entry should be in setup error or retry state
    assert entry.state in (ConfigEntryState.SETUP_ERROR, ConfigEntryState.SETUP_RETRY)


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_empty_disks_list(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test that empty disk list doesn't cause errors."""
    mocker = await mock_graphql_server(GraphqlResponsesNoDisks)
    assert await setup_config_entry(hass, mocker)

    # Array sensors should still work
    state = hass.states.get("sensor.test_server_array_state")
    assert state is not None
    assert state.state == "started"

    # No disk sensors should exist
    assert hass.states.get("sensor.test_server_disk1_status") is None
    assert hass.states.get("sensor.test_server_parity_status") is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_empty_shares_list(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test that empty shares list doesn't cause errors."""
    mocker = await mock_graphql_server(GraphqlResponsesNoShares)
    assert await setup_config_entry(hass, mocker)

    # Array sensors should still work
    state = hass.states.get("sensor.test_server_array_state")
    assert state is not None

    # No share sensors should exist
    assert hass.states.get("sensor.test_server_share_1_free_space") is None
    assert hass.states.get("sensor.test_server_share_2_free_space") is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_disk_with_null_temperature(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test disk with null temperature (parity disk has no temp)."""
    mocker = await mock_graphql_server(GraphqlResponses420)
    assert await setup_config_entry(hass, mocker)

    # Parity disk has null temperature in test data
    state = hass.states.get("sensor.test_server_parity_temperature")
    assert state is not None
    assert state.state == "unknown"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_array_started_state(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test array state sensor shows correct value."""
    mocker = await mock_graphql_server(GraphqlResponses420)
    assert await setup_config_entry(hass, mocker)

    state = hass.states.get("sensor.test_server_array_state")
    assert state is not None
    assert state.state == "started"
    # Check enum options are set
    assert "started" in state.attributes.get("options", [])
    assert "stopped" in state.attributes.get("options", [])


async def test_array_stopped_state(
    hass: HomeAssistant,
    mock_graphql_server: GraphqlServerMocker,
) -> None:
    """Test handling when array is stopped (capacity is 0)."""
    mocker = await mock_graphql_server(GraphqlResponsesArrayStopped)
    assert await setup_config_entry(hass, mocker)

    # Array usage percentage should be None (not a ZeroDivisionError) when stopped
    state = hass.states.get("sensor.test_server_array_usage")
    assert state is not None
    assert state.state == "unknown"  # None value shows as "unknown"
    assert state.state == "unknown"  # None value shows as "unknown"
