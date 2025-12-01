"""Tests for Switch entities (VMs and Docker containers)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.unraid_api.models import DockerContainer, DockerContainerState

from . import setup_config_entry
from .graphql_responses import API_RESPONSES_LATEST

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant

    from tests.conftest import GraphqlServerMocker


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_vm_switch_entity(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test VM switch entity."""
    mocker = await mock_graphql_server(GraphqlResponsesWithVMsAndContainers)
    assert await setup_config_entry(hass, mocker)

    # Check VM switch entity exists
    state = hass.states.get("switch.test_server_vm_test_vm")
    assert state is not None
    assert state.state == "on"  # VM is running
    assert state.attributes["vm_id"] == "vm-123"
    assert state.attributes["state"] == "RUNNING"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_vm_switch_turn_off(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test turning off a VM."""
    mocker = await mock_graphql_server(GraphqlResponsesWithVMsAndContainers)
    assert await setup_config_entry(hass, mocker)

    with patch(
        "custom_components.unraid_api.api.v4_20.UnraidApiV420.stop_vm",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_stop:
        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": "switch.test_server_vm_test_vm"},
            blocking=True,
        )
        mock_stop.assert_called_once_with("vm-123")


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_vm_switch_turn_on(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test turning on a VM."""
    mocker = await mock_graphql_server(GraphqlResponsesWithVMsAndContainersOff)
    assert await setup_config_entry(hass, mocker)

    with patch(
        "custom_components.unraid_api.api.v4_20.UnraidApiV420.start_vm",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_start:
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.test_server_vm_test_vm"},
            blocking=True,
        )
        mock_start.assert_called_once_with("vm-123")


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_docker_switch_entity(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test Docker container switch entity."""
    mocker = await mock_graphql_server(GraphqlResponsesWithVMsAndContainers)
    assert await setup_config_entry(hass, mocker)

    # Check Docker container switch entity exists
    state = hass.states.get("switch.test_server_container_nginx")
    assert state is not None
    assert state.state == "on"  # Container is running
    assert state.attributes["container_id"] == "container-456"
    assert state.attributes["state"] == "RUNNING"
    assert state.attributes["image"] == "nginx:latest"
    assert state.attributes["status"] == "Up 2 days"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_docker_switch_turn_off(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test turning off a Docker container."""
    mocker = await mock_graphql_server(GraphqlResponsesWithVMsAndContainers)
    assert await setup_config_entry(hass, mocker)

    mock_container = DockerContainer(
        id="container-456",
        names=["nginx"],
        state=DockerContainerState.EXITED,
    )

    with patch(
        "custom_components.unraid_api.api.v4_20.UnraidApiV420.stop_container",
        new_callable=AsyncMock,
        return_value=mock_container,
    ) as mock_stop:
        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": "switch.test_server_container_nginx"},
            blocking=True,
        )
        mock_stop.assert_called_once_with("container-456")


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_docker_switch_turn_on(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test turning on a Docker container."""
    mocker = await mock_graphql_server(GraphqlResponsesWithVMsAndContainersOff)
    assert await setup_config_entry(hass, mocker)

    mock_container = DockerContainer(
        id="container-456",
        names=["nginx"],
        state=DockerContainerState.RUNNING,
    )

    with patch(
        "custom_components.unraid_api.api.v4_20.UnraidApiV420.start_container",
        new_callable=AsyncMock,
        return_value=mock_container,
    ) as mock_start:
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.test_server_container_nginx"},
            blocking=True,
        )
        mock_start.assert_called_once_with("container-456")


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_multiple_containers(
    hass: HomeAssistant,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test multiple Docker containers are created."""
    mocker = await mock_graphql_server(GraphqlResponsesWithMultipleContainers)
    assert await setup_config_entry(hass, mocker)

    # Check all container switches exist
    assert hass.states.get("switch.test_server_container_nginx") is not None
    assert hass.states.get("switch.test_server_container_redis") is not None
    assert hass.states.get("switch.test_server_container_postgres") is not None


# Test response classes with VMs and containers


class GraphqlResponsesWithVMsAndContainers(API_RESPONSES_LATEST):
    """Graphql responses with VMs and Docker containers running."""

    def __init__(self) -> None:
        super().__init__()
        self.vms = {
            "data": {
                "vms": {
                    "domain": [
                        {
                            "id": "vm-123",
                            "name": "Test VM",
                            "state": "RUNNING",
                        }
                    ]
                }
            }
        }
        self.docker = {
            "data": {
                "docker": {
                    "containers": [
                        {
                            "id": "container-456",
                            "names": ["nginx"],
                            "state": "RUNNING",
                            "image": "nginx:latest",
                            "status": "Up 2 days",
                        }
                    ]
                }
            }
        }

    def get_response(self, query: str) -> dict:
        if query == "VMs":
            return self.vms
        if query == "Docker":
            return self.docker
        return super().get_response(query)


class GraphqlResponsesWithVMsAndContainersOff(API_RESPONSES_LATEST):
    """Graphql responses with VMs and Docker containers stopped."""

    def __init__(self) -> None:
        super().__init__()
        self.vms = {
            "data": {
                "vms": {
                    "domain": [
                        {
                            "id": "vm-123",
                            "name": "Test VM",
                            "state": "SHUTOFF",
                        }
                    ]
                }
            }
        }
        self.docker = {
            "data": {
                "docker": {
                    "containers": [
                        {
                            "id": "container-456",
                            "names": ["nginx"],
                            "state": "EXITED",
                            "image": "nginx:latest",
                            "status": "Exited (0) 1 hour ago",
                        }
                    ]
                }
            }
        }

    def get_response(self, query: str) -> dict:
        if query == "VMs":
            return self.vms
        if query == "Docker":
            return self.docker
        return super().get_response(query)


class GraphqlResponsesWithMultipleContainers(API_RESPONSES_LATEST):
    """Graphql responses with multiple Docker containers."""

    def __init__(self) -> None:
        super().__init__()
        self.vms = {"data": {"vms": {"domain": []}}}
        self.docker = {
            "data": {
                "docker": {
                    "containers": [
                        {
                            "id": "container-1",
                            "names": ["nginx"],
                            "state": "RUNNING",
                            "image": "nginx:latest",
                            "status": "Up 2 days",
                        },
                        {
                            "id": "container-2",
                            "names": ["redis"],
                            "state": "RUNNING",
                            "image": "redis:7",
                            "status": "Up 1 day",
                        },
                        {
                            "id": "container-3",
                            "names": ["postgres"],
                            "state": "EXITED",
                            "image": "postgres:15",
                            "status": "Exited (0) 3 hours ago",
                        },
                    ]
                }
            }
        }

    def get_response(self, query: str) -> dict:
        if query == "VMs":
            return self.vms
        if query == "Docker":
            return self.docker
        return super().get_response(query)
