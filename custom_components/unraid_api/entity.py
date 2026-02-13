"""Base Entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from awesomeversion import AwesomeVersion
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import UnraidDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import Callable

    from . import UnraidConfigEntry


class UnraidEntityDescription(EntityDescription, frozen_or_thawed=True):
    """Description for Unraid Sensor Entity."""

    min_version: AwesomeVersion = AwesomeVersion("4.20.0")
    available_fn: Callable[[UnraidDataUpdateCoordinator], bool] | None = None


class UnraidBaseEntity(CoordinatorEntity[UnraidDataUpdateCoordinator], Entity):
    """Base Entity."""

    entity_description: UnraidEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidEntityDescription,
        config_entry: UnraidConfigEntry,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}"
        self._attr_translation_key = description.key
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def available(self) -> bool:
        if self.entity_description.available_fn:
            return self.coordinator.last_update_success and self.entity_description.available_fn(
                self.coordinator
            )
        return self.coordinator.last_update_success
