"""Models for Unraid GraphQl Api."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DiskStatus(StrEnum):  # noqa: D101
    DISK_NP = "DISK_NP"
    DISK_OK = "DISK_OK"
    DISK_NP_MISSING = "DISK_NP_MISSING"
    DISK_INVALID = "DISK_INVALID"
    DISK_WRONG = "DISK_WRONG"
    DISK_DSBL = "DISK_DSBL"
    DISK_NP_DSBL = "DISK_NP_DSBL"
    DISK_DSBL_NEW = "DISK_DSBL_NEW"
    DISK_NEW = "DISK_NEW"


class DiskType(StrEnum):  # noqa: D101
    Data = "DATA"
    Parity = "PARITY"
    Flash = "FLASH"
    Cache = "CACHE"


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


@dataclass
class ServerInfo:
    """Server Info."""

    localurl: str
    name: str
    unraid_version: str


@dataclass
class Metrics:
    """Metrics."""

    memory_free: int
    memory_total: int
    memory_active: int
    memory_available: int
    memory_percent_total: float
    cpu_percent_total: float


@dataclass
class Share:
    """Shares."""

    name: str
    free: int
    used: int
    size: int
    allocator: str
    floor: str


@dataclass
class Disk:
    """Disk."""

    name: str
    status: DiskStatus
    temp: int | None
    fs_size: int | None
    fs_free: int | None
    fs_used: int | None
    type: DiskType
    id: str
    is_spinning: bool


@dataclass
class Array:
    """Array."""

    state: ArrayState
    capacity_free: int
    capacity_used: int
    capacity_total: int


class VmState(StrEnum):  # noqa: D101
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    PAUSED = "PAUSED"
    PMSUSPENDED = "PMSUSPENDED"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    SHUTDOWN = "SHUTDOWN"
    CRASHED = "CRASHED"


class DockerState(StrEnum):  # noqa: D101
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    PAUSED = "PAUSED"
    RESTARTING = "RESTARTING"
    CREATED = "CREATED"
    EXITED = "EXITED"
    DEAD = "DEAD"


@dataclass
class VirtualMachine:
    """Virtual Machine."""

    id: str
    name: str
    state: VmState


@dataclass
class DockerContainer:
    """Docker Container."""

    id: str
    name: str
    state: DockerState
    image: str
    autostart: bool
