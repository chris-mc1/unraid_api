"""Tests init."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.unraid_api.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import DEFAULT_HOST, MOCK_OPTION_DATA

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from tests.conftest import GraphqlServerMocker


def add_config_entry(
    hass: HomeAssistant,
    mocker: GraphqlServerMocker | None = None,
    options: dict[str, Any] | None = None,
) -> MockConfigEntry:
    """Add a MockConfigEntry."""
    if options is None:
        options = MOCK_OPTION_DATA

    host = DEFAULT_HOST if mocker is None else mocker.host

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: host,
            CONF_API_KEY: "test_key",
            CONF_VERIFY_SSL: False,
        },
        options=options,
    )
    entry.add_to_hass(hass)
    return entry


async def setup_config_entry(
    hass: HomeAssistant,
    mocker: GraphqlServerMocker | None = None,
    options: dict[str, Any] | None = None,
) -> MockConfigEntry:
    """Do add and setup a MockConfigEntry."""
    entry = add_config_entry(hass, mocker, options)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
