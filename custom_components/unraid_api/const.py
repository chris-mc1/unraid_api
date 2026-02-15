"""Constants."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "unraid_api"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

CONF_SHARES: Final[str] = "shares"
CONF_DRIVES: Final[str] = "drives"
CONF_DOCKER_MODE: Final[str] = "docker_mode"

DOCKER_MODE_ALL: Final[str] = "all"
DOCKER_MODE_OFF: Final[str] = "off"
DOCKER_MODE_EXCEPT_DISABLED: Final[str] = "except_disabled"
DOCKER_MODE_ENABLED_ONLY: Final[str] = "enabled_only"
