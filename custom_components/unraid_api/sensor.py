"""Unraid Sensors."""

from __future__ import annotations

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
    UnitOfDataRate,
    UnitOfElectricPotential,
    UnitOfInformation,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo

from . import _LOGGER
from .const import CONF_DRIVES, CONF_SHARES, DOMAIN
from .entity import UnraidBaseEntity, UnraidEntityDescription
from .models import Disk, DiskType, DockerContainer, Share, UpsDevice

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from . import UnraidConfigEntry
    from .coordinator import UnraidDataUpdateCoordinator


class UnraidSensorEntityDescription(
    UnraidEntityDescription, SensorEntityDescription, frozen_or_thawed=True
):
    """Description for Unraid Sensor Entity."""

    value_fn: Callable[[UnraidDataUpdateCoordinator], StateType]
    extra_values_fn: Callable[[UnraidDataUpdateCoordinator], dict[str, Any]] | None = None


class UnraidDiskSensorEntityDescription(
    UnraidEntityDescription, SensorEntityDescription, frozen_or_thawed=True
):
    """Description for Unraid Disk Sensor Entity."""

    value_fn: Callable[[Disk], StateType]
    extra_values_fn: Callable[[Disk], dict[str, Any]] | None = None


class UnraidShareSensorEntityDescription(
    UnraidEntityDescription, SensorEntityDescription, frozen_or_thawed=True
):
    """Description for Unraid Share Sensor Entity."""

    value_fn: Callable[[Share], StateType]
    extra_values_fn: Callable[[Share], dict[str, Any]] | None = None


class UnraidUpsSensorEntityDescription(
    UnraidEntityDescription, SensorEntityDescription, frozen_or_thawed=True
):
    """Description for Unraid UPS Sensor Entity."""

    min_version: AwesomeVersion = AwesomeVersion("4.26.0")
    value_fn: Callable[[UpsDevice], StateType]


class UnraidDockerSensorEntityDescription(
    UnraidEntityDescription, SensorEntityDescription, frozen_or_thawed=True
):
    """Description for Unraid Docker Sensor Entity."""

    value_fn: Callable[[DockerContainer], StateType]
    extra_values_fn: Callable[[DockerContainer], dict[str, Any]] | None = None


def calc_array_usage_percentage(coordinator: UnraidDataUpdateCoordinator) -> StateType:
    """Calculate the array usage percentage."""
    used = coordinator.data["metrics_array"].capacity_used
    total = coordinator.data["metrics_array"].capacity_total
    if used is None or total is None or total == 0:
        return None
    return (used / total) * 100


def calc_disk_usage_percentage(disk: Disk) -> StateType:
    """Calculate the disk usage percentage."""
    if disk.fs_used is None or disk.fs_size is None or disk.fs_size == 0:
        return None
    return (disk.fs_used / disk.fs_size) * 100


