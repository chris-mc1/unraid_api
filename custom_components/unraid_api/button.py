"""Unraid Buttons."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from awesomeversion import AwesomeVersion
from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.unraid_api.api import UnraidAuthError, UnraidGraphQLError
from custom_components.unraid_api.const import DOMAIN

from .coordinator import UnraidDataUpdateCoordinator
from .models import ParityCheckStatus

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import CoroutineType

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import UnraidConfigEntry

PARALLEL_UPDATES = 1
_LOGGER = logging.getLogger(__name__)


class UnraidButtonEntityDescription(ButtonEntityDescription, frozen_or_thawed=True):
    """Description for Unraid Button Entity."""

    min_version: AwesomeVersion = AwesomeVersion("4.20.0")
    call: Callable[[UnraidDataUpdateCoordinator], CoroutineType[Any, Any, None]]
    available_fn: Callable[[UnraidDataUpdateCoordinator], bool]


BUTTON_DESCRIPTIONS = [
    UnraidButtonEntityDescription(
        key="parity_check_start",
        call=lambda coordinator: coordinator.api_client.start_parity_check(),
        available_fn=lambda coordinator: coordinator.data["array"].parity_check_status
        not in (ParityCheckStatus.PAUSED, ParityCheckStatus.RUNNING),
    ),
    UnraidButtonEntityDescription(
        key="parity_check_cancel",
        call=lambda coordinator: coordinator.api_client.cancel_parity_check(),
        available_fn=lambda coordinator: coordinator.data["array"].parity_check_status
        in (ParityCheckStatus.PAUSED, ParityCheckStatus.RUNNING),
    ),
    UnraidButtonEntityDescription(
        key="parity_check_pause",
        call=lambda coordinator: coordinator.api_client.pause_parity_check(),
        available_fn=lambda coordinator: coordinator.data["array"].parity_check_status
        == ParityCheckStatus.RUNNING,
    ),
    UnraidButtonEntityDescription(
        key="parity_check_resume",
        call=lambda coordinator: coordinator.api_client.resume_parity_check(),
        available_fn=lambda coordinator: coordinator.data["array"].parity_check_status
        == ParityCheckStatus.PAUSED,
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


class UnraidButton(CoordinatorEntity[UnraidDataUpdateCoordinator], ButtonEntity):
    """Button for Unraid Server."""

    entity_description: UnraidButtonEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: UnraidButtonEntityDescription,
        config_entry: UnraidConfigEntry,
    ) -> None:
        super().__init__(config_entry.runtime_data.coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}"
        self._attr_translation_key = description.key
        self._attr_device_info = config_entry.runtime_data.device_info

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.entity_description.available_fn(
            self.coordinator
        )

    async def async_press(self) -> None:
        try:
            await self.entity_description.call(self.coordinator)
        except ClientConnectorSSLError as exc:
            _LOGGER.debug("Button: SSL error: %s", str(exc))
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="ssl_error",
                translation_placeholders={"error": str(exc)},
            ) from exc
        except (ClientConnectionError, TimeoutError) as exc:
            _LOGGER.debug("Button: Connection error: %s", str(exc))
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(exc)},
            ) from exc
        except UnraidAuthError as exc:
            _LOGGER.debug("Button: Auth failed")
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
                translation_placeholders={"error_msg": exc.args[0]},
            ) from exc
        except UnraidGraphQLError as exc:
            _LOGGER.debug("Button: GraphQL Error response: %s", exc.response)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="error_response",
                translation_placeholders={"error_msg": exc.args[0]},
            ) from exc
