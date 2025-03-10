"""Test Constants."""

from __future__ import annotations

from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL

MOCK_CONFIG_DATA = {CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False}
