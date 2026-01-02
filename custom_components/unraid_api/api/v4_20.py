"""Unraid GraphQL API Client for Api >= 4.20."""

from __future__ import annotations

from awesomeversion import AwesomeVersion
from pydantic import BaseModel, Field

from custom_components.unraid_api.models import (
    Array,
    ArrayState,
    Disk,
    DiskStatus,
    DiskType,
    DockerContainer,
    Metrics,
    ParityCheckStatus,
    ServerInfo,
    Share,
)

from . import UnraidApiClient


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

    async def query_metrics(self) -> Metrics:
        response = await self.call_api(METRICS_QUERY, MetricsQuery)
        return Metrics(
            memory_free=response.metrics.memory.free,
            memory_total=response.metrics.memory.total,
            memory_active=response.metrics.memory.active,
            memory_available=response.metrics.memory.available,
            memory_percent_total=response.metrics.memory.percent_total,
            cpu_percent_total=response.metrics.cpu.percent_total,
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

    async def query_array(self) -> Array:
        response = await self.call_api(ARRAY_QUERY, ArrayQuery)
        
        # Parse parity check status if available
        parity_check_status = None
        if response.array.parity_check_status:
            pc = response.array.parity_check_status
            parity_check_status = ParityCheckStatus(
                correcting=pc.correcting,
                date=pc.date,
                duration=pc.duration,
                errors=pc.errors,
                paused=pc.paused,
                progress=pc.progress,
                running=pc.running,
                speed=pc.speed,
                status=pc.status,
            )
        
        return Array(
            state=response.array.state,
            capacity_free=response.array.capacity.kilobytes.free,
            capacity_used=response.array.capacity.kilobytes.used,
            capacity_total=response.array.capacity.kilobytes.total,
            parity_check_status=parity_check_status,
        )

    async def query_docker_containers(self) -> list[DockerContainer]:
        response = await self.call_api(DOCKER_CONTAINERS_QUERY, DockerContainersQuery)
        return [
            DockerContainer(
                id=container.id,
                name=container.names[0].lstrip("/") if container.names else container.id[:12],
                names=container.names,
                state=container.state,
                status=container.status,
                auto_start=container.auto_start,
                image=container.image,
            )
            for container in response.docker.containers
        ]

    async def start_docker_container(self, container_id: str) -> None:
        """Start a Docker container."""
        await self.call_api(
            START_DOCKER_CONTAINER_MUTATION,
            StartDockerContainerMutation,
            variables={"containerId": container_id},
        )

    async def stop_docker_container(self, container_id: str) -> None:
        """Stop a Docker container."""
        await self.call_api(
            STOP_DOCKER_CONTAINER_MUTATION,
            StopDockerContainerMutation,
            variables={"containerId": container_id},
        )


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

METRICS_QUERY = """
query Metrics {
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

ARRAY_QUERY = """
query Array {
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
      correcting
      date
      duration
      errors
      paused
      progress
      running
      speed
      status
  }
}
}

"""

DOCKER_CONTAINERS_QUERY = """
query DockerContainers {
  docker {
    containers {
      id
      names
      state
      status
      autoStart
      image
    }
  }
}
"""

START_DOCKER_CONTAINER_MUTATION = """
mutation StartDockerContainer($containerId: PrefixedID!) {
  docker {
    start(id: $containerId) {
      id
    }
  }
}
"""

STOP_DOCKER_CONTAINER_MUTATION = """
mutation StopDockerContainer($containerId: PrefixedID!) {
  docker {
    stop(id: $containerId) {
      id
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


### Metrics
class MetricsQuery(BaseModel):  # noqa: D101
    metrics: _Metrics


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


### Array
class ArrayQuery(BaseModel):  # noqa: D101
    array: _Array


class ParityCheckStatusResponse(BaseModel):  # noqa: D101
    correcting: bool | None
    date: str | None
    duration: int | None
    errors: int | None
    paused: bool | None
    progress: float
    running: bool | None
    speed: str | None
    status: str | None


class _Array(BaseModel):
    state: ArrayState
    capacity: ArrayCapacity
    parity_check_status: ParityCheckStatusResponse | None = Field(
        alias="parityCheckStatus", default=None
    )


class ArrayCapacity(BaseModel):  # noqa: D101
    kilobytes: ArrayCapacityKilobytes


class ArrayCapacityKilobytes(BaseModel):  # noqa: D101
    free: int
    used: int
    total: int


### Docker Containers
class DockerContainersQuery(BaseModel):  # noqa: D101
    docker: Docker


class Docker(BaseModel):  # noqa: D101
    containers: list[DockerContainerResponse]


class DockerContainerResponse(BaseModel):  # noqa: D101
    id: str
    names: list[str]
    state: str
    status: str
    auto_start: bool = Field(alias="autoStart")
    image: str


### Docker Mutations
class StartDockerContainerMutation(BaseModel):  # noqa: D101
    docker: DockerMutationStartResult


class StopDockerContainerMutation(BaseModel):  # noqa: D101
    docker: DockerMutationStopResult


class DockerMutationStartResult(BaseModel):  # noqa: D101
    start: DockerContainerId


class DockerMutationStopResult(BaseModel):  # noqa: D101
    stop: DockerContainerId


class DockerContainerId(BaseModel):  # noqa: D101
    id: str
