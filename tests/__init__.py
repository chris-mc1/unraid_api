"""Tests init."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.unraid_api.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def setup_config_entry(
    hass: HomeAssistant,
    data: dict[str, Any],
    options: dict[str, Any],
) -> MockConfigEntry:
    """Do setup of a MockConfigEntry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options=options,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
