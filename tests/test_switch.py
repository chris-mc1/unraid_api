"""Tests for Switch entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)

from . import setup_config_entry
from .api_states import API_STATES, ApiState

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from homeassistant.core import HomeAssistant

    from .conftest import MockApiClient


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_docker_switches(
    api_state: ApiState, hass: HomeAssistant, mock_api_client: MagicMock
) -> None:
    """Test docker container switch entities."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)

    state = hass.states.get("switch.test_server_homeassistant")
    assert state.state == STATE_ON
    assert state.name == "Test Server homeassistant"

    state = hass.states.get("switch.test_server_grafana_public")
    assert state.state == STATE_OFF
    assert state.name == "Test Server Grafana Public"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize(("api_state"), API_STATES)
async def test_docker_switches_action(
    api_state: ApiState, hass: HomeAssistant, mock_api_client: MagicMock
) -> None:
    """Test docker container switch actions."""
    api_client: MockApiClient = mock_api_client.return_value
    api_client.state = api_state()
    assert await setup_config_entry(hass)

    await hass.services.async_call(
        domain=SWITCH_DOMAIN,
        service=SERVICE_TURN_ON,
        service_data={ATTR_ENTITY_ID: "switch.test_server_grafana_public"},
        blocking=True,
    )
    api_client.start_container.assert_awaited_once_with(api_client.state.docker[2].id)

    await hass.services.async_call(
        domain=SWITCH_DOMAIN,
        service=SERVICE_TURN_OFF,
        service_data={ATTR_ENTITY_ID: "switch.test_server_homeassistant"},
        blocking=True,
    )
    api_client.stop_container.assert_awaited_once_with(api_client.state.docker[0].id)


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_docker_switches_removed(hass: HomeAssistant, mock_api_client: MagicMock) -> None:
    """Test docker container switch entities."""
    api_client: MockApiClient = mock_api_client.return_value

    config_entry = await setup_config_entry(hass)
    assert config_entry

    assert hass.states.get("switch.test_server_homeassistant")
    assert hass.states.get("switch.test_server_grafana_public")

    api_client.state.docker.pop(0)
    await config_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("switch.test_server_homeassistant") is None
    assert hass.states.get("switch.test_server_grafana_public")
