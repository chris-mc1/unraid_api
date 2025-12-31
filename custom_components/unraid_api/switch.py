"""Unraid Docker Container Switches."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DOCKER
from .coordinator import UnraidDockerCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import UnraidConfigEntry
    from .models import DockerContainer

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""

    @callback
    def add_docker_callback(container: DockerContainer) -> None:
        _LOGGER.info("Adding new Docker container switch: %s (id: %s)", container.name, container.id)
        entity = UnraidDockerSwitch(config_entry, container.id)
        async_add_entites([entity])

    if config_entry.options.get(CONF_DOCKER, True) and config_entry.runtime_data.docker_coordinator:
        config_entry.runtime_data.docker_coordinator.subscribe_docker(add_docker_callback)


class UnraidDockerSwitch(CoordinatorEntity[UnraidDockerCoordinator], SwitchEntity):
    """Switch for Unraid Docker Containers."""

    _attr_has_entity_name = False  # Use container name directly, not as entity name
    _attr_icon = "mdi:docker"  # Docker icon from Material Design Icons

    def __init__(
        self,
        config_entry: UnraidConfigEntry,
        container_id: str,
    ) -> None:
        if config_entry.runtime_data.docker_coordinator is None:
            raise ValueError("Docker coordinator not available")
        super().__init__(config_entry.runtime_data.docker_coordinator)
        self.container_id = container_id
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}-docker-{self.container_id}"
        self._attr_available = False
        # Group under main server device
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        try:
            return self.coordinator.data["docker_containers"][self.container_id].name
        except (KeyError, AttributeError):
            return f"Docker {self.container_id[:12]}"

    @property
    def is_on(self) -> bool:
        """Return True if the container is running."""
        try:
            container = self.coordinator.data["docker_containers"][self.container_id]
            return container.state.upper() == "RUNNING"
        except (KeyError, AttributeError):
            return False

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        try:
            container = self.coordinator.data["docker_containers"][self.container_id]
            return {
                "container_id": container.id,
                "names": container.names,
                "state": container.state,
                "status": container.status,
                "auto_start": container.auto_start,
                "image": container.image,
            }
        except (KeyError, AttributeError):
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.container_id in self.coordinator.data["docker_containers"]
            and self.coordinator.last_update_success
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the container on (start it)."""
        try:
            await self.coordinator.api_client.start_docker_container(
                self.container_id
            )
            _LOGGER.info("Started Docker container: %s", self.name)
            # Request a coordinator update to refresh the state
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            _LOGGER.error("Failed to start Docker container %s: %s", self.name, exc, exc_info=True)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the container off (stop it)."""
        try:
            await self.coordinator.api_client.stop_docker_container(
                self.container_id
            )
            _LOGGER.info("Stopped Docker container: %s", self.name)
            # Request a coordinator update to refresh the state
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            _LOGGER.error("Failed to stop Docker container %s: %s", self.name, exc, exc_info=True)
            raise

