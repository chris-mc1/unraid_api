"""Constants."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "unraid_api"
PLATFORMS = [Platform.SENSOR]

CONF_SHARES: Final[str] = "shares"
CONF_DRIVES: Final[str] = "drives"

QUERY = """

query Hass {
  server {
    localurl
    name
  }
  array {
    state
    disks {
      name
      status
      temp
      fsSize
      fsFree
      fsUsed
      type
      id
    }
    parities {
      name
      status
      temp
      fsSize
      fsFree
      fsUsed
      type
      id
    }
    caches {
      name
      status
      temp
      fsSize
      fsFree
      fsUsed
      type
      id
    }
    capacity {
      kilobytes {
        free
        used
        total
      }
    }
  }
  shares {
    name
    free
    used
    size
    allocator
    floor
    luksStatus
  }
  metrics {
    memory {
      total
      available
      active
      percentTotal
    }
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
