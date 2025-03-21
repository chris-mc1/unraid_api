"""Test Constants."""

from __future__ import annotations

from custom_components.unraid_hass.const import CONF_DRIVES, CONF_SHARES
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL

MOCK_CONFIG_DATA = {CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False}
MOCK_OPTION_DATA = {CONF_SHARES: True, CONF_DRIVES: True}
API_RESPONSE = {
    "data": {
        "server": {"localurl": "http://1.2.3.4", "name": "Test Server"},
        "array": {
            "state": "STARTED",
            "disks": [
                {
                    "name": "disk1",
                    "status": "DISK_OK",
                    "temp": 34,
                    "fsSize": 5999038075,
                    "fsFree": 464583438,
                    "fsUsed": 5534454637,
                    "type": "Data",
                    "id": "c6b",
                },
            ],
            "parities": [
                {
                    "name": "parity",
                    "status": "DISK_OK",
                    "temp": None,
                    "fsSize": None,
                    "fsFree": None,
                    "fsUsed": None,
                    "type": "Parity",
                    "id": "4d5",
                }
            ],
            "caches": [
                {
                    "name": "cache",
                    "status": "DISK_OK",
                    "temp": 30,
                    "fsSize": 119949189,
                    "fsFree": 38907683,
                    "fsUsed": 81041506,
                    "type": "Cache",
                    "id": "8e0",
                }
            ],
            "capacity": {
                "kilobytes": {"free": "523094720", "used": "11474981430", "total": "11998076150"}
            },
        },
        "shares": [
            {
                "name": "Share_1",
                "free": 523094721,
                "used": 11474981429,
                "size": 0,
                "allocator": "highwater",
                "floor": "20000000",
                "luksStatus": "2",
            },
            {
                "name": "Share_2",
                "free": 503491121,
                "used": 5615496143,
                "size": 0,
                "allocator": "highwater",
                "floor": "0",
                "luksStatus": "1",
            },
        ],
        "info": {
            "memory": {"free": 415510528, "total": 16646950912, "active": 12746354688},
            "versions": {"unraid": "7.0.1"},
        },
    }
}
