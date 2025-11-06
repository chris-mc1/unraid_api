"""Unraid Buttons."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity, ButtonEntityDescription
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DOCKER, CONF_VMS
from .coordinator import UnraidDataUpdateCoordinator
from .models import DockerContainer, VirtualMachine

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import UnraidConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class UnraidVmButtonEntityDescription(ButtonEntityDescription):
    """Description for Unraid VM Button Entity."""

    action: str


@dataclass(frozen=True, kw_only=True)
class UnraidDockerButtonEntityDescription(ButtonEntityDescription):
    """Description for Unraid Docker Button Entity."""

    action: str


VM_BUTTON_DESCRIPTIONS: tuple[UnraidVmButtonEntityDescription, ...] = (
    UnraidVmButtonEntityDescription(
        key="vm_reboot",
        translation_key="vm_reboot",
        device_class=ButtonDeviceClass.RESTART,
        action="reboot",
    ),
    UnraidVmButtonEntityDescription(
        key="vm_force_stop",
        translation_key="vm_force_stop",
        action="force_stop",
    ),
    UnraidVmButtonEntityDescription(
        key="vm_pause",
        translation_key="vm_pause",
        action="pause",
    ),
    UnraidVmButtonEntityDescription(
        key="vm_resume",
        translation_key="vm_resume",
        action="resume",
    ),
)

# Docker only supports start/stop actions via the switch
# No additional button actions are available
DOCKER_BUTTON_DESCRIPTIONS: tuple[UnraidDockerButtonEntityDescription, ...] = ()


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""

    @callback
    def add_vm_callback(vm: VirtualMachine) -> None:
        _LOGGER.debug("Adding VM buttons: %s", vm.name)
        entities = [
            UnraidVmButton(config_entry, description, vm.id)
            for description in VM_BUTTON_DESCRIPTIONS
        ]
        async_add_entities(entities)

    @callback
    def add_docker_callback(container: DockerContainer) -> None:
        _LOGGER.debug("Adding Docker buttons: %s", container.name)
        entities = [
            UnraidDockerButton(config_entry, description, container.id)
            for description in DOCKER_BUTTON_DESCRIPTIONS
        ]
        async_add_entities(entities)

    if config_entry.options.get(CONF_VMS, False):
        config_entry.runtime_data.coordinator.subscribe_vms(add_vm_callback)
    if config_entry.options.get(CONF_DOCKER, False):
        config_entry.runtime_data.coordinator.subscribe_docker(add_docker_callback)


class UnraidVmButton(CoordinatorEntity[UnraidDataUpdateCoordinator], ButtonEntity):
    """Button for Unraid VM actions."""

    entity_description: UnraidVmButtonEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: UnraidConfigEntry,
        description: UnraidVmButtonEntityDescription,
        vm_id: str,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.vm_id = vm_id
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.vm_id}"
        self._attr_translation_key = description.translation_key
        self._attr_translation_placeholders = {
            "vm_name": self.coordinator.data["vms"][self.vm_id].name
        }
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_vm_action(self.vm_id, self.entity_description.action)


class UnraidDockerButton(CoordinatorEntity[UnraidDataUpdateCoordinator], ButtonEntity):
    """Button for Unraid Docker container actions."""

    entity_description: UnraidDockerButtonEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: UnraidConfigEntry,
        description: UnraidDockerButtonEntityDescription,
        container_id: str,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.container_id = container_id
        self.entity_description = description
        self._attr_unique_id = (
            f"{config_entry.entry_id}-{description.key}-{self.container_id}"
        )
        self._attr_translation_key = description.translation_key
        self._attr_translation_placeholders = {
            "container_name": self.coordinator.data["docker"][self.container_id].name
        }
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_docker_action(
            self.container_id, self.entity_description.action
        )
