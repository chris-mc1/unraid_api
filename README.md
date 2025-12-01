# Unraid API Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![GitHub Release](https://img.shields.io/github/v/release/ruaan-deysel/unraid_api?include_prereleases)](https://github.com/ruaan-deysel/unraid_api/releases)
[![License](https://img.shields.io/github/license/ruaan-deysel/unraid_api)](LICENSE)

A Home Assistant custom integration for monitoring [Unraid](https://unraid.net/) servers via the local GraphQL API. Get real-time insights into your array, disks, shares, CPU, RAM, UPS, and system uptime.

## ✨ Features

- **Array Monitoring** - State (started/stopped/syncing) and usage percentage
- **System Metrics** - CPU utilization, RAM usage, CPU temperature and power consumption
- **Disk Monitoring** - Temperature, standby state, and usage for all disks including cache
- **Share Monitoring** - Free space tracking for each network share
- **UPS Monitoring** - Battery level, load percentage, and runtime remaining
- **Uptime Tracking** - Human-readable server uptime with boot timestamp
- **VM Control** - Start/stop virtual machines with state monitoring
- **Docker Control** - Start/stop Docker containers with state monitoring

## 📋 Requirements

- **Unraid v7.2** or later (API v4.20.0+)
- **Home Assistant 2024.1** or later
- **HACS** (Home Assistant Community Store)

## 🚀 Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** (menu) → **Custom repositories**
3. Add this repository URL with category **Integration**
4. Click **Download** to install

[![Open HACS Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=unraid_api&owner=ruaan-deysel)

5. **Restart Home Assistant**

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/ruaan-deysel/unraid_api/releases)
2. Extract and copy `custom_components/unraid_api` to your `config/custom_components/` directory
3. Restart Home Assistant

## 🔑 Creating an API Key

Before setup, create an API key on your Unraid server:

### Quick Method

Use this pre-configured link (replace `YOUR_SERVER` with your Unraid IP/hostname):

```
http://YOUR_SERVER/Settings/ManagementAccess/ApiKeys/new?name=HomeAssistant&scopes=array%2Bdisk%2Binfo%2Bservers%2Bshare%2Bups%2Bdocker%2Bvms%3Aread_write&description=Home+Assistant+Integration
```

### Manual Method

1. Go to **Settings** → **Management Access** → **API Keys** in Unraid
2. Create a new key with these permissions:

| Resource | Permission |
|----------|------------|
| Info     | Read       |
| Servers  | Read       |
| Array    | Read       |
| Disk     | Read       |
| Share    | Read       |
| UPS      | Read       |
| Docker   | Read/Write |
| VMs      | Read/Write |

## ⚙️ Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Unraid" and select it

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=unraid_api)

3. Enter your configuration:

| Field | Description |
|-------|-------------|
| **Unraid WebUI URL** | Full URL including protocol (e.g., `http://192.168.1.100` or `https://tower.local`) |
| **API Key** | The API key created above |
| **Verify SSL** | Enable for HTTPS connections with valid certificates |

4. Choose monitoring options:

| Option | Description |
|--------|-------------|
| **Monitor Disks** | Create entities for each disk (temperature, state, usage) |
| **Monitor Shares** | Create entities for each network share (free space) |

> **Note:** The integration automatically detects SSL redirects, so HTTP URLs will work even if your server redirects to HTTPS.

## 📊 Available Entities

### Core Sensors

| Entity | Description |
|--------|-------------|
| Array State | Current state (started, stopped, syncing, etc.) |
| Array Usage | Percentage of used space |
| CPU Usage | Current CPU utilization percentage |
| CPU Temperature | Processor temperature (v4.26.0+) |
| CPU Power | Processor power consumption in watts (v4.26.0+) |
| RAM Usage | Memory utilization percentage |
| Uptime | Human-readable uptime (e.g., "8 days, 1 hour, 28 minutes") |

### UPS Sensors (if UPS connected)

| Entity | Description |
|--------|-------------|
| UPS Battery | Battery charge percentage |
| UPS Load | Current load percentage |
| UPS Runtime | Estimated runtime remaining |

### Disk Entities (per disk, when enabled)

| Entity | Type | Description |
|--------|------|-------------|
| Temperature | Sensor | Current disk temperature |
| Standby | Binary Sensor | Whether disk is spun down |
| Usage | Sensor | Percentage of used space |

### Share Entities (per share, when enabled)

| Entity | Description |
|--------|-------------|
| Free Space | Available space on the share |

### VM Switches (per virtual machine)

| Entity | Description |
|--------|-------------|
| VM {name} | Switch to start/stop the VM, shows running state |

### Docker Switches (per container)

| Entity | Description |
|--------|-------------|
| Container {name} | Switch to start/stop the container, shows running state |

## 🔄 API Version Support

The integration automatically detects your Unraid API version and enables features accordingly:

| API Version | Features |
|-------------|----------|
| 4.20.0+ | Core functionality (array, disks, shares, RAM, CPU usage) |
| 4.26.0+ | Additional CPU temperature and power consumption sensors |

## 🛠️ Troubleshooting

### Connection Issues

- Ensure the Unraid WebUI is accessible from your Home Assistant instance
- Check that the API key has the correct permissions
- For HTTPS, ensure certificates are valid or disable SSL verification

### Missing Sensors

- UPS sensors only appear if a UPS is connected and configured in Unraid
- CPU temperature/power requires Unraid API v4.26.0 or later
- Disk/share sensors require enabling the respective monitoring options

### Reauthentication

If your API key expires or becomes invalid, Home Assistant will prompt for reauthentication. Simply enter a new valid API key.

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
