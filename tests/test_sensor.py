"""Tests for Sensor entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.models import CpuMetricsSubscription

from . import setup_config_entry
from .api_states import API_STATES, ApiState
from .const import MOCK_OPTION_DATA_DISABLED

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from homeassistant.core import HomeAssistant

    from .conftest import MockApiClient


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_main_sensors(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test main sensor entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)

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

    if api_state.version >= AwesomeVersion("4.26.0"):
        # cpu_temp
        state = hass.states.get("sensor.test_server_cpu_temperature")
        assert state.state == "31.0"
        # cpu_power
        state = hass.states.get("sensor.test_server_cpu_power")
        assert state.state == "2.8"
    else:
        # cpu_temp
        state = hass.states.get("sensor.test_server_cpu_temperature")
        assert state is None

        # cpu_power
        state = hass.states.get("sensor.test_server_cpu_power")
        assert state is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_disk_sensors(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test disk sensor entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)

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
    mock_api_client: MagicMock,  # noqa: ARG001
) -> None:
    """Test disk sensor disabled."""
    assert await setup_config_entry(hass, options=MOCK_OPTION_DATA_DISABLED)

    state = hass.states.get("sensor.test_server_parity_status")
    assert state is None

    state = hass.states.get("sensor.test_server_disk1_status")
    assert state is None

    state = hass.states.get("sensor.test_server_cache_status")
    assert state is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_share_sensors(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test share sensor entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)

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
    mock_api_client: MagicMock,  # noqa: ARG001
) -> None:
    """Test share sensor disabled."""
    assert await setup_config_entry(hass, options=MOCK_OPTION_DATA_DISABLED)

    state = hass.states.get("sensor.test_server_share_1_free_space")
    assert state is None

    state = hass.states.get("sensor.test_server_share_2_free_space")
    assert state is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_ups_sensors(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test ups sensor entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)
    if api_state.version >= AwesomeVersion("4.26.0"):
        # ups_status
        state = hass.states.get("sensor.back_ups_es_650g2_status")
        assert state.state == "ONLINE"

        # ups_level
        state = hass.states.get("sensor.back_ups_es_650g2_level")
        assert state.state == "100"

        # ups_runtime
        state = hass.states.get("sensor.back_ups_es_650g2_runtime")
        assert state.state == "0.416666666666667"

        # ups_health
        state = hass.states.get("sensor.back_ups_es_650g2_health")
        assert state.state == "Good"

        # ups_load
        state = hass.states.get("sensor.back_ups_es_650g2_load")
        assert state.state == "20.0"

        # ups_input_voltage
        state = hass.states.get("sensor.back_ups_es_650g2_input_voltage")
        assert state.state == "232.0"

        # ups_output_voltage
        state = hass.states.get("sensor.back_ups_es_650g2_output_voltage")
        assert state.state == "120.5"

    else:
        # ups_status
        state = hass.states.get("sensor.back_ups_es_650g2_status")
        assert state is None

        # ups_level
        state = hass.states.get("sensor.back_ups_es_650g2_level")
        assert state is None

        # ups_runtime
        state = hass.states.get("sensor.back_ups_es_650g2_runtime")
        assert state is None

        # ups_health
        state = hass.states.get("sensor.back_ups_es_650g2_health")
        assert state is None

        # ups_load
        state = hass.states.get("sensor.back_ups_es_650g2_load")
        assert state is None

        # ups_input_voltage
        state = hass.states.get("sensor.back_ups_es_650g2_input_voltage")
        assert state is None

        # ups_output_voltage
        state = hass.states.get("sensor.back_ups_es_650g2_output_voltage")
        assert state is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_main_sensors_subscriptions(
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test subscription sensor entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.websocket_connected = True
    assert await setup_config_entry(hass)
    api_client.cpu_usage_callback(7.5)
    api_client.cpu_metrics_callback(CpuMetricsSubscription(temp=31.0, power=2.8))

    # cpu_utilization
    state = hass.states.get("sensor.test_server_cpu_utilization")
    assert state.state == "7.5"

    api_client.cpu_usage_callback(5.1)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_server_cpu_utilization")
    assert state.state == "5.1"

    # cpu_temp, cpu_power
    state = hass.states.get("sensor.test_server_cpu_temperature")
    assert state.state == "31.0"

    state = hass.states.get("sensor.test_server_cpu_power")
    assert state.state == "2.8"

    api_client.cpu_metrics_callback(CpuMetricsSubscription(temp=35.0, power=3.5))
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_server_cpu_temperature")
    assert state.state == "35.0"

    state = hass.states.get("sensor.test_server_cpu_power")
    assert state.state == "3.5"
