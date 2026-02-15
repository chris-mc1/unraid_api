"""Unraid GraphQL API Client for Api >= 4.20."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

import yarl
from awesomeversion import AwesomeVersion
from pydantic import BaseModel, Field

from custom_components.unraid_api.models import (
    ArrayState,
    ContainerState,
    Disk,
    DiskStatus,
    DiskType,
    DockerContainer,
    MemorySubscription,
    MetricsArray,
    ParityCheckStatus,
    ServerInfo,
    Share,
)

from . import _LOGGER, UnraidApiClient, _to_bool

if TYPE_CHECKING:
    from collections.abc import Callable


def _make_container_obj(container: _DockerContainer) -> DockerContainer:
    label_unraid_webui = container.labels.get("net.unraid.docker.webui", "")
    if label_unraid_webui == "":
        webui = None
    else:
        url = label_unraid_webui if "://" in label_unraid_webui else f"http://{label_unraid_webui}"
        try:
            webui = yarl.URL(url)
        except (ValueError, TypeError):
            _LOGGER.debug("Can't build webui url: %s", label_unraid_webui)

    label_name = container.labels.get("io.home-assistant.unraid_api.name")
    name = label_name or None

    return DockerContainer(
        id=container.id,
        name=container.names[0].lstrip("/"),
        state=container.state,
        image=container.image,
        image_sha256=container.image_sha265.removeprefix("sha256:"),
        status=container.status,
        label_opencontainers_version=container.labels.get("org.opencontainers.image.version"),
        label_unraid_webui=webui,
        label_monitor=_to_bool(container.labels.get("io.home-assistant.unraid_api.monitor")),
        label_name=name,
    )


class UnraidApiV420(UnraidApiClient):
    """
    Unraid GraphQL API Client.

    Api version > 4.20
    """

    version = AwesomeVersion("4.20.0")

    async def query_server_info(self) -> ServerInfo:
        response = await self.call_api(SERVER_INFO_QUERY, ServerInfoQuery)
        return ServerInfo(
            localurl=response.server.localurl,
            name=response.server.name,
            unraid_version=response.info.versions.core.unraid,
        )

    async def query_metrics_array(self) -> MetricsArray:
        response = await self.call_api(METRICS_ARRAY_QUERY, MetricsArrayQuery)
        return MetricsArray(
            memory_free=response.metrics.memory.free,
            memory_total=response.metrics.memory.total,
            memory_active=response.metrics.memory.active,
            memory_available=response.metrics.memory.available,
            memory_percent_total=response.metrics.memory.percent_total,
            cpu_percent_total=response.metrics.cpu.percent_total,
            state=response.array.state,
            capacity_free=response.array.capacity.kilobytes.free,
            capacity_used=response.array.capacity.kilobytes.used,
            capacity_total=response.array.capacity.kilobytes.total,
            parity_check_status=response.array.parity_check.status,
            parity_check_date=response.array.parity_check.date,
            parity_check_duration=response.array.parity_check.duration,
            parity_check_speed=response.array.parity_check.speed,
            parity_check_errors=response.array.parity_check.errors,
            parity_check_progress=response.array.parity_check.progress,
        )

    async def query_shares(self) -> list[Share]:
        response = await self.call_api(SHARES_QUERY, SharesQuery)
        return [
            Share(
                name=share.name,
                free=share.free,
                used=share.used,
                size=share.size,
                allocator=share.allocator,
                floor=share.floor,
            )
            for share in response.shares
        ]

    async def query_disks(self) -> list[Disk]:
        response = await self.call_api(DISKS_QUERY, DiskQuery)
        disks = [
            Disk(
                name=disk.name,
                status=disk.status,
                temp=disk.temp,
                fs_size=disk.fs_size,
                fs_free=disk.fs_free,
                fs_used=disk.fs_used,
                type=disk.type,
                id=disk.id,
                is_spinning=disk.is_spinning,
            )
            for disk in response.array.disks
        ]
        disks.extend(
            [
                Disk(
                    name=disk.name,
                    status=disk.status,
                    temp=disk.temp,
                    fs_size=disk.fs_size,
                    fs_free=disk.fs_free,
                    fs_used=disk.fs_used,
                    type=disk.type,
                    id=disk.id,
                    is_spinning=disk.is_spinning,
                )
                for disk in response.array.caches
            ]
        )
        disks.extend(
            [
                Disk(
                    name=disk.name,
                    status=disk.status,
                    temp=disk.temp,
                    fs_size=None,
                    fs_free=None,
                    fs_used=None,
                    type=disk.type,
                    id=disk.id,
                    is_spinning=disk.is_spinning,
                )
                for disk in response.array.parities
            ]
        )
        return disks

    async def query_docker(self) -> list[DockerContainer]:
        response = await self.call_api(DOCKER_QUERY, DockerQuery)
        return [_make_container_obj(container) for container in response.docker.containers]

    async def subscribe_cpu_usage(self, callback: Callable[[float], None]) -> None:
        def _callback(data: Any) -> None:
            model = SystemMetricsCpuSubscription.model_validate(data)
            callback(model.system_metrics_cpu.percent_total)

        await self._subscribe(
            query=CPU_USAGE_SUBSCRIPTION, operation_name="CpuUsage", callback=_callback
        )

    async def subscribe_memory(self, callback: Callable[[MemorySubscription], None]) -> None:
        def _callback(data: Any) -> None:
            model = SystemMetricsMemorySubscription.model_validate(data)
            callback(
                MemorySubscription(
                    free=model.system_metrics_memory.free,
                    total=model.system_metrics_memory.total,
                    active=model.system_metrics_memory.active,
                    available=model.system_metrics_memory.available,
                    percent_total=model.system_metrics_memory.percent_total,
                )
            )

        await self._subscribe(
            query=MEMORY_SUBSCRIPTION, operation_name="Memory", callback=_callback
        )

    async def start_parity_check(self) -> None:
        await self.call_api(PARITY_CHECK_START, None)

    async def cancel_parity_check(self) -> None:
        await self.call_api(PARITY_CHECK_CANCEL, None)

    async def pause_parity_check(self) -> None:
        await self.call_api(PARITY_CHECK_PAUSE, None)

    async def resume_parity_check(self) -> None:
        await self.call_api(PARITY_CHECK_RESUME, None)

    async def start_container(self, container_id: str) -> DockerContainer:
        model = await self.call_api(DOCKER_START, DockerStart, {"startId": container_id})
        return _make_container_obj(model.docker.start)

    async def stop_container(self, container_id: str) -> DockerContainer:
        model = await self.call_api(DOCKER_STOP, DockerStop, {"stopId": container_id})
        return _make_container_obj(model.docker.stop)


## Queries

SERVER_INFO_QUERY = """
query ServerInfo {
  server {
    localurl
    name
  }
  info {
    versions {
      core {
        unraid
      }
    }
  }
}
"""

METRICS_ARRAY_QUERY = """
query MetricsArray {
  metrics {
    memory {
      free
      total
      percentTotal
      active
      available
    }
    cpu {
      percentTotal
    }
  }
  array {
    state
    capacity {
      kilobytes {
        free
        used
        total
      }
    }
    parityCheckStatus {
      date
      duration
      speed
      status
      errors
      progress
    }
  }
}
"""

SHARES_QUERY = """
query Shares {
  shares {
    name
    free
    used
    size
    allocator
    floor
  }
}
"""

DISKS_QUERY = """
query Disks {
  array {
    caches {
      name
      status
      temp
      fsSize
      fsFree
      fsUsed
      type
      id
      isSpinning
    }
    disks {
      name
      status
      temp
      fsSize
      fsFree
      fsUsed
      fsType
      type
      id
      isSpinning
    }
    parities {
      name
      status
      temp
      type
      id
      isSpinning
    }
  }
}
"""
DOCKER_QUERY = """
query DockerContainers {
  docker {
    containers {
      labels
      names
      id
      image
      imageId
      state
      status
    }
  }
}
"""


## Subscription
CPU_USAGE_SUBSCRIPTION = """
subscription CpuUsage {
  systemMetricsCpu {
    percentTotal
  }
}
"""

MEMORY_SUBSCRIPTION = """
subscription Memory {
  systemMetricsMemory {
    free
    total
    percentTotal
    active
    available
  }
}