SENSOR_DESCRIPTIONS: tuple[UnraidSensorEntityDescription, ...] = (
    UnraidSensorEntityDescription(
        key="array_state",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda coordinator: coordinator.data["metrics_array"].state.lower(),
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
            "used": coordinator.data["metrics_array"].capacity_used,
            "free": coordinator.data["metrics_array"].capacity_free,
            "total": coordinator.data["metrics_array"].capacity_total,
        },
    ),
    UnraidSensorEntityDescription(
        key="array_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics_array"].capacity_free,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="array_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["metrics_array"].capacity_used,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="ram_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["memory"].percent_total,
        extra_values_fn=lambda coordinator: {
            "used": coordinator.data["memory"].active,
            "free": coordinator.data["memory"].available,
            "total": coordinator.data["memory"].total,
        },
    ),
    UnraidSensorEntityDescription(
        key="ram_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["memory"].active,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="ram_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["memory"].available,
        entity_registry_enabled_default=False,
    ),
    UnraidSensorEntityDescription(
        key="cpu_utilization",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["cpu_usage"],
    ),
    UnraidSensorEntityDescription(
        key="cpu_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["cpu_metrics"].temp,
        min_version=AwesomeVersion("4.26.0"),
    ),
    UnraidSensorEntityDescription(
        key="cpu_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda coordinator: coordinator.data["cpu_metrics"].power,
        min_version=AwesomeVersion("4.26.0"),
    ),
    UnraidSensorEntityDescription(
        key="parity_check_status",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda coordinator: coordinator.data["metrics_array"].parity_check_status.lower(),
        options=[
            "never_run",
            "running",
            "paused",
            "completed",
            "cancelled",
            "failed",
        ],
    ),
    UnraidSensorEntityDescription(
        key="parity_check_date",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda coordinator: coordinator.data["metrics_array"].parity_check_date,
    ),
    UnraidSensorEntityDescription(
        key="parity_check_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda coordinator: coordinator.data["metrics_array"].parity_check_duration,
    ),
    UnraidSensorEntityDescription(
        key="parity_check_speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        value_fn=lambda coordinator: coordinator.data["metrics_array"].parity_check_speed,
    ),
    UnraidSensorEntityDescription(
        key="parity_check_errors",
        value_fn=lambda coordinator: coordinator.data["metrics_array"].parity_check_errors,
    ),
    UnraidSensorEntityDescription(
        key="parity_check_progress",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda coordinator: coordinator.data["metrics_array"].parity_check_progress,
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
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
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

UPS_SENSOR_DESCRIPTIONS: tuple[UnraidUpsSensorEntityDescription, ...] = (
    UnraidUpsSensorEntityDescription(
        key="ups_status",
        value_fn=lambda device: device.status,
    ),
    UnraidUpsSensorEntityDescription(
        key="ups_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.battery_level,
    ),
    UnraidUpsSensorEntityDescription(
        key="ups_runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda device: device.battery_runtime,
    ),
    UnraidUpsSensorEntityDescription(
        key="ups_health",
        value_fn=lambda device: device.battery_health,
    ),
    UnraidUpsSensorEntityDescription(
        key="ups_load",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.load_percentage,
    ),
    UnraidUpsSensorEntityDescription(
        key="ups_input_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda device: device.input_voltage,
    ),
    UnraidUpsSensorEntityDescription(
        key="ups_output_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda device: device.output_voltage,
    ),
)
DOCKER_SENSOR_DESCRIPTIONS: tuple[UnraidDockerSensorEntityDescription, ...] = (
    UnraidDockerSensorEntityDescription(
        key="docker_state",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda container: container.state.lower(),
        options=["running", "exited"],
        extra_values_fn=lambda container: {
            "status": container.status,
            "image": container.image,
            "sha265": container.image_sha256,
            "version": container.label_opencontainers_version,
        },
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
        _LOGGER.debug("Sensor: Adding new Disk: %s", disk.name)
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
        _LOGGER.debug("Sensor: Adding new Share: %s", share.name)
        entities = [
            UnraidShareSensor(description, config_entry, share.name)
            for description in SHARE_SENSOR_DESCRIPTIONS
            if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
        ]
        async_add_entites(entities)

    @callback
    def add_ups_callback(device: UpsDevice) -> None:
        _LOGGER.debug("Sensor: Adding new UPS: %s", device.name)
        device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.entry_id}_{device.id}")},
            name=device.name,
            model=device.model,
            via_device=(DOMAIN, config_entry.entry_id),
        )
        entities = [
            UnraidUpsSensor(description, config_entry, device.id, device_info)
            for description in UPS_SENSOR_DESCRIPTIONS
            if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
        ]
        async_add_entites(entities)

    @callback
    def add_container_callback(container_name: str) -> None:
        _LOGGER.debug("Sensor: Adding new Docker container: %s", container_name)
        entities = [
            UnraidDockerSensor(description, config_entry, container_name)
            for description in DOCKER_SENSOR_DESCRIPTIONS
            if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
        ]
        config_entry.runtime_data.containers[container_name]["entities"].extend(entities)
        async_add_entites(entities)

    if config_entry.options[CONF_DRIVES]:
        config_entry.runtime_data.coordinator.subscribe_disks(add_disk_callback)
    if config_entry.options[CONF_SHARES]:
        config_entry.runtime_data.coordinator.subscribe_shares(add_share_callback)
    config_entry.runtime_data.coordinator.subscribe_ups(add_ups_callback)
    config_entry.runtime_data.coordinator.subscribe_docker(add_container_callback)


class UnraidSensor(UnraidBaseEntity, SensorEntity):
    """Sensor for Unraid Server."""

    entity_description: UnraidSensorEntityDescription
    _attr_has_entity_name = True

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


class UnraidDiskSensor(UnraidBaseEntity, SensorEntity):
    """Sensor for Unraid Disks."""

    entity_description: UnraidDiskSensorEntityDescription

    def __init__(
        self,
        description: UnraidDiskSensorEntityDescription,
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


class UnraidShareSensor(UnraidBaseEntity, SensorEntity):
    """Sensor for Unraid Shares."""

    entity_description: UnraidShareSensorEntityDescription

    def __init__(
        self,
        description: UnraidShareSensorEntityDescription,
        config_entry: UnraidConfigEntry,
        share_name: str,
    ) -> None:
        super().__init__(description, config_entry)
        self.share_name = share_name
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.share_name}"
        self._attr_translation_placeholders = {"share_name": self.share_name}

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


class UnraidUpsSensor(UnraidBaseEntity, SensorEntity):
    """Sensor for Unraid UPS."""

    entity_description: UnraidUpsSensorEntityDescription

    def __init__(
        self,
        description: UnraidUpsSensorEntityDescription,
        config_entry: UnraidConfigEntry,
        ups_id: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(description, config_entry)
        self.ups_id = ups_id
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.ups_id}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> StateType:
        try:
            return self.entity_description.value_fn(
                self.coordinator.data["ups_devices"][self.ups_id]
            )
        except (KeyError, AttributeError):
            return None

    @property
    def available(self) -> bool:
        return (
            self.ups_id in self.coordinator.data["ups_devices"]
            and self.coordinator.last_update_success
        )


class UnraidDockerSensor(UnraidBaseEntity, SensorEntity):
    """Sensor for Docker containers."""

    entity_description: UnraidDockerSensorEntityDescription

    def __init__(
        self,
        description: UnraidDockerSensorEntityDescription,
        config_entry: UnraidConfigEntry,
        container_name: str,
    ) -> None:
        super().__init__(description, config_entry)
        self.container_name = container_name
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.container_name}"
        self._attr_device_info = config_entry.runtime_data.containers[container_name]["device_info"]

    @property
    def native_value(self) -> StateType:
        try:
            return self.entity_description.value_fn(
                self.coordinator.data["docker_containers"][self.container_name]
            )
        except (KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        try:
            if self.entity_description.extra_values_fn:
                return self.entity_description.extra_values_fn(
                    self.coordinator.data["docker_containers"][self.container_name]
                )
        except (KeyError, AttributeError):
            return None
        return None

    @property
    def available(self) -> bool:
        return (
            self.container_name in self.coordinator.data["docker_containers"]
            and self.coordinator.last_update_success
        )
