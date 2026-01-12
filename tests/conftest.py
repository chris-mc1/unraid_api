"""Fixtures for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestClient, TestServer

from .api_states import API_STATE_LATEST, ApiState

if TYPE_CHECKING:
    from collections.abc import (
        AsyncGenerator,
        AsyncIterator,
        Awaitable,
        Callable,
        Generator,
    )

    from awesomeversion import AwesomeVersion
    from custom_components.unraid_api.models import (
        Disk,
        MetricsArray,
        ServerInfo,
        Share,
        UpsDevice,
    )

    from .graphql_responses import GraphqlResponses

pytest_plugins = ["aiohttp.pytest_plugin"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:  # noqa: ARG001
    """Enable custom integrations defined in the test dir."""
    return


class GraphqlServerMocker:
    """Mock GraphQL client requests."""

    def __init__(self, response_set: type[GraphqlResponses]) -> None:
        self.responses = response_set()
        self.app = web.Application()
        self.app.add_routes([web.post("/graphql", self.handler)])
        self.server = TestServer(self.app, skip_url_asserts=True)
        self.clients = set[ClientSession]()

    async def handler(self, request: web.Request) -> web.Response:
        body = await request.json()
        query: str = body["query"]
        query = query.split(" ")[1]
        response = self.responses.get_response(query)
        return web.json_response(data=response)

    def create_session(self) -> TestClient:
        """Create a ClientSession that is bound to this mocker."""
        client = ClientSession()
        self.clients.add(client)
        return client

    async def start_server(self) -> None:
        await self.server.start_server()

    async def close(self) -> None:
        while self.clients:
            await self.clients.pop().close()
        await self.server.close()

    @property
    def host(self) -> str:
        return f"http://{self.server.host}:{self.server.port}"


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.unraid_api.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


# From https://github.com/home-assistant/core/blob/6357067f0f427abd995697aaa84fa9ed3e126aef/tests/components/conftest.py#L85
@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Test fixture that ensures all entities are enabled in the registry."""
    with (
        patch(
            "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
            return_value=True,
        ),
        patch(
            "homeassistant.components.device_tracker.config_entry.ScannerEntity.entity_registry_enabled_default",
            return_value=True,
        ),
    ):
        yield


@pytest_asyncio.fixture
async def mock_graphql_server(
    socket_enabled: None,  # noqa: ARG001
) -> AsyncGenerator[Callable[..., Awaitable[GraphqlServerMocker]]]:
    """Graphql Server."""
    mocks = set[GraphqlServerMocker]()

    async def go(response_set: dict) -> GraphqlServerMocker:
        mocker = GraphqlServerMocker(response_set)
        mocks.add(mocker)
        await mocker.start_server()
        return mocker

    yield go

    while mocks:
        await mocks.pop().close()


class MockApiClient:
    """Mock GraphQL API Client."""

    state: ApiState

    def __init__(self, state: type[ApiState]) -> None:
        self.state = state()

    @property
    def version(self) -> AwesomeVersion:
        return self.state.version

    async def query_server_info(self) -> ServerInfo:
        return self.state.server_info

    async def query_metrics_array(self) -> MetricsArray:
        return self.state.metrics_array

    async def query_shares(self) -> list[Share]:
        return self.state.shares

    async def query_disks(self) -> list[Disk]:
        return self.state.disks

    async def query_ups(self) -> list[UpsDevice]:
        return self.state.ups

    async def subscribe_cpu_total(self) -> AsyncIterator[float]:
        pass


@pytest.fixture
def mock_api_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[MagicMock]:
    """Override get_api_client."""
    mock_api_client = AsyncMock(return_value=MockApiClient(API_STATE_LATEST))
    with monkeypatch.context() as m:
        m.setattr("custom_components.unraid_api.config_flow.get_api_client", mock_api_client)
        m.setattr("custom_components.unraid_api.get_api_client", mock_api_client)
        yield mock_api_client
