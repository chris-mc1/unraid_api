"""Unraid Binary Sensors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity, SwitchEntityDescription
from homeassistant.core import callback

from . import _LOGGER
from .entity import UnraidBaseEntity, UnraidEntityDescription
from .helpers import error_handler
from .models import ContainerState, DockerContainer

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from . import UnraidConfigEntry


class UnraidDockerSwitchEntityDescription(
    UnraidEntityDescription, SwitchEntityDescription, frozen_or_thawed=True
):
    """Description for Unraid Docker Sensor Entity."""

    value_fn: Callable[[DockerContainer], StateType]


DOCKER_SWITCH_DESCRIPTIONS: tuple[UnraidDockerSwitchEntityDescription, ...] = (
    UnraidDockerSwitchEntityDescription(
        key="docker_switch",
        device_class=SwitchDeviceClass.SWITCH,
        value_fn=lambda container: container.state == ContainerState.RUNNING,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""

    @callback
    def add_container_callback(container_name: str) -> None:
        _LOGGER.debug("Switch: Adding new Docker container: %s", container_name)
        entities = [
            UnraidDockerSwitch(description, config_entry, container_name)
            for description in DOCKER_SWITCH_DESCRIPTIONS
            if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
        ]
        config_entry.runtime_data.containers[container_name]["entities"].extend(entities)
        async_add_entites(entities)

    config_entry.runtime_data.coordinator.subscribe_docker(add_container_callback)


class UnraidDockerSwitch(UnraidBaseEntity, SwitchEntity):
    """Switch for Docker containers."""

    entity_description: UnraidDockerSwitchEntityDescription
    _attr_name = None

    def __init__(
        self,
        description: UnraidDockerSwitchEntityDescription,
        config_entry: UnraidConfigEntry,
        container_name: str,
    ) -> None:
        super().__init__(description, config_entry)
        self.container_name = container_name
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.container_name}"
        self._attr_device_info = config_entry.runtime_data.containers[container_name]["device_info"]

    @property
    def is_on(self) -> bool:
        try:
            return self.entity_description.value_fn(
                self.coordinator.data["docker_containers"][self.container_name]
            )
        except (KeyError, AttributeError):
            return None

    @error_handler
    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.start_container(self.container_name)

    @error_handler
    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.stop_container(self.container_name)
