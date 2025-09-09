"""Models for Unraid GraphQl Api."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


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
    metrics: Metrics


class Metrics(BaseModel):  # noqa: D101
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
    shares: list[Share]


class Share(BaseModel):  # noqa: D101
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
    disks: list[Disk]
    parities: list[ParityDisk]
    caches: list[Disk]


class Disk(BaseModel):  # noqa: D101
    name: str
    status: ArrayDiskStatus
    temp: int | None
    fs_size: int | None = Field(alias="fsSize")
    fs_free: int | None = Field(alias="fsFree")
    fs_used: int | None = Field(alias="fsUsed")
    type: ArrayDiskType
    id: str
    is_spinning: bool = Field(alias="isSpinning")


class ParityDisk(BaseModel):  # noqa: D101
    name: str
    status: ArrayDiskStatus
    temp: int | None
    type: ArrayDiskType
    id: str
    is_spinning: bool = Field(alias="isSpinning")


class ArrayDiskStatus(StrEnum):  # noqa: D101
    DISK_NP = "DISK_NP"
    DISK_OK = "DISK_OK"
    DISK_NP_MISSING = "DISK_NP_MISSING"
    DISK_INVALID = "DISK_INVALID"
    DISK_WRONG = "DISK_WRONG"
    DISK_DSBL = "DISK_DSBL"
    DISK_NP_DSBL = "DISK_NP_DSBL"
    DISK_DSBL_NEW = "DISK_DSBL_NEW"
    DISK_NEW = "DISK_NEW"


class ArrayDiskType(StrEnum):  # noqa: D101
    DATA = "DATA"
    Parity = "PARITY"
    Flash = "FLASH"
    Cache = "CACHE"


### Array
class ArrayQuery(BaseModel):  # noqa: D101
    array: ArrayArray


class ArrayArray(BaseModel):  # noqa: D101
    state: ArrayState
    capacity: ArrayCapacity


class ArrayState(StrEnum):  # noqa: D101
    STARTED = "STARTED"
    STOPPED = "STOPPED"
    NEW_ARRAY = "NEW_ARRAY"
    RECON_DISK = "RECON_DISK"
    DISABLE_DISK = "DISABLE_DISK"
    SWAP_DSBL = "SWAP_DSBL"
    INVALID_EXPANSION = "INVALID_EXPANSION"
    PARITY_NOT_BIGGEST = "PARITY_NOT_BIGGEST"
    TOO_MANY_MISSING_DISKS = "TOO_MANY_MISSING_DISKS"
    NEW_DISK_TOO_SMALL = "NEW_DISK_TOO_SMALL"
    NO_DATA_DISKS = "NO_DATA_DISKS"


class ArrayCapacity(BaseModel):  # noqa: D101
    kilobytes: ArrayCapacityKilobytes


class ArrayCapacityKilobytes(BaseModel):  # noqa: D101
    free: int
    used: int
    total: int
