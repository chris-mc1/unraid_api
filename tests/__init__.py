"""Tests init."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.unraid_api.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import DEFAULT_HOST, MOCK_OPTION_DATA

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def add_config_entry(
    hass: HomeAssistant,
    options: dict[str, Any] | None = None,
) -> MockConfigEntry:
    """Add a MockConfigEntry."""
    if options is None:
        options = MOCK_OPTION_DATA

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: DEFAULT_HOST,
            CONF_API_KEY: "test_key",
            CONF_VERIFY_SSL: False,
        },
        options=options,
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    return entry


async def setup_config_entry(
    hass: HomeAssistant,
    options: dict[str, Any] | None = None,
) -> MockConfigEntry:
    """Do add and setup a MockConfigEntry."""
    entry = add_config_entry(hass, options)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
