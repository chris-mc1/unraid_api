"""Switch platform for Unraid VM and Docker control."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .models import DockerContainer, DockerContainerState, VirtualMachine, VMState

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import UnraidConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class UnraidVMSwitchEntityDescription(SwitchEntityDescription):
    """Describes Unraid VM switch entity."""

    icon_on: str = "mdi:desktop-tower"
    icon_off: str = "mdi:desktop-tower"


@dataclass(frozen=True, kw_only=True)
class UnraidDockerSwitchEntityDescription(SwitchEntityDescription):
    """Describes Unraid Docker switch entity."""

    icon_on: str = "mdi:docker"
    icon_off: str = "mdi:docker"


VM_SWITCH_DESCRIPTION = UnraidVMSwitchEntityDescription(
    key="vm",
    translation_key="vm",
)

DOCKER_SWITCH_DESCRIPTION = UnraidDockerSwitchEntityDescription(
    key="docker_container",
    translation_key="docker_container",
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Unraid switch entities."""
    coordinator = config_entry.runtime_data.coordinator

    @callback
    def add_vm_callback(vm: VirtualMachine) -> None:
        """Add switch entity for new VM."""
        _LOGGER.debug("Adding new VM: %s", vm.name)
        async_add_entities(
            [
                UnraidVMSwitch(
                    description=VM_SWITCH_DESCRIPTION,
                    config_entry=config_entry,
                    vm_id=vm.id,
                )
            ]
        )

    @callback
    def add_container_callback(container: DockerContainer) -> None:
        """Add switch entity for new Docker container."""
        _LOGGER.debug("Adding new container: %s", container.name)
        async_add_entities(
            [
                UnraidDockerSwitch(
                    description=DOCKER_SWITCH_DESCRIPTION,
                    config_entry=config_entry,
                    container_id=container.id,
                )
            ]
        )

    # Subscribe to new VMs and containers
    coordinator.subscribe_vms(add_vm_callback)
    coordinator.subscribe_containers(add_container_callback)


class UnraidVMSwitch(CoordinatorEntity["UnraidDataUpdateCoordinator"], SwitchEntity):
    """Represents an Unraid VM as a switch."""

    entity_description: UnraidVMSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidVMSwitchEntityDescription,
        config_entry: UnraidConfigEntry,
        vm_id: str,
    ) -> None:
        """Initialize the VM switch."""
        super().__init__(config_entry.runtime_data.coordinator)
        self.entity_description = description
        self._vm_id = vm_id
        self._attr_unique_id = f"{config_entry.entry_id}_vm_switch_{vm_id}"
        vm_name = self.coordinator.data["vms"][vm_id].name
        self._attr_translation_placeholders = {"name": vm_name}
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def _vm(self) -> VirtualMachine | None:
        """Get current VM data."""
        return self.coordinator.data["vms"].get(self._vm_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._vm is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if VM is running."""
        vm = self._vm
        if vm is None:
            return None
        return vm.state == VMState.RUNNING

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self.is_on:
            return self.entity_description.icon_on
        return self.entity_description.icon_off

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        vm = self._vm
        if vm is None:
            return None
        return {
            "vm_id": vm.id,
            "state": vm.state.value,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the VM."""
        vm = self._vm
        if vm is None:
            return
        _LOGGER.debug("Starting VM %s (%s)", vm.name, vm.id)
        await self.coordinator.api_client.start_vm(vm.id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the VM."""
        vm = self._vm
        if vm is None:
            return
        _LOGGER.debug("Stopping VM %s (%s)", vm.name, vm.id)
        await self.coordinator.api_client.stop_vm(vm.id)
        await self.coordinator.async_request_refresh()


class UnraidDockerSwitch(CoordinatorEntity["UnraidDataUpdateCoordinator"], SwitchEntity):
    """Represents an Unraid Docker container as a switch."""

    entity_description: UnraidDockerSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidDockerSwitchEntityDescription,
        config_entry: UnraidConfigEntry,
        container_id: str,
    ) -> None:
        """Initialize the Docker container switch."""
        super().__init__(config_entry.runtime_data.coordinator)
        self.entity_description = description
        self._container_id = container_id
        self._attr_unique_id = f"{config_entry.entry_id}_container_switch_{container_id}"
        container_name = self.coordinator.data["containers"][container_id].name
        self._attr_translation_placeholders = {"name": container_name}
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def _container(self) -> DockerContainer | None:
        """Get current container data."""
        return self.coordinator.data["containers"].get(self._container_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._container is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if container is running."""
        container = self._container
        if container is None:
            return None
        return container.state == DockerContainerState.RUNNING

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        return self.entity_description.icon_on

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        container = self._container
        if container is None:
            return None
        return {
            "container_id": container.id,
            "state": container.state.value,
            "image": container.image,
            "status": container.status,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the container."""
        container = self._container
        if container is None:
            return
        _LOGGER.debug("Starting container %s (%s)", container.name, container.id)
        await self.coordinator.api_client.start_container(container.id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the container."""
        container = self._container
        if container is None:
            return
        _LOGGER.debug("Stopping container %s (%s)", container.name, container.id)
        await self.coordinator.api_client.stop_container(container.id)
        await self.coordinator.async_request_refresh()
