"""API Subscribtions Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.api import get_api_client
from custom_components.unraid_api.models import CpuMetricsSubscription, MemorySubscription

from tests.conftest import EventMock

from .graphql_responses import API_RESPONSES, GraphqlResponses

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .conftest import GraphqlServerMocker


@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_subscribe_cpu_percent_total(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test cpu total Subscribtion."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )
    await api_client.start_websocket()
    assert api_client.websocket_connected

    callback_mock = EventMock()

    await api_client.subscribe_cpu_usage(callback_mock)
    await callback_mock.wait()
    callback_mock.assert_called_once_with(5.1)
    callback_mock.reset_mock()

    await mocker.send_subscription(1)
    await callback_mock.wait()
    callback_mock.assert_called_once_with(7.5)

    await api_client.stop_websocket()


@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_subscribe_cpu_metrics(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test cpu total Subscribtion."""
    if api_responses.version >= AwesomeVersion("4.26.0"):
        mocker = await mock_graphql_server(api_responses)
        session = mocker.create_session()
        api_client = await get_api_client(
            f"{mocker.server.host}:{mocker.server.port}", "test_key", session
        )

        await api_client.start_websocket()
        assert api_client.websocket_connected

        callback_mock = EventMock()

        await api_client.subscribe_cpu_metrics(callback_mock)
        await callback_mock.wait()
        callback_mock.assert_called_once_with(CpuMetricsSubscription(power=2.8, temp=31))
        callback_mock.reset_mock()

        await mocker.send_subscription(1)
        await callback_mock.wait()
        callback_mock.assert_called_once_with(CpuMetricsSubscription(power=3.5, temp=35))

        await api_client.stop_websocket()


@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_subscribe_memory(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test memory Subscribtion."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )
    await api_client.start_websocket()
    assert api_client.websocket_connected

    callback_mock = EventMock()

    await api_client.subscribe_memory(callback_mock)
    await callback_mock.wait()
    callback_mock.assert_called_once_with(
        MemorySubscription(
            total=16644698112,
            active=11771707392,
            available=4872990720,
            percent_total=70.72346589159935,
        )
    )

    callback_mock.reset_mock()
    await mocker.send_subscription(1)
    await callback_mock.wait()
    callback_mock.assert_called_once_with(
        MemorySubscription(
            total=16644698112,
            active=11964444672,
            available=4680253440,
            percent_total=71.88141588085776,
        )
    )

    await api_client.stop_websocket()
