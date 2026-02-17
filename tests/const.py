"""Test Constants."""

from __future__ import annotations

from custom_components.unraid_api.const import (
    CONF_DOCKER_MODE,
    CONF_DRIVES,
    CONF_SHARES,
    DOCKER_MODE_ALL,
    DOCKER_MODE_OFF,
)
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL

DEFAULT_HOST = "http://1.2.3.4"
MOCK_CONFIG_DATA = {CONF_HOST: DEFAULT_HOST, CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False}
MOCK_OPTION_DATA = {CONF_SHARES: True, CONF_DRIVES: True, CONF_DOCKER_MODE: DOCKER_MODE_ALL}
MOCK_OPTION_DATA_DISABLED = {
    CONF_SHARES: False,
    CONF_DRIVES: False,
    CONF_DOCKER_MODE: DOCKER_MODE_OFF,
}
