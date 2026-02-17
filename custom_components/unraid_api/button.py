"""Unraid Buttons."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .entity import UnraidBaseEntity, UnraidEntityDescription
from .helpers import error_handler
from .models import ParityCheckStatus

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import CoroutineType

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import UnraidConfigEntry
    from .coordinator import UnraidDataUpdateCoordinator


PARALLEL_UPDATES = 1


class UnraidButtonEntityDescription(
    UnraidEntityDescription, ButtonEntityDescription, frozen_or_thawed=True
):
    """Description for Unraid Button Entity."""

    call: Callable[[UnraidDataUpdateCoordinator], CoroutineType[Any, Any, None]]
    available_fn: Callable[[UnraidDataUpdateCoordinator], bool]


BUTTON_DESCRIPTIONS = [
    UnraidButtonEntityDescription(
        key="parity_check_start",
        call=lambda coordinator: coordinator.api_client.start_parity_check(),
        available_fn=lambda coordinator: (
            coordinator.data["metrics_array"].parity_check_status
            not in (ParityCheckStatus.PAUSED, ParityCheckStatus.RUNNING)
        ),
    ),
    UnraidButtonEntityDescription(
        key="parity_check_cancel",
        call=lambda coordinator: coordinator.api_client.cancel_parity_check(),
        available_fn=lambda coordinator: (
            coordinator.data["metrics_array"].parity_check_status
            in (ParityCheckStatus.PAUSED, ParityCheckStatus.RUNNING)
        ),
    ),
    UnraidButtonEntityDescription(
        key="parity_check_pause",
        call=lambda coordinator: coordinator.api_client.pause_parity_check(),
        available_fn=lambda coordinator: (
            coordinator.data["metrics_array"].parity_check_status == ParityCheckStatus.RUNNING
        ),
    ),
    UnraidButtonEntityDescription(
        key="parity_check_resume",
        call=lambda coordinator: coordinator.api_client.resume_parity_check(),
        available_fn=lambda coordinator: (
            coordinator.data["metrics_array"].parity_check_status == ParityCheckStatus.PAUSED
        ),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up this integration using config entry."""
    entities = [
        UnraidButton(description, config_entry)
        for description in BUTTON_DESCRIPTIONS
        if description.min_version <= config_entry.runtime_data.coordinator.api_client.version
    ]
    async_add_entites(entities)


class UnraidButton(UnraidBaseEntity, ButtonEntity):
    """Button for Unraid Server."""

    entity_description: UnraidButtonEntityDescription

    @error_handler
    async def async_press(self) -> None:
        await self.entity_description.call(self.coordinator)
