"""Unraid GraphQL API Client for Api >= 4.26."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from awesomeversion import AwesomeVersion
from pydantic import BaseModel, Field

from custom_components.unraid_api.models import CpuMetricsSubscription, MetricsArray, UpsDevice

from .v4_20 import UnraidApiV420, _Array, _Metrics

if TYPE_CHECKING:
    from collections.abc import Callable


class UnraidApiV426(UnraidApiV420):
    """
    Unraid GraphQL API Client.

    Api version > 4.26
    """

    version = AwesomeVersion("4.26.0")

    async def query_metrics_array(self) -> MetricsArray:
        response = await self.call_api(METRICS_ARRAY_QUERY, MetricsArrayQuery)
        return MetricsArray(
            memory_free=response.metrics.memory.free,
            memory_total=response.metrics.memory.total,
            memory_active=response.metrics.memory.active,
            memory_available=response.metrics.memory.available,
            memory_percent_total=response.metrics.memory.percent_total,
            cpu_percent_total=response.metrics.cpu.percent_total,
            cpu_temp=response.info.cpu.packages.temp[0],
            cpu_power=response.info.cpu.packages.power[0],
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

    async def query_ups(self) -> list[UpsDevice]:
        response = await self.call_api(UPS_QUERY, UpsQuery)
        return [
            UpsDevice(
                id=device.id,
                name=device.name,
                model=device.model,
                status=device.status,
                battery_health=device.battery.health,
                battery_runtime=device.battery.estimated_runtime,
                battery_level=device.battery.charge_level,
                load_percentage=device.power.load_percentage,
                output_voltage=device.power.output_voltage,
                input_voltage=device.power.input_voltage,
            )
            for device in response.ups_devices
        ]

    async def subscribe_cpu_metrics(
        self, callback: Callable[[CpuMetricsSubscription], None]
    ) -> None:
        def _callback(data: Any) -> None:
            model = SystemMetricsCpuTelemetrySubscription.model_validate(data)
            callback(
                CpuMetricsSubscription(
                    power=model.system_metrics_cpu_telemetry.power[0],
                    temp=model.system_metrics_cpu_telemetry.temp[0],
                )
            )

        await self._subscribe(
            query=CPU_METRICS_SUBSCRIPTION, operation_name="CpuMetrics", callback=_callback
        )


## Queries

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
  info {
    cpu {
      packages {
        power
        temp
      }
    }
  }
}
"""

UPS_QUERY = """
query UpsDevices {
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
      inputVoltage
      outputVoltage
      loadPercentage
    }
  }
}
"""


## Subscription
CPU_METRICS_SUBSCRIPTION = """
subscription CpuMetrics {
  systemMetricsCpuTelemetry {
    temp
    power
  }
}
"""

## Api Models


### Metrics and Array
class MetricsArrayQuery(BaseModel):  # noqa: D101
    metrics: _Metrics
    array: _Array
    info: Info


class Info(BaseModel):  # noqa: D101
    cpu: Cpu


class Cpu(BaseModel):  # noqa: D101
    packages: Packages


class Packages(BaseModel):  # noqa: D101
    power: list[float]
    temp: list[float]


### UPS
class UpsQuery(BaseModel):  # noqa: D101
    ups_devices: list[UpsDevices] = Field(alias="upsDevices")


class UpsDevices(BaseModel):  # noqa: D101
    id: str
    name: str
    model: str
    status: str
    battery: UPSBattery
    power: UPSPower


class UPSBattery(BaseModel):  # noqa: D101
    charge_level: int = Field(alias="chargeLevel")
    estimated_runtime: int = Field(alias="estimatedRuntime")
    health: str


class UPSPower(BaseModel):  # noqa: D101
    input_voltage: float = Field(alias="inputVoltage")
    load_percentage: float = Field(alias="loadPercentage")
    output_voltage: float = Field(alias="outputVoltage")


### CpuMetricsTelemetry
class SystemMetricsCpuTelemetry(BaseModel):  # noqa: D101
    power: list[float]
    temp: list[float]


class SystemMetricsCpuTelemetrySubscription(BaseModel):  # noqa: D101
    system_metrics_cpu_telemetry: SystemMetricsCpuTelemetry = Field(
        alias="systemMetricsCpuTelemetry"
    )
