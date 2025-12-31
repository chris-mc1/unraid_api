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
  ?name=Homeassistant&scopes=array%2Bdisk%2Binfo%2Bservers%2Bshare%2Bdocker%3Aread_any%2Bdocker%3Aupdate_any&description=Unraid+API+Homeassistant+integration
  ```

  or set permissions manually:
  - Resources:
    - Info
    - Servers
    - Array
    - Disk
    - Share
    - Docker

  - Actions: 
    - Read (All) for Info, Servers, Array, Disk, Share
    - Read (All) and Update (All) for Docker (if you want to control containers)

## Setup

1. Click the button below or use "Add Integration" in Home Assistant and select "Unraid".

    [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=unraid_api)

2. Enter the URL of the Unraid WebUI and your API Key
3. Select if you want to monitor disks, shares, and Docker containers

### Configuration parameters

- Unraid WebUI: URL of the Unraid WebUI (including "http(s)://")
- API Key: API Key for the Unraid API
- Monitor Shares: Create Entities for each Network Share
- Monitor Disks: Create Entities for each Disk
- Monitor Docker containers: Create Switch entities for each Docker container

## Entities

- State of the Array ("Stopped", "Started", ...)
- Percentage of used space on the Array
- Percentage of used RAM
- CPU utilization

- When "Monitor Shares" enabled:

  - Free space for each Share

- When "Monitor Disks" enabled, for each Disk, including Cache disks:

  - State of the Disk
  - Disk Temperature (Temperature is unknown for spun down disk)
  - Disk spinning
  - Percentage of used space on the Disk

- When "Monitor Docker containers" enabled, for each Docker container:

  - Switch entity to start/stop the container
  - Container state (running/stopped)
  - Container status (e.g., "Up 5 weeks")
  - Container image name
  - Auto-start setting
  - All information available in entity attributes

## Remove integration

This integration follows standard integration removal, no extra steps are required.
