# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **VM control** (fixes [#23](https://github.com/chris-mc1/unraid_api/issues/23)): Switch entities for starting and stopping virtual machines with state monitoring (running, shutoff, paused, etc.)
  - Entity naming: `switch.{server}_vm_{vm_name}` with friendly name "VM {name}"
  - Supports start/stop actions via Home Assistant UI or automations
- **Docker control** (fixes [#22](https://github.com/chris-mc1/unraid_api/issues/22), [#23](https://github.com/chris-mc1/unraid_api/issues/23)): Switch entities for starting and stopping Docker containers with state monitoring
  - Entity naming: `switch.{server}_container_{container_name}` with friendly name "Container {name}"
  - Supports start/stop actions via Home Assistant UI or automations
- **Uptime sensor**: Shows server uptime in human-readable format (e.g., "8 days, 1 hour, 28 minutes") with raw `uptime_since` timestamp attribute
- **UPS monitoring** (fixes [#31](https://github.com/chris-mc1/unraid_api/issues/31)): Three new sensors for UPS-connected servers:
  - UPS Battery (percentage)
  - UPS Load (percentage)
  - UPS Runtime (minutes remaining)
- **SSL redirect auto-detection**: Automatically follows HTTP→HTTPS redirects during setup, supporting Unraid's myunraid.net SSL proxy
- **Improved translations**: Enhanced sensor descriptions and field help text in config flow

### Changed

- **Entity naming convention**:
  - VM switches: `{entry_id}_vm_switch_{vm_id}` unique ID, "VM {name}" friendly name
  - Docker switches: `{entry_id}_container_switch_{container_id}` unique ID, "Container {name}" friendly name
- Cleaner sensor naming convention (e.g., "UPS Battery" instead of device model name)
- Host field now accepts IP address or hostname without requiring `http://` prefix

### Fixed

- HTTP connections now properly redirect to HTTPS when server uses SSL proxy
- SSL certificate errors now automatically retry without verification for self-signed certificates
- Fixed connection issues when entering just IP address without protocol prefix
- Fixed VM GraphQL query to only request available fields (id, name, state)
- Fixed `ZeroDivisionError` in array usage percentage calculation when array is stopped (total capacity is 0)

## [1.0.0] - Initial Release

### Features

- Core integration with Unraid GraphQL API (v4.20.0+)
- Array state monitoring (started/stopped/syncing)
- Disk monitoring:
  - Temperature sensors
  - Standby state binary sensors
  - Usage sensors (used/total space)
- Share monitoring with usage sensors
- System metrics:
  - CPU usage percentage
  - RAM usage (free/total)
- Version-specific API support:
  - v4.20.0: Base implementation
  - v4.26.0: Added CPU temperature and power consumption
- Config flow with:
  - Host/API key configuration
  - SSL verification toggle
  - Options for disk/share monitoring
- Reauth flow for expired API keys
- Dynamic entity creation for disks and shares
