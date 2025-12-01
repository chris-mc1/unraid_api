"""Tests init."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.unraid_api.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
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
    *,
    expect_success: bool = True,
) -> MockConfigEntry | bool:
    """
    Do add and setup a MockConfigEntry.

    Args:
        hass: Home Assistant instance
        mocker: GraphQL server mocker
        options: Config entry options
        expect_success: If True (default), returns True on success, False on failure.
                       If False, returns the config entry for state inspection.

    Returns:
        If expect_success is True: Returns True if setup succeeded, False otherwise.
        If expect_success is False: Returns the MockConfigEntry for state inspection.

    """
    entry = add_config_entry(hass, mocker, options)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    if expect_success:
        return entry.state == ConfigEntryState.LOADED
    return entry
