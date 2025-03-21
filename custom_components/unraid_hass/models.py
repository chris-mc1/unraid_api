"""Models for Unraid GraphQl Api."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


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
    Data = "Data"
    Parity = "Parity"
    Flash = "Flash"
    Cache = "Cache"


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


class QueryResponse(BaseModel):  # noqa: D101
    array: Array
    server: Server
    shares: list[Share]
    info: Info


class Array(BaseModel):  # noqa: D101
    disks: list[Disk]
    parities: list[Disk]
    caches: list[Disk]
    state: ArrayState
    capacity: ArrayCapacity


class Disk(BaseModel):  # noqa: D101
    name: str
    status: ArrayDiskStatus
    temp: int | None
    fs_size: int | None = Field(alias="fsSize")
    fs_free: int | None = Field(alias="fsFree")
    fs_used: int | None = Field(alias="fsUsed")
    type: ArrayDiskType
    id: str


class ArrayCapacity(BaseModel):  # noqa: D101
    kilobytes: ArrayCapacityKilobytes


class ArrayCapacityKilobytes(BaseModel):  # noqa: D101
    free: int
    used: int
    total: int


class Server(BaseModel):  # noqa: D101
    localurl: str
    name: str


class Share(BaseModel):  # noqa: D101
    name: str
    free: int
    used: int
    size: int
    allocator: str
    floor: str
    luks_status: str = Field(alias="luksStatus")


class Info(BaseModel):  # noqa: D101
    memory: InfoMemory
    versions: InfoVersions


class InfoMemory(BaseModel):  # noqa: D101
    free: int
    total: int
    active: int


class InfoVersions(BaseModel):  # noqa: D101
    unraid: str
