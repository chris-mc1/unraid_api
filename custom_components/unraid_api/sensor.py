"""Unraid Sensors."""

from __future__ import annotations

import contextlib
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from awesomeversion import AwesomeVersion
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfInformation,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DRIVES, CONF_SHARES
from .coordinator import UnraidDataUpdateCoordinator
from .models import Disk, DiskType, Share, UPSDevice

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from . import UnraidConfigEntry

_LOGGER = logging.getLogger(__name__)


class UnraidSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid Sensor Entity."""

    min_version: AwesomeVersion = AwesomeVersion("4.20.0")
    value_fn: Callable[[UnraidDataUpdateCoordinator], StateType]
    extra_values_fn: Callable[[UnraidDataUpdateCoordinator], dict[str, Any]] | None = None


class UnraidDiskSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid Disk Sensor Entity."""

    min_version: AwesomeVersion = AwesomeVersion("4.20.0")
    value_fn: Callable[[Disk], StateType]
    extra_values_fn: Callable[[Disk], dict[str, Any]] | None = None


class UnraidShareSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid Share Sensor Entity."""

    min_version: AwesomeVersion = AwesomeVersion("4.20.0")
    value_fn: Callable[[Share], StateType]
    extra_values_fn: Callable[[Share], dict[str, Any]] | None = None


class UnraidUPSSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid UPS Sensor Entity."""

    min_version: AwesomeVersion = AwesomeVersion("4.20.0")
    value_fn: Callable[[UPSDevice], StateType]
    extra_values_fn: Callable[[UPSDevice], dict[str, Any]] | None = None


def calc_array_usage_percentage(coordinator: UnraidDataUpdateCoordinator) -> StateType:
    """Calculate the array usage percentage."""
    used = coordinator.data["array"].capacity_used
    total = coordinator.data["array"].capacity_total
    return (used / total) * 100


def calc_disk_usage_percentage(disk: Disk) -> StateType:
    """Calculate the disk usage percentage."""
    if disk.fs_used is None or disk.fs_size is None or disk.fs_size == 0:
        return None
    return (disk.fs_used / disk.fs_size) * 100


def format_uptime(coordinator: UnraidDataUpdateCoordinator) -> str | None:
    """Format uptime as human-readable string."""
    uptime_since = coordinator.data.get("uptime_since")
    if not uptime_since:
        return None

    try:
        # Parse ISO timestamp
        start_time = datetime.fromisoformat(uptime_since)
        now = datetime.now(UTC)
        delta = now - start_time
        total_seconds = int(delta.total_seconds())

        if total_seconds < 0:
            return None

        # Calculate components
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 or not parts:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        return ", ".join(parts)
    except (ValueError, TypeError):
        return None


SENSOR_DESCRIPTIONS: tuple[UnraidSensorEntityDescription, ...] = (
    UnraidSensorEntityDescription(
        key="array_state",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda coordinator: coordinator.data["array"].state.lower(),
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
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=calc_array_usage_percentage,
        extra_values_fn=lambda coordinator: {
            "used": coordinator.data["array"].capacity_used,
            "free": coordinator.data["array"].capacity_free,
            "total": coordinator.data["array"].capacity_total,
        },
    ),
    UnraidSensorEntityDescription(
        key="array_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["array"].capacity_free,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="array_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["array"].capacity_used,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="ram_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].memory_percent_total,
        extra_values_fn=lambda coordinator: {
            "used": coordinator.data["metrics"].memory_active,
            "free": coordinator.data["metrics"].memory_free,
            "total": coordinator.data["metrics"].memory_total,
            "available": coordinator.data["metrics"].memory_available,
        },
    ),
    UnraidSensorEntityDescription(
        key="ram_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].memory_active,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="ram_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].memory_free,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="cpu_utilization",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].cpu_percent_total,
    ),
    UnraidSensorEntityDescription(
        key="cpu_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].cpu_temp,
    ),
    UnraidSensorEntityDescription(
        key="cpu_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics"].cpu_power,
    ),
    UnraidSensorEntityDescription(
        key="uptime",
        value_fn=format_uptime,
        extra_values_fn=lambda coordinator: {
            "uptime_since": coordinator.data.get("uptime_since"),
        },
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
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda disk: disk.temp,
    ),
)

