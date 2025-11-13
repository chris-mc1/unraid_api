"""Fixtures for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from custom_components import unraid_api
from custom_components.unraid_api import config_flow

from .const import CLIENT_RESPONSES

if TYPE_CHECKING:
    from collections.abc import Generator

    from awesomeversion import AwesomeVersion
    from custom_components.unraid_api.models import Array, Disk, Metrics, ServerInfo, Share

pytest_plugins = ["aiohttp.pytest_plugin"]


class MockAPIClient:
    """Mock Unraid GraphQL API Client."""

    def __init__(self, responses: dict) -> None:
        self.responses = responses

    async def query_api_version(self) -> AwesomeVersion:
        return self.responses["api_version"]

    async def query_server_info(self) -> ServerInfo:
        return self.responses["server_info"]

    async def query_metrics(self) -> Metrics:
        return self.responses["metrics"]

    async def query_shares(self) -> list[Share]:
        return self.responses["shares"]

    async def query_disks(self) -> list[Disk]:
        return self.responses["disks"]

    async def query_array(self) -> Array:
        return self.responses["array"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:  # noqa: ARG001
    """Enable custom integrations defined in the test dir."""
    return


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.unraid_api.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture(params=CLIENT_RESPONSES)
def mock_get_api_client(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[AsyncMock]:
    """Override get_api_client."""
    mock_get_api_client = AsyncMock(return_value=MockAPIClient(request.param))
    monkeypatch.setattr(unraid_api, "get_api_client", mock_get_api_client)
    monkeypatch.setattr(config_flow, "get_api_client", mock_get_api_client)
    return mock_get_api_client
