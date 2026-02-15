"""Unraid Binary Sensors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import callback

from . import _LOGGER
from .const import CONF_DRIVES
from .entity import UnraidBaseEntity, UnraidEntityDescription

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import UnraidConfigEntry
    from .models import Disk


class UnraidDiskBinarySensorEntityDescription(
    UnraidEntityDescription, BinarySensorEntityDescription, frozen_or_thawed=True
):
    """Description for Unraid Binary Sensor Entity."""

    value_fn: Callable[[Disk], bool]
    extra_values_fn: Callable[[Disk], dict[str, Any]] | None = None


DISK_BINARY_SENSOR_DESCRIPTIONS: tuple[UnraidDiskBinarySensorEntityDescription, ...] = (
    UnraidDiskBinarySensorEntityDescription(
        key="disk_spinning",
        device_class=BinarySensorDeviceClass.MOVING,
        value_fn=lambda disk: disk.is_spinning,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""

    @callback
    def add_disk_callback(disk: Disk) -> None:
        _LOGGER.debug("Binary Sensor: Adding new disk: %s", disk.name)
        entities = [
            UnraidDiskBinarySensorEntity(description, config_entry, disk.id)
            for description in DISK_BINARY_SENSOR_DESCRIPTIONS
            if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
        ]
        async_add_entites(entities)

    if config_entry.options[CONF_DRIVES]:
        config_entry.runtime_data.coordinator.subscribe_disks(add_disk_callback)


class UnraidDiskBinarySensorEntity(UnraidBaseEntity, BinarySensorEntity):
    """Binary Sensor for Unraid Disks."""

    entity_description: UnraidDiskBinarySensorEntityDescription

    def __init__(
        self,
        description: UnraidDiskBinarySensorEntityDescription,
        config_entry: UnraidConfigEntry,
        disk_id: str,
    ) -> None:
        super().__init__(description, config_entry)
        self.disk_id = disk_id
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.disk_id}"
        self._attr_translation_placeholders = {
            "disk_name": self.coordinator.data["disks"][self.disk_id].name
        }

    @property
    def is_on(self) -> bool | None:
        try:
            return self.entity_description.value_fn(self.coordinator.data["disks"][self.disk_id])
        except (KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        try:
            if self.entity_description.extra_values_fn:
                return self.entity_description.extra_values_fn(
                    self.coordinator.data["disks"][self.disk_id]
                )
        except (KeyError, AttributeError):
            return None
        return None
