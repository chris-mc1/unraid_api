# Copilot Instructions

Home Assistant custom integration for monitoring Unraid servers via GraphQL API. Provides sensors for array, disks, shares, CPU, and RAM.

## Development Setup

```bash
bash script/setup.sh    # Install deps with uv (always uses latest versions)
bash script/develop.sh  # Start HA instance for debugging (port 8123)
bash script/lint.sh     # Format and lint (ruff format + ruff check --fix)
pytest                   # Run tests
pytest --cov=custom_components.unraid_api --cov-report=term-missing  # With coverage
```

**Critical**: Zero tolerance for linting errors. Always run `bash script/lint.sh` before committing. Check HA logs in the terminal running `develop.sh` for integration issues.

## Architecture

### Entry Flow
1. `__init__.py`: `async_setup_entry()` → creates API client via `get_api_client()` with version detection
2. `api/__init__.py`: Base `UnraidApiClient` + dynamic subclass selection based on API version (≥4.20.0)
3. `coordinator.py`: `UnraidDataUpdateCoordinator` fetches data every 1 min using `asyncio.TaskGroup` for parallel queries
4. Platforms: `sensor.py`, `binary_sensor.py` create entities

### Version-Specific API Pattern
Each Unraid API version gets its own file in `api/` inheriting from the previous:
```
api/__init__.py  → Base UnraidApiClient + get_api_client() version detection
api/v4_20.py     → UnraidApiV420 (minimum supported, implements all queries)
api/v4_26.py     → UnraidApiV426(UnraidApiV420) (adds CPU temp/power to metrics)
```

**Why version files over feature flags**: Clean separation, easier testing, no runtime conditionals scattered throughout. Each file is self-contained with its GraphQL queries and Pydantic response models.

**Adding a new API version**:
1. Create `api/v4_XX.py` inheriting from previous version
2. Set `version = AwesomeVersion("4.XX.0")`
3. Override only the methods with changed queries
4. Update `_import_client_class()` in `api/__init__.py`

### Config Flow Pattern
Two-step flow in `config_flow.py`:
1. **User step** (`async_step_user`): Collects host, API key, SSL verify → validates connection
2. **Options step** (`async_step_options`): Toggles for disk/share monitoring

**Reauth flow**: When API key becomes invalid, `async_step_reauth` → `async_step_reauth_key` allows updating credentials without reconfiguration.

**Options flow** (`UnraidOptionsFlow`): Post-setup toggle of disk/share monitoring via `OptionsFlowWithReload`.

### GraphQL Query Pattern
Queries are defined as constants in version-specific API files:
```python
# In api/v4_26.py
METRICS_QUERY = """
query Metrics {
  metrics { memory { free total } cpu { percentTotal } }
  info { cpu { packages { power temp } } }
}
"""

class MetricsQuery(BaseModel):  # Pydantic model for response validation
    metrics: _Metrics
    info: Info
```
Call with: `response = await self.call_api(METRICS_QUERY, MetricsQuery)`

### Dynamic Entity Creation
Disks/shares are added dynamically via callback pattern:
```python
# coordinator.py maintains known_disks/known_shares sets
# On new disk/share, fires callbacks to create entities at runtime
coordinator.subscribe_disks(callback_fn)
```

## Key Patterns

### Adding a Sensor
1. Define `UnraidSensorEntityDescription` in `sensor.py` with `value_fn` callback:
   ```python
   UnraidSensorEntityDescription(
       key="my_sensor",
       value_fn=lambda coordinator: coordinator.data["metrics"].my_value,
       min_version=AwesomeVersion("4.26.0"),  # Optional: version gate
   )
   ```
2. Add to `SENSOR_DESCRIPTIONS` tuple
3. Add translation key to `translations/en.json`

### Error Handling
Use exception groups (`except*`) pattern consistently in coordinator:
```python
except* UnraidAuthError as exc:
    raise ConfigEntryAuthFailed(translation_domain=DOMAIN, translation_key="auth_failed") from exc
```
All errors use translation keys from `translations/en.json`.

### Data Models
- `models.py`: Dataclasses for API response data (`ServerInfo`, `Metrics`, `Array`, `Disk`, `Share`)
- API files: Pydantic models for raw GraphQL response validation, converted to dataclasses

## Testing

Tests use `pytest-homeassistant-custom-component` framework with custom GraphQL mocker:
```python
# tests/conftest.py: GraphqlServerMocker mocks GraphQL responses
# tests/graphql_responses.py: Response data classes

async def test_sensor(hass, mock_graphql_server):
    mocker = await mock_graphql_server(API_RESPONSES_LATEST)
    assert await setup_config_entry(hass, mocker)
    state = hass.states.get("sensor.test_server_array_state")
```

## Changelog

**Always update `CHANGELOG.md`** when making changes. Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format:
- Add new features under `### Added`
- Document modifications under `### Changed`
- Note bug fixes under `### Fixed`
- List removals under `### Removed`

Keep changes in `[Unreleased]` section until a version is released.

## File Reference

- `CHANGELOG.md`: Track all notable changes (keep updated!)
- `const.py`: Domain, platforms, config keys
- `config_flow.py`: Two-step setup (credentials → options) + reauth flow
- `manifest.json`: Integration metadata, requirements
