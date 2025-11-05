"""Constants."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "unraid_api"
PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]

CONF_SHARES: Final[str] = "shares"
CONF_DRIVES: Final[str] = "drives"
CONF_VMS: Final[str] = "vms"
CONF_DOCKER: Final[str] = "docker"
