"""Tests for API v4.26 specific functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from awesomeversion import AwesomeVersion

from . import setup_config_entry
from .graphql_responses import GraphqlResponses420

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant

    from tests.conftest import GraphqlServerMocker


class GraphqlResponses426(GraphqlResponses420):
    """Graphql Responses for API version 4.26 with CPU temp and power."""

    version = AwesomeVersion("4.26.0")

    def __init__(self) -> None:
        super().__init__()
        self.api_version = {"data": {"info": {"versions": {"core": {"api": "4.26.0"}}}}}
        # Override metrics to include CPU temp and power from info.cpu.packages
        self.metrics = {
            "data": {
                "metrics": {
                    "memory": {
                        "free": 415510528,
                        "total": 16646950912,
                        "active": 12746354688,
                        "percentTotal": 76.56870471583932,
                        "available": 3900596224,
                    },
                    "cpu": {"percentTotal": 5.1},
                },
                "info": {
                    "cpu": {
                        "packages": {
                            "power": [45.5],
                            "temp": [62.0],
                        }
                    }
                },
            }
        }


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_v426_cpu_temperature_sensor(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test CPU temperature sensor with v4.26 API."""
    mocker = await mock_graphql_server(GraphqlResponses426)
    assert await setup_config_entry(hass, mocker)

    # CPU temperature should have a value from info.cpu.packages.temp
    state = hass.states.get("sensor.test_server_cpu_temperature")
    assert state is not None
    assert state.state == "62.0"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_v426_cpu_power_sensor(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test CPU power sensor with v4.26 API."""
    mocker = await mock_graphql_server(GraphqlResponses426)
    assert await setup_config_entry(hass, mocker)

    # CPU power should have a value from info.cpu.packages.power
    state = hass.states.get("sensor.test_server_cpu_power")
    assert state is not None
    assert state.state == "45.5"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_v420_cpu_temperature_unknown(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test CPU temperature is unknown with v4.20 API (no cpu packages data)."""
    mocker = await mock_graphql_server(GraphqlResponses420)
    assert await setup_config_entry(hass, mocker)

    # CPU temperature should be unknown on v4.20
    state = hass.states.get("sensor.test_server_cpu_temperature")
    assert state is not None
    assert state.state == "unknown"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_v420_cpu_power_unknown(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test CPU power is unknown with v4.20 API (no cpu packages data)."""
    mocker = await mock_graphql_server(GraphqlResponses420)
    assert await setup_config_entry(hass, mocker)

    # CPU power should be unknown on v4.20
    state = hass.states.get("sensor.test_server_cpu_power")
    assert state is not None
    assert state.state == "unknown"
