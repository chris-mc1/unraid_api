"""GraphQL API responses for Tests."""

from __future__ import annotations

from awesomeversion import AwesomeVersion

## API Version 4.20
API_VERSION_RESPONSE_V4_20 = {
    "data": {
        "info": {
            "versions": {
                "core": {
                    "api": "4.20.0+196bd52",
                }
            },
        },
    }
}


SERVER_INFO_RESPONSE_V4_20 = {
    "data": {
        "server": {"localurl": "http://1.2.3.4", "name": "Test Server"},
        "info": {
            "versions": {
                "core": {
                    "unraid": "7.0.1",
                },
            },
        },
    }
}

METRICS_RESPONSE_V4_20 = {
    "data": {
        "metrics": {
            "memory": {
                "free": 415510528,
                "total": 16646950912,
                "active": 12746354688,
                "percentTotal": 76.56870471583932,
                "available": 3900596224,
            },
            "cpu": {"percentTotal": 5.1},
        },
    }
}

SHARES_RESPONSE_V4_20 = {
    "data": {
        "shares": [
            {
                "name": "Share_1",
                "free": 523094721,
                "used": 11474981429,
                "size": 0,
                "allocator": "highwater",
                "floor": "20000000",
            },
            {
                "name": "Share_2",
                "free": 503491121,
                "used": 5615496143,
                "size": 0,
                "allocator": "highwater",
                "floor": "0",
            },
        ],
    }
}

DISKS_RESPONSE_V4_20 = {
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
                    "isSpinning": True,
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
                    "isSpinning": False,
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
                    "isSpinning": True,
                }
            ],
        },
    }
}

ARRAY_RESPONSE_V4_20 = {
    "data": {
        "array": {
            "state": "STARTED",
            "capacity": {
                "kilobytes": {"free": "523094720", "used": "11474981430", "total": "11998076150"}
            },
        },
    }
}


API_RESPONSES = [
    {
        "api_version": API_VERSION_RESPONSE_V4_20,
        "server_info": SERVER_INFO_RESPONSE_V4_20,
        "metrics": METRICS_RESPONSE_V4_20,
        "shares": SHARES_RESPONSE_V4_20,
        "disks": DISKS_RESPONSE_V4_20,
        "array": ARRAY_RESPONSE_V4_20,
        "version": AwesomeVersion("4.20.0"),
    }
]
