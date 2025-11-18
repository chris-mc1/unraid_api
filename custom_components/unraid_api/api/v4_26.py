"""Unraid GraphQL API Client for Api >= 4.26."""

from __future__ import annotations

from awesomeversion import AwesomeVersion
from pydantic import BaseModel

from custom_components.unraid_api.models import Metrics

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
