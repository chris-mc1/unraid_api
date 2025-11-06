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
        return response.vm.start is not None

    async def vm_stop(self, vm_id: str) -> bool:
        """Stop a VM."""
        response = await self.call_api(
            VM_STOP_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm.stop is not None

    async def vm_reboot(self, vm_id: str) -> bool:
        """Reboot a VM."""
        response = await self.call_api(
            VM_REBOOT_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm.reboot is not None

    async def vm_pause(self, vm_id: str) -> bool:
        """Pause a VM."""
        response = await self.call_api(
            VM_PAUSE_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm.pause is not None

    async def vm_resume(self, vm_id: str) -> bool:
        """Resume a VM."""
        response = await self.call_api(
            VM_RESUME_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm.resume is not None

    async def vm_force_stop(self, vm_id: str) -> bool:
        """Force stop a VM."""
        response = await self.call_api(
            VM_FORCE_STOP_MUTATION, VmActionResponse, variables={"id": vm_id}
        )
        return response.vm.force_stop is not None

    async def docker_start(self, container_id: str) -> bool:
        """Start a Docker container."""
        response = await self.call_api(
            DOCKER_START_MUTATION, DockerActionResponse, variables={"id": container_id}
        )
        return response.docker.start is not None

    async def docker_stop(self, container_id: str) -> bool:
        """Stop a Docker container."""
        response = await self.call_api(
            DOCKER_STOP_MUTATION, DockerActionResponse, variables={"id": container_id}
        )
        return response.docker.stop is not None


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
mutation StartVM($id: PrefixedID!) {
  vm {
    start(id: $id) {
      id
      state
    }
  }
}
"""

VM_STOP_MUTATION = """
mutation StopVM($id: PrefixedID!) {
  vm {
    stop(id: $id) {
      id
      state
    }
  }
}
"""

VM_REBOOT_MUTATION = """
mutation RebootVM($id: PrefixedID!) {
  vm {
    reboot(id: $id) {
      id
      state
    }
  }
}
"""

VM_PAUSE_MUTATION = """
mutation PauseVM($id: PrefixedID!) {
  vm {
    pause(id: $id) {
      id
      state
    }
  }
}
"""

VM_RESUME_MUTATION = """
mutation ResumeVM($id: PrefixedID!) {
  vm {
    resume(id: $id) {
      id
      state
    }
  }
}
"""

VM_FORCE_STOP_MUTATION = """
mutation ForceStopVM($id: PrefixedID!) {
  vm {
    forceStop(id: $id) {
      id
      state
    }
  }
}
"""

DOCKER_START_MUTATION = """
mutation StartContainer($id: PrefixedID!) {
  docker {
    start(id: $id) {
      id
      state
    }
  }
}
"""

DOCKER_STOP_MUTATION = """
mutation StopContainer($id: PrefixedID!) {
  docker {
    stop(id: $id) {
      id
      state
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


class _VmActionResult(BaseModel):  # noqa: D101
    id: str
    state: VmState


class _VmMutations(BaseModel):  # noqa: D101
    start: _VmActionResult | None = None
    stop: _VmActionResult | None = None
    reboot: _VmActionResult | None = None
    pause: _VmActionResult | None = None
    resume: _VmActionResult | None = None
    force_stop: _VmActionResult | None = Field(alias="forceStop", default=None)


class VmActionResponse(BaseModel):  # noqa: D101
    vm: _VmMutations


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


class _DockerActionResult(BaseModel):  # noqa: D101
    id: str
    state: DockerState


class _DockerMutations(BaseModel):  # noqa: D101
    start: _DockerActionResult | None = None
    stop: _DockerActionResult | None = None


class DockerActionResponse(BaseModel):  # noqa: D101
    docker: _DockerMutations
