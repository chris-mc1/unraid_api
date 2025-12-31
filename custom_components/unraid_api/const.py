"""Constants."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "unraid_api"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]

CONF_SHARES: Final[str] = "shares"
CONF_DRIVES: Final[str] = "drives"
CONF_DOCKER: Final[str] = "docker"

# Polling interval configuration keys
CONF_POLL_INTERVAL_METRICS: Final[str] = "poll_interval_metrics"
CONF_POLL_INTERVAL_DISKS: Final[str] = "poll_interval_disks"
CONF_POLL_INTERVAL_SHARES: Final[str] = "poll_interval_shares"
CONF_POLL_INTERVAL_DOCKER: Final[str] = "poll_interval_docker"
CONF_POLL_INTERVAL_UPS: Final[str] = "poll_interval_ups"

# Polling interval options (in seconds)
POLL_INTERVAL_OPTIONS: Final[dict[int, str]] = {
    30: "30 seconds",
    60: "1 minute",
    120: "2 minutes",
    180: "3 minutes",
    300: "5 minutes",
    600: "10 minutes",
    900: "15 minutes",
    1800: "30 minutes",
    3600: "60 minutes",
}

# Default polling intervals (in seconds)
DEFAULT_POLL_INTERVAL_METRICS: Final[int] = 30
DEFAULT_POLL_INTERVAL_DISKS: Final[int] = 60
DEFAULT_POLL_INTERVAL_SHARES: Final[int] = 60
DEFAULT_POLL_INTERVAL_DOCKER: Final[int] = 30
DEFAULT_POLL_INTERVAL_UPS: Final[int] = 60
