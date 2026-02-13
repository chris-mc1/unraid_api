"""Models for Unraid GraphQl Api."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime  # noqa: TC003
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


class ParityCheckStatus(StrEnum):  # noqa: D101
    NEVER_RUN = "NEVER_RUN"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


@dataclass
class ServerInfo:
    """Server Info."""

    localurl: str
    name: str
    unraid_version: str


@dataclass
class MetricsArray:
    """Metrics."""

    memory_free: int
    memory_total: int
    memory_active: int
    memory_available: int
    memory_percent_total: float
    cpu_percent_total: float
    state: ArrayState
    capacity_free: int
    capacity_used: int
    capacity_total: int
    parity_check_status: ParityCheckStatus
    parity_check_date: datetime
    parity_check_duration: int
    parity_check_speed: float
    parity_check_errors: int | None
    parity_check_progress: int
    cpu_temp: float | None = None
    cpu_power: float | None = None


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
class UpsDevice:
    """UPS device."""

    id: str
    name: str
    model: str
    status: str
    battery_level: int
    battery_runtime: int
    battery_health: str
    load_percentage: float
    output_voltage: float
    input_voltage: float


@dataclass
class CpuMetricsSubscription:
    """Cpu metrics subscription."""

    power: float
    temp: float


@dataclass
class MemorySubscription:
    """Memory subscription."""

    free: int
    total: int
    active: int
    available: int
    percent_total: float
