"""Unraid GraphQL API Client for Api >= 4.26."""

from __future__ import annotations

from awesomeversion import AwesomeVersion
from pydantic import BaseModel, Field

from custom_components.unraid_api.models import Metrics, UpsDevice

from .v4_20 import UnraidApiV420, _Metrics


class UnraidApiV426(UnraidApiV420):
    """
    Unraid GraphQL API Client.

    Api version > 4.26
    """

    version = AwesomeVersion("4.26.0")

    async def query_metrics(self) -> Metrics:
        response = await self.call_api(METRICS_QUERY, MetricsQuery)
        return Metrics(
            memory_free=response.metrics.memory.free,
            memory_total=response.metrics.memory.total,
            memory_active=response.metrics.memory.active,
            memory_available=response.metrics.memory.available,
            memory_percent_total=response.metrics.memory.percent_total,
            cpu_percent_total=response.metrics.cpu.percent_total,
            cpu_temp=response.info.cpu.packages.temp[0],
            cpu_power=response.info.cpu.packages.power[0],
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


## Queries

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

## Api Models


### Metrics
class MetricsQuery(BaseModel):  # noqa: D101
    metrics: _Metrics
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
