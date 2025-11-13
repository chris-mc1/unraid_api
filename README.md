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
  ?name=Homeassistant&scopes=array%2Bdisk%2Binfo%2Bservers%2Bshare%2Bvms%2Bdocker%3Aread_any%2Cwrite_any&description=Unraid+API+Homeassistant+integration
  ```

  or set permissions manually:
  - Resources:
    - Info
    - Servers
    - Array
    - Disk
    - Share
    - VMs (for VM management)
    - Docker (for Docker management)

  - Actions: Read (All), Write (for VM/Docker control)

## Setup

1. Click the button below or use "Add Integration" in Home Assistant and select "Unraid".

    [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=unraid_api)

2. Enter the URL of the Unraid WebUI and your API Key
3. Select which resources you want to monitor (disks, shares, VMs, Docker containers)

### Configuration parameters

- Unraid WebUI: URL of the Unraid WebUI (including "http(s)://")
- API Key: API Key for the Unraid API
- Monitor Shares: Create Entities for each Network Share
- Monitor Disks: Create Entities for each Disk
- Monitor VMs: Create Entities for each Virtual Machine
- Monitor Docker: Create Entities for each Docker container

## Entities

### Server Entities

- State of the Array ("Stopped", "Started", ...)
- Percentage of used space on the Array
- Percentage of used RAM
- CPU utilization

### Share Entities

- When "Monitor Shares" enabled:

  - Free space for each Share

### Disk Entities

- When "Monitor Disks" enabled, for each Disk, including Cache disks:

  - State of the Disk
  - Disk Temperature (Temperature is unknown for spun down disk)
  - Disk spinning
  - Percentage of used space on the Disk
  - Spinning status (binary sensor)

### VM Entities

- When "Monitor VMs" enabled, for each Virtual Machine:

  **Sensors:**
  - VM State (running, stopped, paused, etc.)

  **Aggregate Sensors:**
  - VMs Total
  - VMs Running
  - VMs Stopped
  - VMs Paused

  **Controls:**
  - Power switch (start/stop VM)
  - Reboot button
  - Force stop button
  - Pause button
  - Resume button

### Docker Entities

- When "Monitor Docker" enabled, for each Docker container:

  **Sensors:**
  - Container State (running, stopped, paused, exited, etc.)
  - Extra attributes: image, autostart

  **Aggregate Sensors:**
  - Containers Total
  - Containers Running
  - Containers Stopped
  - Containers Paused

  **Controls:**
  - Power switch (start/stop container)

## Remove integration

This integration follows standard integration removal, no extra steps are required.
