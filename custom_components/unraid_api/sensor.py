"""Unraid Sensors."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfInformation, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DOCKER, CONF_DRIVES, CONF_SHARES, CONF_VMS
from .coordinator import UnraidDataUpdateCoordinator
from .models import Disk, DiskType, DockerContainer, DockerState, Share, VirtualMachine, VmState

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


class UnraidVmSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid VM Sensor Entity."""

    value_fn: Callable[[VirtualMachine], StateType]
    extra_values_fn: Callable[[VirtualMachine], dict[str, Any]] | None = None


class UnraidDockerSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for Unraid Docker Sensor Entity."""

    value_fn: Callable[[DockerContainer], StateType]
    extra_values_fn: Callable[[DockerContainer], dict[str, Any]] | None = None


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


def count_vms_by_state(coordinator: UnraidDataUpdateCoordinator, state: VmState) -> int:
    """Count VMs in a specific state."""
    return sum(1 for vm in coordinator.data["vms"].values() if vm.state == state)


def count_vms_total(coordinator: UnraidDataUpdateCoordinator) -> int:
    """Count total VMs."""
    return len(coordinator.data["vms"])


def count_docker_by_state(coordinator: UnraidDataUpdateCoordinator, state: DockerState) -> int:
    """Count Docker containers in a specific state."""
    return sum(1 for container in coordinator.data["docker"].values() if container.state == state)


def count_docker_total(coordinator: UnraidDataUpdateCoordinator) -> int:
    """Count total Docker containers."""
    return len(coordinator.data["docker"])


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

VM_SENSOR_DESCRIPTIONS: tuple[UnraidVmSensorEntityDescription, ...] = (
    UnraidVmSensorEntityDescription(
        key="vm_state",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda vm: vm.state.value,
        options=[
            "RUNNING",
            "STOPPED",
            "PAUSED",
            "PMSUSPENDED",
            "SHUTTING_DOWN",
            "SHUTDOWN",
            "CRASHED",
        ],
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

DOCKER_SENSOR_DESCRIPTIONS: tuple[UnraidDockerSensorEntityDescription, ...] = (
    UnraidDockerSensorEntityDescription(
        key="docker_state",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda container: container.state.value,
        options=[
            "RUNNING",
            "STOPPED",
            "PAUSED",
            "RESTARTING",
            "CREATED",
            "EXITED",
            "DEAD",
        ],
        entity_category=EntityCategory.DIAGNOSTIC,
        extra_values_fn=lambda container: {
            "image": container.image,
            "autostart": container.autostart,
        },
    ),
)

VM_AGGREGATE_SENSOR_DESCRIPTIONS: tuple[UnraidSensorEntityDescription, ...] = (
    UnraidSensorEntityDescription(
        key="vms_total",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=count_vms_total,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    UnraidSensorEntityDescription(
        key="vms_running",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: count_vms_by_state(coordinator, VmState.RUNNING),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    UnraidSensorEntityDescription(
        key="vms_stopped",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: count_vms_by_state(coordinator, VmState.STOPPED),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    UnraidSensorEntityDescription(
        key="vms_paused",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: count_vms_by_state(coordinator, VmState.PAUSED),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

DOCKER_AGGREGATE_SENSOR_DESCRIPTIONS: tuple[UnraidSensorEntityDescription, ...] = (
    UnraidSensorEntityDescription(
        key="docker_total",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=count_docker_total,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    UnraidSensorEntityDescription(
        key="docker_running",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: count_docker_by_state(coordinator, DockerState.RUNNING),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    UnraidSensorEntityDescription(
        key="docker_stopped",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: count_docker_by_state(coordinator, DockerState.STOPPED),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    UnraidSensorEntityDescription(
        key="docker_paused",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: count_docker_by_state(coordinator, DockerState.PAUSED),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""
    entities = [UnraidSensor(description, config_entry) for description in SENSOR_DESCRIPTIONS]

    # Add VM aggregate sensors if VM monitoring is enabled
    if config_entry.options.get(CONF_VMS, False):
        entities.extend(
            UnraidSensor(description, config_entry)
            for description in VM_AGGREGATE_SENSOR_DESCRIPTIONS
        )

    # Add Docker aggregate sensors if Docker monitoring is enabled
    if config_entry.options.get(CONF_DOCKER, False):
        entities.extend(
            UnraidSensor(description, config_entry)
            for description in DOCKER_AGGREGATE_SENSOR_DESCRIPTIONS
        )

    async_add_entites(entities)

    @callback
    def add_disk_callback(disk: Disk) -> None:
        _LOGGER.debug("Adding new Disk: %s", disk.name)
        entities = [
            UnraidDiskSensor(description, config_entry, disk.id)
            for description in DISK_SENSOR_DESCRIPTIONS
        ]
        if disk.type != DiskType.Parity:
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

    @callback
    def add_vm_callback(vm: VirtualMachine) -> None:
        _LOGGER.debug("Adding new VM: %s", vm.name)
        entities = [
            UnraidVmSensor(description, config_entry, vm.id)
            for description in VM_SENSOR_DESCRIPTIONS
        ]
        async_add_entites(entities)

    @callback
    def add_docker_callback(container: DockerContainer) -> None:
        _LOGGER.debug("Adding new Docker container: %s", container.name)
        entities = [
            UnraidDockerSensor(description, config_entry, container.id)
            for description in DOCKER_SENSOR_DESCRIPTIONS
        ]
        async_add_entites(entities)

    if config_entry.options.get(CONF_DRIVES, True):
        config_entry.runtime_data.coordinator.subscribe_disks(add_disk_callback)
    if config_entry.options.get(CONF_SHARES, True):
        config_entry.runtime_data.coordinator.subscribe_shares(add_share_callback)
    if config_entry.options.get(CONF_VMS, False):
        config_entry.runtime_data.coordinator.subscribe_vms(add_vm_callback)
    if config_entry.options.get(CONF_DOCKER, False):
        config_entry.runtime_data.coordinator.subscribe_docker(add_docker_callback)


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


class UnraidVmSensor(CoordinatorEntity[UnraidDataUpdateCoordinator], SensorEntity):
    """Sensor for Unraid VMs."""

    entity_description: UnraidVmSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidVmSensorEntityDescription,
        config_entry: UnraidConfigEntry,
        vm_id: str,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.vm_id = vm_id
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}-{self.vm_id}"
        self._attr_translation_key = description.key
        self._attr_translation_placeholders = {
            "vm_name": self.coordinator.data["vms"][self.vm_id].name
        }
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def native_value(self) -> StateType:
        try:
            return self.entity_description.value_fn(self.coordinator.data["vms"][self.vm_id])
        except (KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        try:
            if self.entity_description.extra_values_fn:
                return self.entity_description.extra_values_fn(
                    self.coordinator.data["vms"][self.vm_id]
                )
        except (KeyError, AttributeError):
            return None
        return None


class UnraidDockerSensor(CoordinatorEntity[UnraidDataUpdateCoordinator], SensorEntity):
    """Sensor for Unraid Docker containers."""

    entity_description: UnraidDockerSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidDockerSensorEntityDescription,
        config_entry: UnraidConfigEntry,
        container_id: str,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.container_id = container_id
        self.entity_description = description
        self._attr_unique_id = (
            f"{config_entry.entry_id}-{description.key}-{self.container_id}"
        )
        self._attr_translation_key = description.key
        self._attr_translation_placeholders = {
            "container_name": self.coordinator.data["docker"][self.container_id].name
        }
        self._attr_available = False
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def native_value(self) -> StateType:
        try:
            return self.entity_description.value_fn(
                self.coordinator.data["docker"][self.container_id]
            )
        except (KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        try:
            if self.entity_description.extra_values_fn:
                return self.entity_description.extra_values_fn(
                    self.coordinator.data["docker"][self.container_id]
                )
        except (KeyError, AttributeError):
            return None
        return None
