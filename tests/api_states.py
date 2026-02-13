"""Unraid API states for Tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from awesomeversion import AwesomeVersion
from custom_components.unraid_api.models import (
    ArrayState,
    Disk,
    DiskStatus,
    DiskType,
    MetricsArray,
    ParityCheckStatus,
    ServerInfo,
    Share,
    UpsDevice,
)


class ApiState:
    """API state Baseclass."""

    version: AwesomeVersion
    server_info: ClassVar[ServerInfo]
    metrics_array: ClassVar[MetricsArray]
    shares: ClassVar[list[Share]]
    disks: ClassVar[list[Disk]]
    ups: ClassVar[list[UpsDevice]]


class ApiState420(ApiState):
    """API state for version 4.20."""

    version = AwesomeVersion("4.20.0")

    def __init__(self) -> None:
        self.server_info = ServerInfo(
            localurl="http://1.2.3.4", name="Test Server", unraid_version="7.0.1"
        )
        self.metrics_array = MetricsArray(
            memory_free=415510528,
            memory_total=16646950912,
            memory_active=12746354688,
            memory_available=3900596224,
            memory_percent_total=76.56870471583932,
            cpu_percent_total=5.1,
            state=ArrayState.STARTED,
            capacity_free=523094720,
            capacity_used=11474981430,
            capacity_total=11998076150,
            parity_check_status=ParityCheckStatus.COMPLETED,
            parity_check_date=datetime(
                year=2025,
                month=9,
                day=27,
                hour=22,
                minute=0,
                second=1,
                tzinfo=UTC,
            ),
            parity_check_duration=5982,
            parity_check_speed=10.0,
            parity_check_errors=None,
            parity_check_progress=0,
        )
        self.shares = [
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
        ]
        self.disks = [
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
        ]
        self.ups = None


class ApiState426(ApiState420):
    """API state for version 4.20."""

    version = AwesomeVersion("4.26.0")

    def __init__(self) -> None:
        super().__init__()

        self.metrics_array.cpu_power = 2.8
        self.metrics_array.cpu_temp = 31.0
        self.ups = [
            UpsDevice(
                id="Back-UPS ES 650G2",
                name="Back-UPS ES 650G2",
                model="Back-UPS ES 650G2",
                status="ONLINE",
                battery_level=100,
                battery_runtime=25,
                battery_health="Good",
                load_percentage=20.0,
                output_voltage=120.5,
                input_voltage=232.0,
            )
        ]


API_STATES = [ApiState420, ApiState426]

API_STATE_LATEST = API_STATES[-1]
