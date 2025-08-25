"""The Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfInformation, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DRIVES, CONF_SHARES
from .coordinator import UnraidDataUpdateCoordinator
from .models import ArrayDiskType, Disk, Share

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from . import UnraidConfigEntry

_LOGGER = logging.getLogger(__name__)


class UnraidSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid Sensor Entity."""

    value_fn: Callable[[UnraidDataUpdateCoordinator], StateType]
    extra_values_fn: Callable[[UnraidDataUpdateCoordinator], dict[str, Any]] | None = None


class UnraidDiskSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid Disk Sensor Entity."""

    value_fn: Callable[[Disk], StateType]
    extra_values_fn: Callable[[Disk], dict[str, Any]] | None = None


class UnraidShareSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid Share Sensor Entity."""

    value_fn: Callable[[Share], StateType]
    extra_values_fn: Callable[[Share], dict[str, Any]] | None = None


def calc_array_usage_percentage(coordinator: UnraidDataUpdateCoordinator) -> StateType:
    """Calculate the array usage percentage."""
    used = coordinator.data["array"].array.capacity.kilobytes.used
    total = coordinator.data["array"].array.capacity.kilobytes.total
    return (used / total) * 100


def calc_disk_usage_percentage(disk: Disk) -> StateType:
    """Calculate the disk usage percentage."""
    return (disk.fs_used / disk.fs_size) * 100


SENSOR_DESCRIPTIONS: tuple[UnraidSensorEntityDescription, ...] = (
    UnraidSensorEntityDescription(
        key="array_state",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda coordinator: coordinator.data["array"].array.state.value.lower(),
        options=[
            "started",
            "stopped",
            "new_array",
            "recon_disk",
            "disable_disk",
            "swap_dsbl",
            "invalid_expansion",
            "parity_not_biggest",
            "too_many_missing_disks",
            "new_disk_too_small",
            "no_data_disks",
        ],
    ),
    UnraidSensorEntityDescription(
        key="array_usage",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=2,
        value_fn=calc_array_usage_percentage,
        extra_values_fn=lambda coordinator: {
            "used": coordinator.data["array"].array.capacity.kilobytes.used,
            "free": coordinator.data["array"].array.capacity.kilobytes.free,
            "total": coordinator.data["array"].array.capacity.kilobytes.total,
        },
    ),
    UnraidSensorEntityDescription(
        key="array_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["array"].array.capacity.kilobytes.free,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="array_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["array"].array.capacity.kilobytes.used,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="ram_usage",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].memory.percent_total,
        extra_values_fn=lambda coordinator: {
            "used": coordinator.data["metrics"].memory.active,
            "free": coordinator.data["metrics"].memory.free,
            "total": coordinator.data["metrics"].memory.total,
        },
    ),
    UnraidSensorEntityDescription(
        key="ram_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].memory.active,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="ram_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].memory.free,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="cpu_utilization",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].cpu.percent_total,
    ),
)

DISK_SENSOR_DESCRIPTIONS: tuple[UnraidDiskSensorEntityDescription, ...] = (
    UnraidDiskSensorEntityDescription(
        key="disk_status",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda disk: disk.status.value.lower(),
        options=[
            "disk_np",
            "disk_ok",
            "disk_np_missing",
            "disk_invalid",
            "disk_wrong",
            "disk_dsbl",
            "disk_np_dsbl",
            "disk_dsbl_new",
            "disk_new",
        ],
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    UnraidDiskSensorEntityDescription(
        key="disk_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda disk: disk.temp,
    ),
)

DISK_SENSOR_SPACE_DESCRIPTIONS: tuple[UnraidDiskSensorEntityDescription, ...] = (
    UnraidDiskSensorEntityDescription(
        key="disk_usage",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=2,
        value_fn=calc_disk_usage_percentage,
    ),
    UnraidDiskSensorEntityDescription(
        key="disk_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda disk: disk.fs_free,
        entity_registry_enabled_default=False,
    ),
    UnraidDiskSensorEntityDescription(
        key="disk_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda disk: disk.fs_used,
        entity_registry_enabled_default=False,
    ),
)

SHARE_SENSOR_DESCRIPTIONS: tuple[UnraidShareSensorEntityDescription, ...] = (
    UnraidShareSensorEntityDescription(
        key="share_free",
        name="free space",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda share: share.free,
        extra_values_fn=lambda share: {
            "used": share.used,
            "total": share.size,
            "allocator": share.allocator,
            "floor": share.floor,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""
    entities = [UnraidSensor(description, config_entry) for description in SENSOR_DESCRIPTIONS]
    async_add_entites(entities)

    @callback
    def add_disk_callback(disk: Disk) -> None:
        _LOGGER.debug("Adding new Disk: %s", disk.name)
        entities = [
            UnraidDiskSensor(description, config_entry, disk.id)
            for description in DISK_SENSOR_DESCRIPTIONS
        ]
        if disk.type != ArrayDiskType.Parity:
            entities.extend(
                UnraidDiskSensor(description, config_entry, disk.id)
                for description in DISK_SENSOR_SPACE_DESCRIPTIONS
            )
        async_add_entites(entities)

    @callback
    def add_share_callback(share: Share) -> None:
        _LOGGER.debug("Adding new Share: %s", share.name)
        entities = [
            UnraidShareSensor(description, config_entry, share.name)
            for description in SHARE_SENSOR_DESCRIPTIONS
        ]
        async_add_entites(entities)

    if config_entry.options[CONF_DRIVES]:
        config_entry.runtime_data.coordinator.subscribe_disks(add_disk_callback)
    if config_entry.options[CONF_SHARES]:
        config_entry.runtime_data.coordinator.subscribe_shares(add_share_callback)


class UnraidSensor(CoordinatorEntity[UnraidDataUpdateCoordinator], SensorEntity):
    """Sensor for Unraid Server."""

    entity_description: UnraidSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidSensorEntityDescription,
        config_entry: UnraidConfigEntry,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}"
        self._attr_translation_key = description.key
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.extra_values_fn:
            return self.entity_description.extra_values_fn(self.coordinator)
        return None


class UnraidDiskSensor(CoordinatorEntity[UnraidDataUpdateCoordinator], SensorEntity):
    """Sensor for Unraid Disks."""

    entity_description: UnraidDiskSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidDiskSensorEntityDescription,
        config_entry: UnraidConfigEntry,
        disk_id: str,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.disk_id = disk_id
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.disk_id}"
        self._attr_translation_key = description.key
        self._attr_translation_placeholders = {
            "disk_name": self.coordinator.data["disks"][self.disk_id].name
        }
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data["disks"][self.disk_id])

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.extra_values_fn:
            return self.entity_description.extra_values_fn(
                self.coordinator.data["disks"][self.disk_id]
            )
        return None


class UnraidShareSensor(CoordinatorEntity[UnraidDataUpdateCoordinator], SensorEntity):
    """Sensor for Unraid Shares."""

    entity_description: UnraidShareSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidShareSensorEntityDescription,
        config_entry: UnraidConfigEntry,
        share_name: str,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.share_name = share_name
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.share_name}"
        self._attr_translation_key = description.key
        self._attr_translation_placeholders = {"share_name": self.share_name}
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data["shares"][self.share_name])

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.extra_values_fn:
            return self.entity_description.extra_values_fn(
                self.coordinator.data["shares"][self.share_name]
            )
        return None
