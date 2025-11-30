"""Fixtures for testing."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from unittest import mock
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestClient, TestServer
from homeassistant.const import EVENT_HOMEASSISTANT_CLOSE

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterator

    from homeassistant.core import Event, HomeAssistant
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

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
        self.server = TestServer(self.app)
        self.clients = set[GraphqlServerMocker]()

    async def handler(self, request: web.Request) -> web.Response:
        body = await request.json()
        query: str = body["query"]
        query = query.split(" ")[1]
        response = self.responses.get_response(query)
        return web.json_response(data=response)

    def create_session(self, loop: AbstractEventLoop | None = None) -> TestClient:
        """Create a ClientSession that is bound to this mocker."""
        client = TestClient(self.server, loop=loop)
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


@contextmanager
def mock_aiohttp_client(mocker: GraphqlServerMocker) -> Iterator[AiohttpClientMocker]:
    """Context manager to mock aiohttp client."""

    def create_session(hass: HomeAssistant, *args: Any, **kwargs: Any) -> ClientSession:  # noqa: ARG001
        session = mocker.create_session(hass.loop)

        async def close_session(event: Event) -> None:  # noqa: ARG001
            """Close session."""
            await session.close()

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_CLOSE, close_session)

        return session

    with mock.patch(
        "homeassistant.helpers.aiohttp_client._async_create_clientsession",
        side_effect=create_session,
    ):
        yield mocker