"""


## Mutations
PARITY_CHECK_START = """
mutation ParityCheck {
  parityCheck {
    start(correct: true)
  }
}
"""

PARITY_CHECK_CANCEL = """
mutation ParityCheck {
  parityCheck {
    cancel
  }
}
"""

PARITY_CHECK_PAUSE = """
mutation ParityCheck {
  parityCheck {
    pause
  }
}
"""

PARITY_CHECK_RESUME = """
mutation ParityCheck {
  parityCheck {
    resume
  }
}
"""

DOCKER_START = """
mutation DockerStart($startId: PrefixedID!) {
  docker {
    start(id: $startId) {
      state
      names
      labels
      id
      image
      imageId
      status
    }
  }
}
"""

DOCKER_STOP = """
mutation DockerStop($stopId: PrefixedID!) {
  docker {
    stop(id: $stopId) {
      state
      names
      labels
      id
      image
      imageId
      status
    }
  }
}
"""

## Api Models


### Server Info
class ServerInfoQuery(BaseModel):  # noqa: D101
    server: Server
    info: Info


class Server(BaseModel):  # noqa: D101
    localurl: str
    name: str


class Info(BaseModel):  # noqa: D101
    versions: InfoVersions


class InfoVersions(BaseModel):  # noqa: D101
    core: InfoVersionsCore


class InfoVersionsCore(BaseModel):  # noqa: D101
    unraid: str


### Metrics and Array
class MetricsArrayQuery(BaseModel):  # noqa: D101
    metrics: _Metrics
    array: _Array


class _Metrics(BaseModel):
    memory: MetricsMemory
    cpu: MetricsCpu


class MetricsMemory(BaseModel):  # noqa: D101
    free: int
    total: int
    active: int
    percent_total: float = Field(alias="percentTotal")
    available: int


class MetricsCpu(BaseModel):  # noqa: D101
    percent_total: float = Field(alias="percentTotal")


class _Array(BaseModel):
    state: ArrayState
    capacity: ArrayCapacity
    parity_check: ParityCheck = Field(alias="parityCheckStatus")


class ArrayCapacity(BaseModel):  # noqa: D101
    kilobytes: ArrayCapacityKilobytes


class ArrayCapacityKilobytes(BaseModel):  # noqa: D101
    free: int
    used: int
    total: int


class ParityCheck(BaseModel):  # noqa: D101
    date: datetime
    duration: int
    speed: float
    status: ParityCheckStatus
    errors: int | None
    progress: int


### Shares
class SharesQuery(BaseModel):  # noqa: D101
    shares: list[_Share]


class _Share(BaseModel):
    name: str
    free: int
    used: int
    size: int
    allocator: str
    floor: str


### Disks
class DiskQuery(BaseModel):  # noqa: D101
    array: DisksArray


class DisksArray(BaseModel):  # noqa: D101
    disks: list[FSDisk]
    parities: list[ParityDisk]
    caches: list[FSDisk]


class ParityDisk(BaseModel):  # noqa: D101
    name: str
    status: DiskStatus
    temp: int | None
    type: DiskType
    id: str
    is_spinning: bool = Field(alias="isSpinning")


class FSDisk(ParityDisk):  # noqa: D101
    fs_size: int | None = Field(alias="fsSize")
    fs_free: int | None = Field(alias="fsFree")
    fs_used: int | None = Field(alias="fsUsed")


### Docker
class DockerQuery(BaseModel):  # noqa: D101
    docker: Docker


class Docker(BaseModel):  # noqa: D101
    containers: list[_DockerContainer]


class _DockerContainer(BaseModel):
    id: str
    names: list[str]
    state: ContainerState
    labels: dict[str, str]
    image: str
    image_sha265: str = Field(alias="imageId")
    status: str


class DockerStart(BaseModel):  # noqa: D101
    docker: _DockerStart


class _DockerStart(BaseModel):
    start: _DockerContainer


class DockerStop(BaseModel):  # noqa: D101
    docker: _DockerStop


class _DockerStop(BaseModel):
    stop: _DockerContainer


### CpuMetrics
class SystemMetricsCpu(BaseModel):  # noqa: D101
    percent_total: float = Field(alias="percentTotal")


class SystemMetricsCpuSubscription(BaseModel):  # noqa: D101
    system_metrics_cpu: SystemMetricsCpu = Field(alias="systemMetricsCpu")


### Memory
class SystemMetricsMemorySubscription(BaseModel):  # noqa: D101
    system_metrics_memory: MetricsMemory = Field(alias="systemMetricsMemory")
