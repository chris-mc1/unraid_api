"""The Unraid Homeassistant integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@dataclass
class UnraidData:
    """Dataclass for runtime data."""


type UnraidConfigEntry = ConfigEntry[UnraidData]


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: UnraidConfigEntry,  # noqa: ARG001
) -> bool:
    """Set up this integration using config entry."""
    return False
