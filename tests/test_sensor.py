"""Tests for Sensor entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from . import setup_config_entry
from .const import MOCK_OPTION_DATA_DISABLED
from .graphql_responses import API_RESPONSES, API_RESPONSES_LATEST, GraphqlResponses

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant

    from tests.conftest import GraphqlServerMocker


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_main_sensors(
    api_responses: GraphqlResponses,
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test main sensor entities."""
    mocker = await mock_graphql_server(api_responses)
    assert await setup_config_entry(hass, mocker)

    # array_state
    state = hass.states.get("sensor.test_server_array_state")
    assert state.state == "started"

    # array_usage
    state = hass.states.get("sensor.test_server_array_usage")
    assert state.state == "95.6401783630953"
    assert state.attributes["used"] == 11474981430
    assert state.attributes["free"] == 523094720
    assert state.attributes["total"] == 11998076150

    # array_free
    state = hass.states.get("sensor.test_server_array_free_space")
    assert state.state == "523.09472"

    # array_used
    state = hass.states.get("sensor.test_server_array_used_space")
    assert state.state == "11474.98143"

    # ram_usage
    state = hass.states.get("sensor.test_server_ram_usage")
    assert state.state == "76.5687047158393"
    assert state.attributes["used"] == 12746354688
    assert state.attributes["free"] == 415510528
    assert state.attributes["total"] == 16646950912
    assert state.attributes["available"] == 3900596224

    # ram_used
    state = hass.states.get("sensor.test_server_ram_used")
    assert state.state == "12.746354688"

    # ram_free
    state = hass.states.get("sensor.test_server_ram_free")
    assert state.state == "0.415510528"

    # cpu_utilization
    state = hass.states.get("sensor.test_server_cpu_utilization")
    assert state.state == "5.1"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_disk_sensors(
    api_responses: GraphqlResponses,
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test disk sensor entities."""
    mocker = await mock_graphql_server(api_responses)
    assert await setup_config_entry(hass, mocker)

    # disk_status
    state = hass.states.get("sensor.test_server_parity_status")
    assert state.state == "disk_ok"
    state = hass.states.get("sensor.test_server_disk1_status")
    assert state.state == "disk_ok"
    state = hass.states.get("sensor.test_server_cache_status")
    assert state.state == "disk_ok"

    # disk_temp
    state = hass.states.get("sensor.test_server_parity_temperature")
    assert state.state == "unknown"
    state = hass.states.get("sensor.test_server_disk1_temperature")
    assert state.state == "34"
    state = hass.states.get("sensor.test_server_cache_temperature")
    assert state.state == "30"

    # disk_usage
    state = hass.states.get("sensor.test_server_parity_usage")
    assert state is None
    state = hass.states.get("sensor.test_server_disk1_usage")
    assert state.state == "92.2557011275512"
    state = hass.states.get("sensor.test_server_cache_usage")
    assert state.state == "67.5631962797181"

    # disk_free
    state = hass.states.get("sensor.test_server_parity_free_space")
    assert state is None
    state = hass.states.get("sensor.test_server_disk1_free_space")
    assert state.state == "464.583438"
    state = hass.states.get("sensor.test_server_cache_free_space")
    assert state.state == "38.907683"

    # disk_used
    state = hass.states.get("sensor.test_server_parity_used_space")
    assert state is None
    state = hass.states.get("sensor.test_server_disk1_used_space")
    assert state.state == "5534.454637"
    state = hass.states.get("sensor.test_server_cache_used_space")
    assert state.state == "81.041506"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_disk_sensors_disabled(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test disk sensor disabled."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    assert await setup_config_entry(hass, mocker, options=MOCK_OPTION_DATA_DISABLED)

    state = hass.states.get("sensor.test_server_parity_status")
    assert state is None

    state = hass.states.get("sensor.test_server_disk1_status")
    assert state is None

    state = hass.states.get("sensor.test_server_cache_status")
    assert state is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_share_sensors(
    api_responses: GraphqlResponses,
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test share sensor entities."""
    mocker = await mock_graphql_server(api_responses)
    assert await setup_config_entry(hass, mocker)

    # share_free
    state = hass.states.get("sensor.test_server_share_1_free_space")
    assert state.state == "523.094721"
    assert state.attributes["used"] == 11474981429
    assert state.attributes["total"] == 0
    assert state.attributes["allocator"] == "highwater"
    assert state.attributes["floor"] == "20000000"

    state = hass.states.get("sensor.test_server_share_2_free_space")
    assert state.state == "503.491121"
    assert state.attributes["used"] == 5615496143
    assert state.attributes["total"] == 0
    assert state.attributes["allocator"] == "highwater"
    assert state.attributes["floor"] == "0"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_share_sensors_disabled(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test share sensor disabled."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    assert await setup_config_entry(hass, mocker, options=MOCK_OPTION_DATA_DISABLED)

    state = hass.states.get("sensor.test_server_share_1_free_space")
    assert state is None

    state = hass.states.get("sensor.test_server_share_2_free_space")
    assert state is None
