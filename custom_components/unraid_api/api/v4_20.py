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
    DockerContainerState,
    Metrics,
    ServerInfo,
    Share,
    UPSDevice,
    UPSStatus,
    VirtualMachine,
    VMState,
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
            uptime=response.info.os.uptime if response.info.os else None,
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

    async def query_ups_devices(self) -> list[UPSDevice]:
        """Query UPS devices from Unraid."""
        response = await self.call_api(UPS_QUERY, UPSQuery)
        return [
            UPSDevice(
                id=ups.id,
                name=ups.name,
                model=ups.model,
                status=(
                    UPSStatus(ups.status)
                    if ups.status in UPSStatus.__members__
                    else UPSStatus.ONLINE
                ),
                battery_charge=ups.battery.charge_level,
                battery_runtime=ups.battery.estimated_runtime,
                battery_health=ups.battery.health,
                load_percentage=ups.power.load_percentage,
                input_voltage=ups.power.input_voltage,
                output_voltage=ups.power.output_voltage,
            )
            for ups in response.ups_devices
        ]

    async def query_vms(self) -> list[VirtualMachine]:
        """Query virtual machines from Unraid."""
        response = await self.call_api(VMS_QUERY, VMsQuery)
        return [
            VirtualMachine(
                id=vm.id,
                name=vm.name,
                state=VMState(vm.state) if vm.state in VMState.__members__ else VMState.SHUTOFF,
            )
            for vm in response.vms.domain
        ]

    async def query_docker_containers(self) -> list[DockerContainer]:
        """Query Docker containers from Unraid."""
        response = await self.call_api(DOCKER_QUERY, DockerQuery)
        return [
            DockerContainer(
                id=container.id,
                names=container.names,
                state=(
                    DockerContainerState(container.state)
                    if container.state in DockerContainerState.__members__
                    else DockerContainerState.EXITED
                ),
                image=container.image,
                status=container.status,
            )
            for container in response.docker.containers
        ]

    async def start_vm(self, vm_id: str) -> bool:
        """Start a virtual machine."""
        response = await self.call_api(
            VM_START_MUTATION,
            VMStartMutation,
            variables={"id": vm_id},
        )
        return response.vm.start

    async def stop_vm(self, vm_id: str) -> bool:
        """Stop a virtual machine."""
        response = await self.call_api(
            VM_STOP_MUTATION,
            VMStopMutation,
            variables={"id": vm_id},
        )
        return response.vm.stop

    async def start_container(self, container_id: str) -> DockerContainer:
        """Start a Docker container."""
        response = await self.call_api(
            DOCKER_START_MUTATION,
            DockerStartMutation,
            variables={"id": container_id},
        )
        container = response.docker.start
        return DockerContainer(
            id=container.id,
            names=container.names,
            state=(
                DockerContainerState(container.state)
                if container.state in DockerContainerState.__members__
                else DockerContainerState.EXITED
            ),
            image=None,
            status=None,
        )

    async def stop_container(self, container_id: str) -> DockerContainer:
        """Stop a Docker container."""
        response = await self.call_api(
            DOCKER_STOP_MUTATION,
            DockerStopMutation,
            variables={"id": container_id},
        )
        container = response.docker.stop
        return DockerContainer(
            id=container.id,
            names=container.names,
            state=(
                DockerContainerState(container.state)
                if container.state in DockerContainerState.__members__
                else DockerContainerState.EXITED
            ),
            image=None,
            status=None,
        )


## Queries

SERVER_INFO_QUERY = """
query ServerInfo {
  server {
    localurl
    name
  }
  info {
    os {
      uptime
    }
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

## Api Models


### Server Info
class ServerInfoQuery(BaseModel):  # noqa: D101
    server: Server
    info: Info


class Server(BaseModel):  # noqa: D101
    localurl: str
    name: str


class Info(BaseModel):  # noqa: D101
    os: InfoOs | None = None
    versions: InfoVersions


class InfoOs(BaseModel):  # noqa: D101
    uptime: str | None = None


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


### UPS Devices
UPS_QUERY = """
query UPSDevices {
  upsDevices {
    id
    name
    model
    status
    battery {
      chargeLevel
      estimatedRuntime
      health
    }
    power {
      loadPercentage
      inputVoltage
      outputVoltage
    }
  }
}
"""


class UPSQuery(BaseModel):  # noqa: D101
    ups_devices: list[_UPSDevice] = Field(alias="upsDevices")


class _UPSDevice(BaseModel):
    id: str
    name: str
    model: str
    status: str
    battery: _UPSBattery
    power: _UPSPower


class _UPSBattery(BaseModel):
    charge_level: int = Field(alias="chargeLevel")
    estimated_runtime: int = Field(alias="estimatedRuntime")
    health: str | None


class _UPSPower(BaseModel):
    load_percentage: int = Field(alias="loadPercentage")
    input_voltage: float | None = Field(alias="inputVoltage")
    output_voltage: float | None = Field(alias="outputVoltage")


### Virtual Machines
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


class VMsQuery(BaseModel):  # noqa: D101
    vms: _Vms


class _Vms(BaseModel):
    domain: list[_VMDomain]


class _VMDomain(BaseModel):
    id: str
    name: str
    state: str


VM_START_MUTATION = """
mutation StartVM($id: PrefixedID!) {
  vm {
    start(id: $id)
  }
}
"""


class VMStartMutation(BaseModel):  # noqa: D101
    vm: _VMStartResult


class _VMStartResult(BaseModel):
    start: bool


VM_STOP_MUTATION = """
mutation StopVM($id: PrefixedID!) {
  vm {
    stop(id: $id)
  }
}
"""


class VMStopMutation(BaseModel):  # noqa: D101
    vm: _VMStopResult


class _VMStopResult(BaseModel):
    stop: bool


### Docker Containers
DOCKER_QUERY = """
query Docker {
  docker {
    containers {
      id
      names
      state
      image
      status
    }
  }
}
"""


class DockerQuery(BaseModel):  # noqa: D101
    docker: _Docker


class _Docker(BaseModel):
    containers: list[_DockerContainer]


class _DockerContainer(BaseModel):
    id: str
    names: list[str]
    state: str
    image: str | None = None
    status: str | None = None


DOCKER_START_MUTATION = """
mutation StartContainer($id: PrefixedID!) {
  docker {
    start(id: $id) {
      id
      names
      state
    }
  }
}
"""


class DockerStartMutation(BaseModel):  # noqa: D101
    docker: _DockerStartResult


class _DockerStartResult(BaseModel):
    start: _DockerContainerResult


class _DockerContainerResult(BaseModel):
    id: str
    names: list[str]
    state: str


DOCKER_STOP_MUTATION = """
mutation StopContainer($id: PrefixedID!) {
  docker {
    stop(id: $id) {
      id
      names
      state
    }
  }
}
"""


class DockerStopMutation(BaseModel):  # noqa: D101
    docker: _DockerStopResult


class _DockerStopResult(BaseModel):
    stop: _DockerContainerResult
