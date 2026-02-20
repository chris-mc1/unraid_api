"""Fixtures for testing."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestClient, TestServer
from custom_components.unraid_api.api import GRAPHQL_WS_PROTOCOL, GraphQLWebsocketMessageType

from .api_states import API_STATE_LATEST, ApiState

if TYPE_CHECKING:
    from collections.abc import (
        AsyncGenerator,
        Awaitable,
        Callable,
        Generator,
    )

    from awesomeversion import AwesomeVersion
    from custom_components.unraid_api.models import (
        CpuMetricsSubscription,
        Disk,
        DockerContainer,
        MemorySubscription,
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


class EventMock(Mock):
    """
    Mock with internal Event.

    The Event is set and cleared every time the mock is called.
    """

    def __init__(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        self._call_event = asyncio.Event()
        self.wait = self._call_event.wait

    def __call__(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> Any:
        return_value = super().__call__(*args, **kwargs)
        self._call_event.set()
        self._call_event.clear()
        return return_value


class GraphqlServerMocker:
    """Mock GraphQL client requests."""

    ws: web.WebSocketResponse | None = None

    def __init__(self, response_set: type[GraphqlResponses]) -> None:
        self.responses = response_set()
        self.app = web.Application()
        self.app.add_routes(
            [web.post("/graphql", self.handler), web.get("/graphql", self.websocket_handler)]
        )
        self.server = TestServer(self.app, skip_url_asserts=True)
        self.clients = set[ClientSession]()

        self._ws_msg = list[str]()
        self._ws_subscriptions = dict[str, str]()

    async def handler(self, request: web.Request) -> web.Response:
        body = await request.json()
        query: str = body["query"]
        query = query.split(" ", maxsplit=2)[1].split("(", maxsplit=1)[0]
        response = self.responses.get_response(query)
        return web.json_response(data=response)

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(
            heartbeat=2,
            protocols=(GRAPHQL_WS_PROTOCOL,),
        )
        await ws.prepare(request)
        self.ws = ws
        while not ws.closed:
            async for msg in ws:
                if msg.type != web.WSMsgType.TEXT:
                    continue
                message = msg.json()
                self._ws_msg.append(message)
                if message["type"] == GraphQLWebsocketMessageType.CONNECTION_INIT:
                    await ws.send_json({"type": GraphQLWebsocketMessageType.CONNECTION_ACK.value})
                elif message["type"] == GraphQLWebsocketMessageType.SUBSCRIBE:
                    query: str = message["payload"]["query"]
                    query = query.split(" ")[1]
                    self._ws_subscriptions[query] = message["id"]
                    response = self.responses.get_subscription(query)
                    await self.ws.send_json(
                        {
                            "id": message["id"],
                            "type": GraphQLWebsocketMessageType.NEXT.value,
                            "payload": {"data": response},
                        }
                    )
        self.ws = None
        return ws

    async def send_subscription(self, index: int = 0) -> None:
        for query, op_id in self._ws_subscriptions.items():
            response = self.responses.get_subscription(query, index)
            await self.ws.send_json(
                {
                    "id": op_id,
                    "type": GraphQLWebsocketMessageType.NEXT.value,
                    "payload": {"data": response},
                }
            )

    def create_session(self) -> TestClient:
        """Create a ClientSession that is bound to this mocker."""
        client = ClientSession()
        self.clients.add(client)
        return client

    async def start_server(self) -> None:
        await self.server.start_server()

    async def close(self) -> None:
        if self.ws:
            await self.ws.send_json({"type": GraphQLWebsocketMessageType.COMPLETE.value})
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
    websocket_connected = False
    cpu_usage_callback: Callable[[float], None]
    cpu_metrics_callback: Callable[[CpuMetricsSubscription]]
    memory_callback: Callable[[MemorySubscription]]

    def __init__(self, state: type[ApiState]) -> None:
        self.state = state()

        self.start_container = AsyncMock(return_value=self.state.docker[2])
        self.stop_container = AsyncMock(return_value=self.state.docker[0])

    @property
    def version(self) -> AwesomeVersion:
        return self.state.version

    async def start_websocket(self) -> None:
        pass

    async def stop_websocket(self) -> None:
        pass

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

    async def query_docker(self) -> list[DockerContainer]:
        return self.state.docker

    async def subscribe_cpu_usage(self, callback: Callable[[float], None]) -> None:
        self.cpu_usage_callback = callback

    async def subscribe_cpu_metrics(
        self, callback: Callable[[CpuMetricsSubscription], None]
    ) -> None:
        self.cpu_metrics_callback = callback

    async def subscribe_memory(self, callback: Callable[[MemorySubscription], None]) -> None:
        self.memory_callback = callback

    async def start_container(self, container_id: str) -> DockerContainer:
        pass

    async def stop_container(self, container_id: str) -> DockerContainer:
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
