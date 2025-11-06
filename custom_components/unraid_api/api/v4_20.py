"""Unraid GraphQL API Client for Api >= 4.20."""

from __future__ import annotations

from pydantic import BaseModel, Field

from custom_components.unraid_api.models import (
    Array,
    ArrayState,
    Disk,
    DiskStatus,
    DiskType,
    DockerContainer,
    DockerState,
    Metrics,
    ServerInfo,
    Share,
    VirtualMachine,
    VmState,
)

from . import UnraidApiClient


class UnraidApiV420(UnraidApiClient):
    """
    Unraid GraphQL API Client.

    Api version > 4.20
    """

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
        return Array(
            state=response.array.state,
            capacity_free=response.array.capacity.kilobytes.free,
            capacity_used=response.array.capacity.kilobytes.used,
            capacity_total=response.array.capacity.kilobytes.total,
        )

    async def query_vms(self) -> list[VirtualMachine]:
        response = await self.call_api(VMS_QUERY, VmsQuery)
        return [
            VirtualMachine(
                id=vm.id,
                name=vm.name,
                state=vm.state,
            )
            for vm in response.vms.domain
        ]

    async def query_docker_containers(self) -> list[DockerContainer]:
        response = await self.call_api(DOCKER_QUERY, DockerQuery)
        return [
            DockerContainer(
                id=container.id,
                name=container.names[0].lstrip("/") if container.names else container.id,
                state=container.state,
                image=container.image,
                autostart=container.auto_start,
            )
            for container in response.docker.containers
        ]

    async def vm_start(self, vm_id: str) -> bool:
        """Start a VM."""
        response = await self.call_api(
            VM_START_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm_start.success

    async def vm_stop(self, vm_id: str) -> bool:
        """Stop a VM."""
        response = await self.call_api(
            VM_STOP_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm_stop.success

    async def vm_reboot(self, vm_id: str) -> bool:
        """Reboot a VM."""
        response = await self.call_api(
            VM_REBOOT_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm_reboot.success

    async def vm_pause(self, vm_id: str) -> bool:
        """Pause a VM."""
        response = await self.call_api(
            VM_PAUSE_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm_pause.success

    async def vm_resume(self, vm_id: str) -> bool:
        """Resume a VM."""
        response = await self.call_api(
            VM_RESUME_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm_resume.success

    async def vm_force_stop(self, vm_id: str) -> bool:
        """Force stop a VM."""
        response = await self.call_api(
            VM_FORCE_STOP_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm_force_stop.success

    async def docker_start(self, container_id: str) -> bool:
        """Start a Docker container."""
        response = await self.call_api(
            DOCKER_START_MUTATION, DockerActionResponse, variables={"id": container_id}
        )
        return response.docker_start.success

    async def docker_stop(self, container_id: str) -> bool:
        """Stop a Docker container."""
        response = await self.call_api(
            DOCKER_STOP_MUTATION, DockerActionResponse, variables={"id": container_id}
        )
        return response.docker_stop.success


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
  }
}

"""

VMS_QUERY = """
query VMs {
  vms {
    domain {
      id
      name
      state
    }
  }
}
"""

DOCKER_QUERY = """
query Docker {
  docker {
    containers {
      id
      names
      state
      image
      autoStart
    }
  }
}
"""

VM_START_MUTATION = """
mutation StartVM($id: String!) {
  vmStart(id: $id) {
    success
  }
}
"""

VM_STOP_MUTATION = """
mutation StopVM($id: String!) {
  vmStop(id: $id) {
    success
  }
}
"""

VM_REBOOT_MUTATION = """
mutation RebootVM($id: String!) {
  vmReboot(id: $id) {
    success
  }
}
"""

VM_PAUSE_MUTATION = """
mutation PauseVM($id: String!) {
  vmPause(id: $id) {
    success
  }
}
"""

VM_RESUME_MUTATION = """
mutation ResumeVM($id: String!) {
  vmResume(id: $id) {
    success
  }
}
"""

VM_FORCE_STOP_MUTATION = """
mutation ForceStopVM($id: String!) {
  vmForceStop(id: $id) {
    success
  }
}
"""

DOCKER_START_MUTATION = """
mutation StartContainer($id: String!) {
  dockerStart(id: $id) {
    success
  }
}
"""

DOCKER_STOP_MUTATION = """
mutation StopContainer($id: String!) {
  dockerStop(id: $id) {
    success
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


class _Array(BaseModel):
    state: ArrayState
    capacity: ArrayCapacity


class ArrayCapacity(BaseModel):  # noqa: D101
    kilobytes: ArrayCapacityKilobytes


class ArrayCapacityKilobytes(BaseModel):  # noqa: D101
    free: int
    used: int
    total: int


### VMs
class VmsQuery(BaseModel):  # noqa: D101
    vms: _VmsRoot


class _VmsRoot(BaseModel):
    domain: list[_VM]


class _VM(BaseModel):
    id: str
    name: str
    state: VmState


class _ActionResult(BaseModel):  # noqa: D101
    success: bool


class VmActionResponse(BaseModel):  # noqa: D101
    vm_start: _ActionResult | None = Field(alias="vmStart", default=None)
    vm_stop: _ActionResult | None = Field(alias="vmStop", default=None)
    vm_reboot: _ActionResult | None = Field(alias="vmReboot", default=None)
    vm_pause: _ActionResult | None = Field(alias="vmPause", default=None)
    vm_resume: _ActionResult | None = Field(alias="vmResume", default=None)
    vm_force_stop: _ActionResult | None = Field(alias="vmForceStop", default=None)


### Docker
class DockerQuery(BaseModel):  # noqa: D101
    docker: _DockerRoot


class _DockerRoot(BaseModel):
    containers: list[_Container]


class _Container(BaseModel):
    id: str
    names: list[str]
    state: DockerState
    image: str
    auto_start: bool = Field(alias="autoStart")


class DockerActionResponse(BaseModel):  # noqa: D101
    docker_start: _ActionResult | None = Field(alias="dockerStart", default=None)
    docker_stop: _ActionResult | None = Field(alias="dockerStop", default=None)
