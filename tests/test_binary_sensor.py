"""Tests for Sensor entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from . import setup_config_entry
from .api_states import API_STATES, ApiState
from .const import MOCK_OPTION_DATA_DISABLED

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from homeassistant.core import HomeAssistant

    from .conftest import MockApiClient


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_main_binary_sensor(
    api_state: ApiState,
    hass: HomeAssistant,
    mock_api_client: MagicMock,
) -> None:
    """Test disk sensor entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)

    state = hass.states.get("binary_sensor.test_server_parity_spinning")
    assert state.state == "off"

    state = hass.states.get("binary_sensor.test_server_disk1_spinning")
    assert state.state == "on"

    state = hass.states.get("binary_sensor.test_server_disk1_spinning")
    assert state.state == "on"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_disk_sensors_disabled(
    hass: HomeAssistant,
    mock_api_client: MagicMock,  # noqa: ARG001
) -> None:
    """Test disk sensor disabled."""
    assert await setup_config_entry(hass, options=MOCK_OPTION_DATA_DISABLED)

    state = hass.states.get("binary_sensor.test_server_parity_spinning")
    assert state is None

    state = hass.states.get("binary_sensor.test_server_disk1_spinning")
    assert state is None

    state = hass.states.get("binary_sensor.test_server_disk1_spinning")
    assert state is None