DISK_SENSOR_SPACE_DESCRIPTIONS: tuple[UnraidDiskSensorEntityDescription, ...] = (
    UnraidDiskSensorEntityDescription(
        key="disk_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=calc_disk_usage_percentage,
        extra_values_fn=lambda disk: {
            "free": disk.fs_free,
            "used": disk.fs_used,
            "total": disk.fs_size,
        },
    ),
    UnraidDiskSensorEntityDescription(
        key="disk_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda disk: disk.fs_free,
        entity_registry_enabled_default=False,
    ),
    UnraidDiskSensorEntityDescription(
        key="disk_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
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
        state_class=SensorStateClass.MEASUREMENT,
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


UPS_SENSOR_DESCRIPTIONS: tuple[UnraidUPSSensorEntityDescription, ...] = (
    UnraidUPSSensorEntityDescription(
        key="ups_battery",
        translation_key="ups_battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda ups: ups.battery_charge,
    ),
    UnraidUPSSensorEntityDescription(
        key="ups_load",
        translation_key="ups_load",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda ups: ups.load_percentage,
    ),
    UnraidUPSSensorEntityDescription(
        key="ups_runtime",
        translation_key="ups_runtime",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        value_fn=lambda ups: ups.battery_runtime,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""
    entities = [
        UnraidSensor(description, config_entry)
        for description in SENSOR_DESCRIPTIONS
        if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
    ]
    async_add_entites(entities)

    @callback
    def add_disk_callback(disk: Disk) -> None:
        _LOGGER.debug("Adding new Disk: %s", disk.name)
        entities = [
            UnraidDiskSensor(description, config_entry, disk.id)
            for description in DISK_SENSOR_DESCRIPTIONS
            if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
        ]
        if disk.type != DiskType.Parity:
            entities.extend(
                UnraidDiskSensor(description, config_entry, disk.id)
                for description in DISK_SENSOR_SPACE_DESCRIPTIONS
                if description.min_version
                <= config_entry.runtime_data.coordinator.api_client.version
            )
        async_add_entites(entities)

    @callback
    def add_share_callback(share: Share) -> None:
        _LOGGER.debug("Adding new Share: %s", share.name)
        entities = [
            UnraidShareSensor(description, config_entry, share.name)
            for description in SHARE_SENSOR_DESCRIPTIONS
            if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
        ]
        async_add_entites(entities)

    if config_entry.options[CONF_DRIVES]:
        config_entry.runtime_data.coordinator.subscribe_disks(add_disk_callback)
    if config_entry.options[CONF_SHARES]:
        config_entry.runtime_data.coordinator.subscribe_shares(add_share_callback)

    # Add UPS sensors if UPS devices are detected
    coordinator = config_entry.runtime_data.coordinator
    if coordinator.data["ups_devices"]:
        _LOGGER.debug("Adding UPS sensors")
        ups_entities: list[SensorEntity] = [
            UnraidUPSSensor(description, config_entry)
            for description in UPS_SENSOR_DESCRIPTIONS
            if description.min_version <= coordinator.api_client.version
        ]
        async_add_entites(ups_entities)


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
        try:
            return self.entity_description.value_fn(self.coordinator)
        except (KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        try:
            if self.entity_description.extra_values_fn:
                return self.entity_description.extra_values_fn(self.coordinator)
        except (KeyError, AttributeError):
            return None
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
        try:
            return self.entity_description.value_fn(
                self.coordinator.data["shares"][self.share_name]
            )
        except (KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        try:
            if self.entity_description.extra_values_fn:
                return self.entity_description.extra_values_fn(
                    self.coordinator.data["shares"][self.share_name]
                )
        except (KeyError, AttributeError):
            return None
        return None


class UnraidUPSSensor(CoordinatorEntity[UnraidDataUpdateCoordinator], SensorEntity):
    """Sensor for Unraid UPS."""

    entity_description: UnraidUPSSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidUPSSensorEntityDescription,
        config_entry: UnraidConfigEntry,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}"
        self._attr_translation_key = description.translation_key
        self._attr_device_info = config_entry.runtime_data.device_info

    def _get_ups(self) -> UPSDevice | None:
        """Get first UPS device from coordinator data."""
        ups_devices = self.coordinator.data["ups_devices"]
        return ups_devices[0] if ups_devices else None

    @property
    def native_value(self) -> StateType:
        """Return sensor value."""
        ups = self._get_ups()
        if ups:
            try:
                return self.entity_description.value_fn(ups)
            except (KeyError, AttributeError):
                return None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        ups = self._get_ups()
        if not ups:
            return None

        attrs: dict[str, Any] = {
            "ups_model": ups.model,
            "ups_status": ups.status.value,
        }

        if self.entity_description.extra_values_fn:
            with contextlib.suppress(KeyError, AttributeError):
                attrs.update(self.entity_description.extra_values_fn(ups))

        return attrs
