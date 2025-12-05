"""Tests for Device registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.unraid_api.const import DOMAIN

from . import setup_config_entry
from .graphql_responses import API_RESPONSES_LATEST

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceRegistry

    from .conftest import GraphqlServerMocker


async def test_device_registry(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
    device_registry: DeviceRegistry,
) -> None:
    """Test device registry."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    entry = await setup_config_entry(hass, mocker)
    device = device_registry.async_get_device({(DOMAIN, entry.entry_id)})

    assert device.name == "Test Server"
    assert device.sw_version == "7.0.1"
    assert device.configuration_url == "http://1.2.3.4"


async def test_ups_device_registry(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
    device_registry: DeviceRegistry,
) -> None:
    """Test UPS device registry."""
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    entry = await setup_config_entry(hass, mocker)

    root_device = device_registry.async_get_device({(DOMAIN, entry.entry_id)})
    ups_device = device_registry.async_get_device({(DOMAIN, f"{entry.entry_id}_Back-UPS ES 650G2")})

    assert ups_device.name == "Back-UPS ES 650G2"
    assert ups_device.model == "Back-UPS ES 650G2"
    assert ups_device.via_device_id == root_device.id
