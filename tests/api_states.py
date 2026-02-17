"""Unraid API states for Tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

import yarl
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.models import (
    ArrayState,
    ContainerState,
    Disk,
    DiskStatus,
    DiskType,
    DockerContainer,
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
    docker: ClassVar[list[DockerContainer]]


class ApiState420(ApiState):
    """API state for version 4.20."""

    version = AwesomeVersion("4.20.0")

    def __init__(self) -> None:
        self.server_info = ServerInfo(
            localurl="http://1.2.3.4", name="Test Server", unraid_version="7.0.1"
        )
        self.metrics_array = MetricsArray(
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
        self.docker = [
            DockerContainer(
                id="4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:9591842fdb0e817f385407d6eb71d0070bcdfd3008506d5e7e53c3036939c2b0",
                name="homeassistant",
                state=ContainerState.RUNNING,
                image="ghcr.io/home-assistant/home-assistant:stable",
                image_sha256="e0477b544d48b26ad81e2132b8ce36f0a20dfd7eb44de9c40718fa78dc92e24d",
                status="Up 28 minutes",
                label_opencontainers_version="2026.2.2",
                label_unraid_webui=yarl.URL("http://homeassistant.unraid.lan"),
                label_monitor=None,
                label_name=None,
            ),
            DockerContainer(
                id="4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:db6215c5578bd28bc78fab45e16b7a2d6d94ec3bb3b23a5ad5b8b4979e79bf86",
                name="postgres",
                state=ContainerState.RUNNING,
                image="postgres:15",
                image_sha256="a748a13f04094ee02b167d3e2a919368bc5e93cbd2b1c41a6d921dbaa59851ac",
                status="Up 28 minutes",
                label_opencontainers_version=None,
                label_unraid_webui=None,
                label_monitor=False,
                label_name="Postgres",
            ),
            DockerContainer(
                id="4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:cc3843b7435c45ba8ff9c10b7e3c494d51fc303e609d12825b63537be52db369",
                name="grafana",
                state=ContainerState.EXITED,
                image="grafana/grafana-enterprise",
                image_sha256="32241300d32d708c29a186e61692ff00d6c3f13cb862246326edd4612d735ae5",
                status="Up 28 minutes",
                label_opencontainers_version=None,
                label_unraid_webui=None,
                label_monitor=True,
                label_name="Grafana Public",
            ),
        ]


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
