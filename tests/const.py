"""Test Constants."""

from __future__ import annotations

from datetime import UTC, datetime

from awesomeversion import AwesomeVersion
from custom_components.unraid_api.const import CONF_DRIVES, CONF_SHARES
from custom_components.unraid_api.models import (
    Array,
    ArrayState,
    Disk,
    DiskStatus,
    DiskType,
    Metrics,
    ParityCheckStatus,
    ServerInfo,
    Share,
)
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL

MOCK_CONFIG_DATA = {CONF_HOST: "http://1.2.3.4", CONF_API_KEY: "test_key", CONF_VERIFY_SSL: False}
MOCK_OPTION_DATA = {CONF_SHARES: True, CONF_DRIVES: True}

API_VERSION_RESPONSE_INCOMPATIBLE = {
    "data": {
        "info": {
            "versions": {
                "core": {
                    "api": "4.10",
                }
            },
        },
    }
}

API_VERSION_RESPONSE_UNAUTHENTICATED = {
    "errors": [
        {
            "message": "No user session found",
            "locations": [{"line": 2, "column": 3}],
            "path": ["info"],
            "extensions": {
                "code": "UNAUTHENTICATED",
                "originalError": {
                    "message": "No user session found",
                    "error": "Unauthorized",
                    "statusCode": 401,
                },
            },
        }
    ],
    "data": None,
}
CLIENT_RESPONSES = [
    {
        "api_version": AwesomeVersion("4.20.0"),
        "server_info": ServerInfo(
            localurl="http://1.2.3.4", unraid_version="7.0.1", name="Test Server"
        ),
        "metrics": Metrics(
            memory_free=415510528,
            memory_total=16646950912,
            memory_active=12746354688,
            memory_percent_total=76.56870471583932,
            memory_available=3900596224,
            cpu_percent_total=5.1,
        ),
        "shares": [
            Share(
                name="Share_1",
                free=523094721,
                used=11474981429,
                size=0,
                allocator="highwater",
                floor="20000000",
            ),
            Share(
                name="Share_2",
                free=503491121,
                used=5615496143,
                size=0,
                allocator="highwater",
                floor="0",
            ),
        ],
        "disks": [
            Disk(
                name="disk1",
                status=DiskStatus.DISK_OK,
                temp=34,
                fs_size=5999038075,
                fs_free=464583438,
                fs_used=5534454637,
                type=DiskType.Data,
                id="c6b",
                is_spinning=True,
            ),
            Disk(
                name="cache",
                status=DiskStatus.DISK_OK,
                temp=30,
                fs_size=119949189,
                fs_free=38907683,
                fs_used=81041506,
                type=DiskType.Cache,
                id="8e0",
                is_spinning=True,
            ),
            Disk(
                name="parity",
                status=DiskStatus.DISK_OK,
                temp=None,
                fs_size=None,
                fs_free=None,
                fs_used=None,
                type=DiskType.Parity,
                id="4d5",
                is_spinning=False,
            ),
        ],
        "array": Array(
            state=ArrayState.STARTED,
            capacity_free=523094720,
            capacity_used=11474981430,
            capacity_total=11998076150,
            parity_check_status=ParityCheckStatus.COMPLETED,
            parity_check_date=datetime(
                year=2025, month=9, day=27, hour=22, minute=0, second=1, tzinfo=UTC
            ),
            parity_check_duration=5982,
            parity_check_speed=10,
            parity_check_errors=None,
            parity_check_progress=0,
        ),
    }
]
