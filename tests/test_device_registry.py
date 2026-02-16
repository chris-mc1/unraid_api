"""Tests for Device registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.unraid_api.const import DOMAIN

from . import setup_config_entry

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceRegistry

    from tests.conftest import MockApiClient


async def test_device_registry(
    hass: HomeAssistant,
    mock_api_client: MagicMock,  # noqa: ARG001
    device_registry: DeviceRegistry,
) -> None:
    """Test device registry."""
    config_entry = await setup_config_entry(hass)
    device = device_registry.async_get_device({(DOMAIN, config_entry.entry_id)})

    assert device.name == "Test Server"
    assert device.sw_version == "7.0.1"
    assert device.configuration_url == "http://1.2.3.4"


async def test_ups_device_registry(
    hass: HomeAssistant,
    mock_api_client: MagicMock,  # noqa: ARG001
    device_registry: DeviceRegistry,
) -> None:
    """Test UPS device registry."""
    config_entry = await setup_config_entry(hass)

    root_device = device_registry.async_get_device({(DOMAIN, config_entry.entry_id)})
    ups_device = device_registry.async_get_device(
        {(DOMAIN, f"{config_entry.entry_id}_Back-UPS ES 650G2")}
    )

    assert ups_device.name == "Back-UPS ES 650G2"
    assert ups_device.model == "Back-UPS ES 650G2"
    assert ups_device.via_device_id == root_device.id


async def test_docker_device_registry(
    hass: HomeAssistant,
    mock_api_client: MagicMock,  # noqa: ARG001
    device_registry: DeviceRegistry,
) -> None:
    """Test Docker device registry."""
    config_entry = await setup_config_entry(hass)

    root_device = device_registry.async_get_device({(DOMAIN, config_entry.entry_id)})

    container = device_registry.async_get_device(
        {(DOMAIN, f"{config_entry.entry_id}_docker_homeassistant")}
    )
    assert container.name == "Test Server homeassistant"
    assert container.sw_version == "2026.2.2"
    assert container.configuration_url == "http://homeassistant.unraid.lan"
    assert container.via_device_id == root_device.id

    container = device_registry.async_get_device(
        {(DOMAIN, f"{config_entry.entry_id}_docker_Postgres")}
    )
    assert container.name == "Test Server Postgres"
    assert container.via_device_id == root_device.id

    container = device_registry.async_get_device(
        {(DOMAIN, f"{config_entry.entry_id}_docker_Grafana Public")}
    )
    assert container.name == "Test Server Grafana Public"
    assert container.via_device_id == root_device.id


async def test_docker_device_registry_remove(
    hass: HomeAssistant,
    mock_api_client: MagicMock,
    device_registry: DeviceRegistry,
) -> None:
    """Test Docker device registry."""
    api_client: MockApiClient = mock_api_client.return_value

    config_entry = await setup_config_entry(hass)
    assert config_entry

    assert device_registry.async_get_device(
        {(DOMAIN, f"{config_entry.entry_id}_docker_homeassistant")}
    )

    api_client.state.docker.pop(0)
    await config_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert device_registry.async_remove_device
