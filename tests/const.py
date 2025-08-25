"""Test Constants."""

from __future__ import annotations

from custom_components.unraid_api.const import CONF_DRIVES, CONF_SHARES
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL

MOCK_CONFIG_DATA = {CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False}
MOCK_OPTION_DATA = {CONF_SHARES: True, CONF_DRIVES: True}
SERVER_INFO_RESPONSE = {
    "data": {
        "server": {"localurl": "http://1.2.3.4", "name": "Test Server"},
        "info": {
            "versions": {
                "core": {"unraid": "7.0.1"},
            },
        },
    }
}

METRICS_RESPONSE = {
    "data": {
        "metrics": {
            "memory": {
                "free": 415510528,
                "total": 16646950912,
                "active": 12746354688,
                "percentTotal": 76.56870471583932,
            },
            "cpu": {"percentTotal": 5.1},
        },
    }
}

SHARES_RESPONSE = {
    "data": {
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
    }
}

DISKS_RESPONSE = {
    "data": {
        "array": {
            "disks": [
                {
                    "name": "disk1",
                    "status": "DISK_OK",
                    "temp": 34,
                    "fsSize": 5999038075,
                    "fsFree": 464583438,
                    "fsUsed": 5534454637,
                    "type": "DATA",
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
                    "type": "PARITY",
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
                    "type": "CACHE",
                    "id": "8e0",
                }
            ],
        },
    }
}

ARRAY_RESPONSE = {
    "data": {
        "array": {
            "state": "STARTED",
            "capacity": {
                "kilobytes": {"free": "523094720", "used": "11474981430", "total": "11998076150"}
            },
        },
    }
}
