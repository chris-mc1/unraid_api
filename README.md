# Unraid

The **Unraid API** integration allows users to integrate their [Unraid](https://unraid.net/) server using Unraids local GraphQL API.

## Install the Integration

1. Go to the HACS -> Custom Repositories and add this repository as a Custom Repository [See HACS Documentation for help](https://hacs.xyz/docs/faq/custom_repositories/)

2. Click the button bellow and click 'Download' to install the Integration:

    [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=unraid_api&owner=chris-mc1)

3. Restart Home Assistant.

## Prerequisites

- Unraid v7.2 or later
- Create an [API Key](https://docs.unraid.net/API/how-to-use-the-api/#managing-api-keys) with this Template:

```txt
?name=Homeassistant&scopes=disk%2Binfo%2Bservers%2Bshare%3Aread_any%2Carray%2Bdocker%3Aread_any%2Bupdate_any&description=Unraid+API+Homeassistant+integration
```

or set permissions manually:

- Read (All):
  - Info
  - Servers
  - Array
  - Disk
  - Share
  - Docker

- Update (All):
  - Array
  - Docker

## Setup

1. Click the button below or use "Add Integration" in Home Assistant and select "Unraid".

  [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=unraid_api)

1. Enter the URL of the Unraid WebUI including "http(s)://" and the port when using a nonstandard port. You must use https when "Use SSL/TLS:" is set to "Yes" or "Strict" in the Unraid Management access settings.
2. Enter your API Key
3. Select which aspects of your Server to monitor

### Configuration parameters

- Unraid WebUI: URL of the Unraid WebUI (including "http(s)://")
- API Key: API Key for the Unraid API
- Monitor Shares: Create Entities for each Network Share
- Monitor Disks: Create Entities for each Disk
- Monitor Docker Containers: [Docker mode](#docker)

### Docker

Each monitored container must have a unique name. By default the container name is used, but can be overwritten by setting the `io.home-assistant.unraid_api.name` label on the container.

Docker modes:

- Disabled: Docker monitoring is disabled
- All (Ignore labels): All container are monitored, regardless of their label.
- Enabled with Label only: Only Container with `io.home-assistant.unraid_api.name=true` are monitored
- All except disabled with Label: All container are monitored, Container with `io.home-assistant.unraid_api.name=false` are excluded

All supported Docker Labels:

- `io.home-assistant.unraid_api.monitor`: Enabled or disable monitoring for this container.
- `io.home-assistant.unraid_api.name`: Overwrite container name
- `net.unraid.docker.webui`: WebUI Url in Device page
- `org.opencontainers.image.version`: Software version shown in Device page and as an extra state attribute

## Entities

- Sensors:
  - Array: State, Usage, Free space, Used space
  - RAM: Usage, Free, Used
  - CPU: Utilization, Temperature, Power
  - Parity check: Status, Progress, Speed
  - Disks: Status, Temperature, Usage, Free space, Used space, Spinning
  - Shares: Free space
  - UPS: Status, Level, Runtime, Health, Load, Input voltage, Output voltage
  - Docker Container: State

- Buttons:
  - Parity check: Start, Stop, Pause, Resume

- Switches:
  - Docker Container: Start/Stop

## Remove integration

This integration follows standard integration removal, no extra steps are required.
