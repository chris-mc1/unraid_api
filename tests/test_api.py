"""API Client Tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.api import IncompatibleApiError, UnraidApiClient, get_api_client
from custom_components.unraid_api.api import _normalize_url as normalize_url
from custom_components.unraid_api.models import ArrayState, DiskStatus, DiskType, ParityCheckStatus

from .graphql_responses import API_RESPONSES, GraphqlResponses, GraphqlResponses410

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .conftest import GraphqlServerMocker


@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_get_api_client(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test get_api_client."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )

    assert api_client.version == api_responses.version


async def test_get_api_client_incompatible(
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test get_api_client with incompatible version."""
    mocker = await mock_graphql_server(GraphqlResponses410)
    session = mocker.create_session()

    with pytest.raises(IncompatibleApiError):
        await get_api_client(f"{mocker.server.host}:{mocker.server.port}", "test_key", session)


@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_api_version(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test querying api version."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = UnraidApiClient(f"{mocker.server.host}:{mocker.server.port}", "test_key", session)

    api_version = await api_client.query_api_version()

    assert api_version == api_responses.version


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_server_info(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test querying server info."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )

    server_info = await api_client.query_server_info()

    assert server_info.localurl == "http://1.2.3.4"
    assert server_info.unraid_version == "7.0.1"
    assert server_info.name == "Test Server"


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_metrics_array(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test querying metrics and array."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )
    metrics_array = await api_client.query_metrics_array()

    assert metrics_array.memory_free == 415510528
    assert metrics_array.memory_total == 16646950912
    assert metrics_array.memory_active == 12746354688
    assert metrics_array.memory_percent_total == 76.56870471583932
    assert metrics_array.memory_available == 3900596224
    assert metrics_array.cpu_percent_total == 5.1
    assert metrics_array.state == ArrayState.STARTED
    assert metrics_array.capacity_free == 523094720
    assert metrics_array.capacity_used == 11474981430
    assert metrics_array.capacity_total == 11998076150

    assert metrics_array.parity_check_status == ParityCheckStatus.COMPLETED
    assert metrics_array.parity_check_date == datetime(
        year=2025, month=9, day=27, hour=22, minute=0, second=1, tzinfo=UTC
    )
    assert metrics_array.parity_check_duration == 5982
    assert metrics_array.parity_check_speed == 10
    assert metrics_array.parity_check_errors is None
    assert metrics_array.parity_check_progress == 0

    if api_responses.version >= AwesomeVersion("4.26.0"):
        assert metrics_array.cpu_power == 2.8
        assert metrics_array.cpu_temp == 31
    else:
        assert metrics_array.cpu_power is None
        assert metrics_array.cpu_temp is None


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_shares(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test querying share info."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )
    shares = await api_client.query_shares()

    assert shares[0].name == "Share_1"
    assert shares[0].free == 523094721
    assert shares[0].used == 11474981429
    assert shares[0].size == 0
    assert shares[0].allocator == "highwater"
    assert shares[0].floor == "20000000"

    assert shares[1].name == "Share_2"
    assert shares[1].free == 503491121
    assert shares[1].used == 5615496143
    assert shares[1].size == 0
    assert shares[1].allocator == "highwater"
    assert shares[1].floor == "0"


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_disks(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test querying disk info."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )
    disks = await api_client.query_disks()

    assert disks[0].name == "disk1"
    assert disks[0].status == DiskStatus.DISK_OK
    assert disks[0].temp == 34
    assert disks[0].fs_size == 5999038075
    assert disks[0].fs_free == 464583438
    assert disks[0].fs_used == 5534454637
    assert disks[0].type == DiskType.Data
    assert disks[0].id == "c6b"
    assert disks[0].is_spinning is True

    assert disks[1].name == "cache"
    assert disks[1].status == DiskStatus.DISK_OK
    assert disks[1].temp == 30
    assert disks[1].fs_size == 119949189
    assert disks[1].fs_free == 38907683
    assert disks[1].fs_used == 81041506
    assert disks[1].type == DiskType.Cache
    assert disks[1].id == "8e0"
    assert disks[1].is_spinning is True

    assert disks[2].name == "parity"
    assert disks[2].status == DiskStatus.DISK_OK
    assert disks[2].temp is None
    assert disks[2].fs_size is None
    assert disks[2].fs_free is None
    assert disks[2].fs_used is None
    assert disks[2].type == DiskType.Parity
    assert disks[2].id == "4d5"
    assert disks[2].is_spinning is False


def test_normalize_url() -> None:
    """Test URL normalization."""
    assert str(normalize_url("192.168.1.10")) == "http://192.168.1.10"
    assert str(normalize_url("http://192.168.1.10")) == "http://192.168.1.10"
    assert str(normalize_url("https://192.168.1.10")) == "https://192.168.1.10"
    assert str(normalize_url("192.168.1.10/graphql")) == "http://192.168.1.10"

    assert str(normalize_url("192.168.1.10:8080")) == "http://192.168.1.10:8080"
    assert str(normalize_url("http://192.168.1.10:8080")) == "http://192.168.1.10:8080"
    assert str(normalize_url("https://192.168.1.10:8080")) == "https://192.168.1.10:8080"
    assert str(normalize_url("192.168.1.10:8080/graphql")) == "http://192.168.1.10:8080"

    assert str(normalize_url("unraid.lan")) == "http://unraid.lan"
    assert str(normalize_url("http://unraid.lan")) == "http://unraid.lan"
    assert str(normalize_url("https://unraid.lan")) == "https://unraid.lan"
    assert str(normalize_url("unraid.lan/graphql")) == "http://unraid.lan"

    assert str(normalize_url("unraid.lan:8080")) == "http://unraid.lan:8080"
    assert str(normalize_url("http://unraid.lan:8080")) == "http://unraid.lan:8080"
    assert str(normalize_url("https://unraid.lan:8080")) == "https://unraid.lan:8080"
    assert str(normalize_url("unraid.lan:8080/graphql")) == "http://unraid.lan:8080"
