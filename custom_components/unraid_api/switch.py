"""Unraid Switches."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DOCKER, CONF_VMS
from .coordinator import UnraidDataUpdateCoordinator
from .models import DockerContainer, DockerState, VirtualMachine, VmState

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from . import UnraidConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""

    @callback
    def add_vm_callback(vm: VirtualMachine) -> None:
        _LOGGER.debug("Adding VM switch: %s", vm.name)
        async_add_entities([UnraidVmSwitch(config_entry, vm.id)])

    @callback
    def add_docker_callback(container: DockerContainer) -> None:
        _LOGGER.debug("Adding Docker switch: %s", container.name)
        async_add_entities([UnraidDockerSwitch(config_entry, container.id)])

    if config_entry.options.get(CONF_VMS, False):
        config_entry.runtime_data.coordinator.subscribe_vms(add_vm_callback)
    if config_entry.options.get(CONF_DOCKER, False):
        config_entry.runtime_data.coordinator.subscribe_docker(add_docker_callback)


class UnraidVmSwitch(CoordinatorEntity[UnraidDataUpdateCoordinator], SwitchEntity):
    """Switch for Unraid VM power control."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: UnraidConfigEntry,
        vm_id: str,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.vm_id = vm_id
        self._attr_unique_id = f"{config_entry.entry_id}-vm-{self.vm_id}"
        self._attr_translation_key = "vm"
        self._attr_translation_placeholders = {
            "vm_name": self.coordinator.data["vms"][self.vm_id].name
        }
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if VM is running."""
        try:
            vm = self.coordinator.data["vms"][self.vm_id]
            return vm.state == VmState.RUNNING
        except (KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        try:
            vm = self.coordinator.data["vms"][self.vm_id]
            return {
                "state": vm.state.value,
            }
        except (KeyError, AttributeError):
            return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the VM."""
        await self.coordinator.async_vm_action(self.vm_id, "start")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the VM."""
        await self.coordinator.async_vm_action(self.vm_id, "stop")


class UnraidDockerSwitch(CoordinatorEntity[UnraidDataUpdateCoordinator], SwitchEntity):
    """Switch for Unraid Docker container power control."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: UnraidConfigEntry,
        container_id: str,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.container_id = container_id
        self._attr_unique_id = f"{config_entry.entry_id}-docker-{self.container_id}"
        self._attr_translation_key = "docker"
        self._attr_translation_placeholders = {
            "container_name": self.coordinator.data["docker"][self.container_id].name
        }
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if container is running."""
        try:
            container = self.coordinator.data["docker"][self.container_id]
            return container.state == DockerState.RUNNING
        except (KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        try:
            container = self.coordinator.data["docker"][self.container_id]
            return {
                "state": container.state.value,
                "image": container.image,
                "autostart": container.autostart,
            }
        except (KeyError, AttributeError):
            return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the container."""
        await self.coordinator.async_docker_action(self.container_id, "start")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the container."""
        await self.coordinator.async_docker_action(self.container_id, "stop")
