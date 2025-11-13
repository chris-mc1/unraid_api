"""API Client Tests."""

from asyncio import AbstractEventLoop

import pytest
from custom_components.unraid_api.api import (
    IncompatibleApiError,
    UnraidApiClient,
    get_api_client,
)
from custom_components.unraid_api.api.v4_20 import UnraidApiV420
from custom_components.unraid_api.models import ArrayState, DiskStatus, DiskType
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .const import (
    API_VERSION_RESPONSE_INCOMPATIBLE,
)
from .graphql_responses import API_RESPONSES, API_VERSION_RESPONSE_V4_20


@pytest.mark.parametrize(
    ("api_response", "api_client_type"), [(API_VERSION_RESPONSE_V4_20, UnraidApiV420)]
)
async def test_get_api_client(
    api_response: dict, api_client_type: type[UnraidApiClient], loop: AbstractEventLoop
) -> None:
    """Test get_api_client."""
    aioclient_mock = AiohttpClientMocker()
    session = aioclient_mock.create_session(loop)
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_response,
        headers={"Content-Type": "application/json"},
    )

    api_client = await get_api_client("http://1.2.3.4", "test_key", session)

    assert type(api_client) is api_client_type


async def test_get_api_client_incompatible(loop: AbstractEventLoop) -> None:
    """Test get_api_client with incompatible version."""
    aioclient_mock = AiohttpClientMocker()
    session = aioclient_mock.create_session(loop)
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=API_VERSION_RESPONSE_INCOMPATIBLE,
        headers={"Content-Type": "application/json"},
    )

    with pytest.raises(IncompatibleApiError):
        await get_api_client("http://1.2.3.4", "test_key", session)


@pytest.mark.parametrize(("api_responses"), API_RESPONSES)
async def test_api_version(api_responses: dict, loop: AbstractEventLoop) -> None:
    """Test querying api version."""
    aioclient_mock = AiohttpClientMocker()
    session = aioclient_mock.create_session(loop)

    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["api_version"],
        headers={"Content-Type": "application/json"},
    )
    api_client = UnraidApiClient("http://1.2.3.4", "test_key", session)
    api_version = await api_client.query_api_version()

    assert api_version == api_responses["version"]


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_server_info(api_responses: dict, loop: AbstractEventLoop) -> None:
    """Test querying server info."""
    aioclient_mock = AiohttpClientMocker()
    session = aioclient_mock.create_session(loop)
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["api_version"],
        headers={"Content-Type": "application/json"},
    )
    api_client = await get_api_client("http://1.2.3.4", "test_key", session)

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["server_info"],
        headers={"Content-Type": "application/json"},
    )
    server_info = await api_client.query_server_info()

    assert server_info.localurl == "http://1.2.3.4"
    assert server_info.unraid_version == "7.0.1"
    assert server_info.name == "Test Server"


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_metrics(api_responses: dict, loop: AbstractEventLoop) -> None:
    """Test querying metrics."""
    aioclient_mock = AiohttpClientMocker()
    session = aioclient_mock.create_session(loop)

    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["api_version"],
        headers={"Content-Type": "application/json"},
    )
    api_client = await get_api_client("http://1.2.3.4", "test_key", session)

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["metrics"],
        headers={"Content-Type": "application/json"},
    )
    metrics = await api_client.query_metrics()

    assert metrics.memory_free == 415510528
    assert metrics.memory_total == 16646950912
    assert metrics.memory_active == 12746354688
    assert metrics.memory_percent_total == 76.56870471583932
    assert metrics.memory_available == 3900596224
    assert metrics.cpu_percent_total == 5.1


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_shares(api_responses: dict, loop: AbstractEventLoop) -> None:
    """Test querying share info."""
    aioclient_mock = AiohttpClientMocker()
    session = aioclient_mock.create_session(loop)

    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["api_version"],
        headers={"Content-Type": "application/json"},
    )
    api_client = await get_api_client("http://1.2.3.4", "test_key", session)

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["shares"],
        headers={"Content-Type": "application/json"},
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
async def test_disks(api_responses: dict, loop: AbstractEventLoop) -> None:
    """Test querying disk info."""
    aioclient_mock = AiohttpClientMocker()
    session = aioclient_mock.create_session(loop)

    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["api_version"],
        headers={"Content-Type": "application/json"},
    )
    api_client = await get_api_client("http://1.2.3.4", "test_key", session)

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["disks"],
        headers={"Content-Type": "application/json"},
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


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_array(api_responses: dict, loop: AbstractEventLoop) -> None:
    """Test querying array info."""
    aioclient_mock = AiohttpClientMocker()
    session = aioclient_mock.create_session(loop)

    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["api_version"],
        headers={"Content-Type": "application/json"},
    )
    api_client = await get_api_client("http://1.2.3.4", "test_key", session)

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "http://1.2.3.4/graphql",
        json=api_responses["array"],
        headers={"Content-Type": "application/json"},
    )
    array = await api_client.query_array()

    assert array.state == ArrayState.STARTED
    assert array.capacity_free == 523094720
    assert array.capacity_used == 11474981430
    assert array.capacity_total == 11998076150
