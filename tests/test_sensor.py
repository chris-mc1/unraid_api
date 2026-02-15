"""Tests for Sensor entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.const import (
    CONF_DOCKER_MODE,
    CONF_DRIVES,
    CONF_SHARES,
    DOCKER_MODE_ENABLED_ONLY,
    DOCKER_MODE_EXCEPT_DISABLED,
)
from custom_components.unraid_api.models import CpuMetricsSubscription, MemorySubscription

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
    api_client.memory_callback(
        MemorySubscription(
            free=415510528,
            total=16646950912,
            active=12746354688,
            available=3900596224,
            percent_total=76.56870471583932,
        )
    )
    await hass.async_block_till_done()

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

    # RAM
    state = hass.states.get("sensor.test_server_ram_usage")
    assert state.state == "76.5687047158393"
    assert state.attributes["used"] == 12746354688
    assert state.attributes["free"] == 415510528
    assert state.attributes["total"] == 16646950912
    assert state.attributes["available"] == 3900596224

    state = hass.states.get("sensor.test_server_ram_used")
    assert state.state == "12.746354688"

    state = hass.states.get("sensor.test_server_ram_free")
    assert state.state == "0.415510528"

    api_client.memory_callback(
        MemorySubscription(
            free=248168448,
            total=16644698112,
            active=11771707392,
            available=4872990720,
            percent_total=70.72346589159935,
        )
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_server_ram_usage")
    assert state.state == "70.7234658915993"
    assert state.attributes["used"] == 11771707392
    assert state.attributes["free"] == 248168448
    assert state.attributes["total"] == 16644698112
    assert state.attributes["available"] == 4872990720

    state = hass.states.get("sensor.test_server_ram_used")
    assert state.state == "11.771707392"

    state = hass.states.get("sensor.test_server_ram_free")
    assert state.state == "0.248168448"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_parity_check_sensors(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test parity check sensor entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)

    # parity_check_status
    state = hass.states.get("sensor.test_server_parity_check")
    assert state.state == "completed"

    # parity_check_date
    state = hass.states.get("sensor.test_server_parity_check_date")
    assert state.state == "2025-09-27T22:00:01+00:00"

    # parity_check_duration
    state = hass.states.get("sensor.test_server_parity_check_duration")
    assert state.state == "1.66166666666667"

    # parity_check_speed
    state = hass.states.get("sensor.test_server_parity_check_speed")
    assert state.state == "10.0"

    # parity_check_errors
    state = hass.states.get("sensor.test_server_parity_check_errors")
    assert state.state == "unknown"

    # parity_check_progress
    state = hass.states.get("sensor.test_server_parity_check_progress")
    assert state.state == "0"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_docker_sensors_monitor_all(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test docker container sensor entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)

    # homeassistant
    state = hass.states.get("sensor.test_server_homeassistant_state")
    assert state.state == "running"
    assert state.attributes["image"] == "ghcr.io/home-assistant/home-assistant:stable"
    assert (
        state.attributes["sha265"]
        == "e0477b544d48b26ad81e2132b8ce36f0a20dfd7eb44de9c40718fa78dc92e24d"
    )
    assert state.attributes["status"] == "Up 28 minutes"

    # postgres
    state = hass.states.get("sensor.test_server_postgres_state")
    assert state.state == "running"
    assert state.attributes["image"] == "postgres:15"
    assert (
        state.attributes["sha265"]
        == "a748a13f04094ee02b167d3e2a919368bc5e93cbd2b1c41a6d921dbaa59851ac"
    )
    assert state.attributes["status"] == "Up 28 minutes"

    # grafana
    state = hass.states.get("sensor.test_server_grafana_public_state")
    assert state.state == "exited"
    assert state.attributes["image"] == "grafana/grafana-enterprise"
    assert (
        state.attributes["sha265"]
        == "32241300d32d708c29a186e61692ff00d6c3f13cb862246326edd4612d735ae5"
    )
    assert state.attributes["status"] == "Up 28 minutes"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_docker_sensors_monitor_except_disabled(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test docker container sensor entities with "except_disabled" option ."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(
        hass, {CONF_SHARES: True, CONF_DRIVES: True, CONF_DOCKER_MODE: DOCKER_MODE_EXCEPT_DISABLED}
    )

    # homeassistant
    state = hass.states.get("sensor.test_server_homeassistant_state")
    assert state

    # postgres
    state = hass.states.get("sensor.test_server_postgres_state")
    assert state is None

    # grafana
    state = hass.states.get("sensor.test_server_grafana_public_state")
    assert state


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_docker_sensors_monitor_enabled_only(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test docker container sensor entities with "enabled_only" option ."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(
        hass, {CONF_SHARES: True, CONF_DRIVES: True, CONF_DOCKER_MODE: DOCKER_MODE_ENABLED_ONLY}
    )

    # homeassistant
    state = hass.states.get("sensor.test_server_homeassistant_state")
    assert state is None

    # postgres
    state = hass.states.get("sensor.test_server_postgres_state")
    assert state is None

    # grafana
    state = hass.states.get("sensor.test_server_grafana_public_state")
    assert state


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_docker_sensors_disabled(
    hass: HomeAssistant,
    mock_api_client: MagicMock,  # noqa: ARG001
) -> None:
    """Test share sensor disabled."""
    assert await setup_config_entry(hass, options=MOCK_OPTION_DATA_DISABLED)

    state = hass.states.get("sensor.test_server_homeassistant_state")
    assert state is None

    state = hass.states.get("sensor.test_server_postgres_state")
    assert state is None

    state = hass.states.get("sensor.test_server_grafana_public_state")
    assert state is None
