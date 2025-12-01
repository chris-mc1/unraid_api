# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration for monitoring Unraid servers via the Unraid GraphQL API. It provides sensors for array status, disk monitoring, share monitoring, CPU/RAM metrics, and temperature monitoring.

## Development Commands

### Initial Setup
```bash
# Run setup script to install all dependencies with latest versions
bash script/setup.sh

# This will:
# - Install/upgrade uv package manager
# - Create virtual environment in .venv/
# - Install latest Home Assistant and all dependencies
# - Install test dependencies
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=custom_components.unraid_api --cov-report=term-missing

# Run specific test file
pytest tests/test_sensor.py

# Run specific test
pytest tests/test_sensor.py::test_sensor_entity
```

### Code Quality
```bash
# Format and lint code
ruff check custom_components/
ruff format custom_components/

# Format and lint tests
ruff check tests/
ruff format tests/
```

### Development Environment
The project uses Python 3.13.2+ and includes a dev container configuration. Dependencies are managed via `pyproject.toml` with separate dependency groups for dev and test.

**Important**: Dependencies are configured to always use the latest stable versions:
- Home Assistant: Always installs latest stable release (currently 2025.11.3)
- All other dependencies: Use latest compatible versions without pinning
- The `script/setup.sh` uses `uv sync --upgrade` to ensure latest versions on every setup

### Running Home Assistant for Testing

Port 8123 is automatically forwarded in the devcontainer for testing your integration with a local Home Assistant instance.

## Architecture

### Entry Point Flow
1. **Config Entry Setup** (`__init__.py`): `async_setup_entry()` initializes the integration
   - Creates API client with version detection via `get_api_client()`
   - Queries server info and validates connection/auth
   - Creates coordinator and device info
   - Forwards setup to platform modules (sensor, binary_sensor)

2. **Version-Based API Client** (`api/__init__.py`):
   - Base class `UnraidApiClient` provides core GraphQL functionality
   - `get_api_client()` detects API version and dynamically imports correct subclass
   - Version-specific implementations in `api/v4_20.py`, `api/v4_26.py` etc.
   - Minimum supported version: 4.20.0

3. **Data Coordinator** (`coordinator.py`):
   - `UnraidDataUpdateCoordinator` manages data fetching every 1 minute
   - Uses `asyncio.TaskGroup` to fetch metrics, array, disks, and shares in parallel
   - Implements callback system for dynamic entity addition (`subscribe_disks`, `subscribe_shares`)
   - Handles all exception types with proper translation keys for user-facing errors

### Entity Architecture

**Sensor Platform** (`sensor.py`):
- Server-level sensors: array state/usage, RAM, CPU (temp, utilization, power)
- Disk sensors: status, temperature, usage (created dynamically via callbacks)
- Share sensors: free space with attributes (created dynamically via callbacks)
- Entity descriptions use `value_fn` callbacks for data extraction
- Parity disks don't get space usage sensors (only status/temp)

**Binary Sensor Platform** (`binary_sensor.py`):
- Disk spinning state (moving device class)
- Also uses callback-based dynamic entity creation

### Data Models (`models.py`)
All API responses are validated as dataclasses:
- `ServerInfo`, `Metrics`, `Array`, `Disk`, `Share`
- Enums: `DiskStatus`, `DiskType`, `ArrayState`

### Config Flow (`config_flow.py`)
- Two-step flow: user credentials → options (drives/shares monitoring)
- Validates connection during setup with comprehensive error handling
- Supports reauth flow for API key updates
- Options flow allows toggling disk/share monitoring

### Error Handling Pattern
All modules use exception groups (`except*`) for handling:
- `ClientConnectorSSLError`: SSL verification issues
- `ClientConnectionError`/`TimeoutError`: Connection failures
- `UnraidAuthError`: Invalid API key (triggers reauth)
- `UnraidGraphQLError`: GraphQL errors from Unraid
- `IncompatibleApiError`: Unsupported API version
- `ValidationError`: Invalid data structure from API

Errors use translation keys from `custom_components/unraid_api/translations/en.json`

## Testing Architecture

### Test Setup (`tests/conftest.py`)
- `GraphqlServerMocker`: Custom aiohttp test server that mocks GraphQL responses
- `mock_aiohttp_client`: Context manager that patches Home Assistant's client session
- Response classes in `tests/graphql_responses.py` define API mock data
- Tests use pytest-homeassistant-custom-component framework

### Testing Pattern
Tests follow this structure:
1. Create GraphQL mocker with response set
2. Use `mock_aiohttp_client` context manager
3. Set up config entry with mocker's host
4. Assert entities are created with correct state/attributes

Run tests with `pytest` - async tests auto-detected via `asyncio_mode = "auto"` in pyproject.toml.

## Key Integration Points

### Home Assistant Integration Type
- Integration type: `device` (represents physical Unraid server)
- IoT class: `local_polling` (polls local API every minute)
- Platforms: SENSOR, BINARY_SENSOR

### Config Entry Runtime Data
Uses typed `UnraidConfigEntry = ConfigEntry[UnraidData]` pattern where `UnraidData` contains:
- `coordinator`: The data update coordinator
- `device_info`: Device metadata for entity registry

### Dynamic Entity Addition
Disks and shares are added dynamically as they appear in API responses:
- Coordinator maintains `known_disks`/`known_shares` sets
- On first appearance, callbacks fire to create entities
- Allows hot-plugging of disks/shares without reload

## Common Patterns

### Adding New Sensor
1. Define `UnraidSensorEntityDescription` in sensor.py with `value_fn` callback
2. Add to appropriate tuple (SENSOR_DESCRIPTIONS, DISK_SENSOR_DESCRIPTIONS, etc.)
3. Add translation key to `translations/en.json`
4. Set `min_version` if requires specific API version
5. Use `extra_values_fn` for additional attributes

### Adding New API Query
1. Add query string constant to version-specific API file (e.g., `api/v4_26.py`)
2. Define Pydantic models for response validation
3. Add abstract method to base `UnraidApiClient` class
4. Implement in version-specific subclass
5. Update models.py with dataclass for processed data

### Version Compatibility
- Each entity description has `min_version` field
- Entities only created if coordinator's API version >= min_version
- New API versions get new files in `api/` directory
- Version detection happens during `get_api_client()` initialization
