# Unraid

The **Unraid** integration allows users to integrate their [Unraid](https://www.home-connect.com/global) server using Unraids local GraphQL API.

## Install the Integration

1. Go to the HACS -> Custom Repositories and add this repository as a Custom Repository [See HACS Documentation for help](https://hacs.xyz/docs/faq/custom_repositories/)

2. Click the button bellow and click 'Download' to install the Integration:

    [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=unraid_hass&owner=chris-mc1)

3. Restart Home Assistant.

## Prerequisites

- Install the [Unraid Connect Plugin](https://docs.unraid.net/connect/) on your Unraid server
- Enable the [developer mode](https://docs.unraid.net/API/cli/#developer-mode)
- Create an [API Key](https://docs.unraid.net/API/how-to-use-the-api/#creating-an-api-key) with role: "admin" and permissions:

  - array: read
  - info: read
  - shares: read

## Setup

1. Click the button below or use "Add Integration" in Home Assistant and select "Unraid".

    [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=unraid_hass)

2. Enter the URL of the Unraid WebUI and your API Key
3. Select if you want to monitor disk and shares

### Configuration parameters

- Unraid WebUI: URL of the Unraid WebUI (including "http(s)://")
- API Key: API Key for the Unraid API
- Monitor Shares: Create Entities for each Network Share
- Monitor Disks: Create Entities for each Disk

## Entities

- State of the Array ("Stopped", "Started", ...)
- Percentage of used space on the Array
- Percentage of used RAM

- When "Monitor Shares" enabled:

  - Free space for each Share

- When "Monitor Disks" enabled, for each Disk, including Cache disks:

  - State of the Disk
  - Disk Temperature (Temperature is unknown for spun down disk)
  - Percentage of used space on the Disk

## Remove integration

This integration follows standard integration removal, no extra steps are required.
