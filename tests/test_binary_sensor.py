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
async def test_main_binary_sensor(
    api_responses: GraphqlResponses,
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test disk sensor entities."""
    mocker = await mock_graphql_server(api_responses)
    assert await setup_config_entry(hass, mocker)

    state = hass.states.get("binary_sensor.test_server_parity_spinning")
    assert state.state == "off"

    state = hass.states.get("binary_sensor.test_server_disk1_spinning")
    assert state.state == "on"

    state = hass.states.get("binary_sensor.test_server_disk1_spinning")
    assert state.state == "on"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_disk_sensors_disabled(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test disk sensor disabled."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    assert await setup_config_entry(hass, mocker, options=MOCK_OPTION_DATA_DISABLED)

    state = hass.states.get("binary_sensor.test_server_parity_spinning")
    assert state is None

    state = hass.states.get("binary_sensor.test_server_disk1_spinning")
    assert state is None

    state = hass.states.get("binary_sensor.test_server_disk1_spinning")
    assert state is None
