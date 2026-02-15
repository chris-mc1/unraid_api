"""API Client Tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import yarl
from awesomeversion import AwesomeVersion
from custom_components.unraid_api.api import IncompatibleApiError, UnraidApiClient, get_api_client
from custom_components.unraid_api.api import _normalize_url as normalize_url
from custom_components.unraid_api.api import _to_bool as to_bool
from custom_components.unraid_api.models import (
    ArrayState,
    ContainerState,
    DiskStatus,
    DiskType,
    ParityCheckStatus,
)

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


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_docker(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test querying docker."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )
    docker_containers = await api_client.query_docker()

    assert len(docker_containers) == 3

    ## Homeassistant

    assert (
        docker_containers[0].id
        == "4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:9591842fdb0e817f385407d6eb71d0070bcdfd3008506d5e7e53c3036939c2b0"  # noqa: E501
    )
    assert docker_containers[0].name == "homeassistant"
    assert docker_containers[0].state == ContainerState.RUNNING
    assert docker_containers[0].image == "ghcr.io/home-assistant/home-assistant:stable"
    assert (
        docker_containers[0].image_sha256
        == "e0477b544d48b26ad81e2132b8ce36f0a20dfd7eb44de9c40718fa78dc92e24d"
    )
    assert docker_containers[0].status == "Up 28 minutes"
    assert docker_containers[0].label_opencontainers_version == "2026.2.2"
    assert docker_containers[0].label_unraid_webui == yarl.URL("http://homeassistant.unraid.lan")
    assert docker_containers[0].label_monitor is None
    assert docker_containers[0].label_name is None

    ## Postgres

    assert (
        docker_containers[1].id
        == "4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:db6215c5578bd28bc78fab45e16b7a2d6d94ec3bb3b23a5ad5b8b4979e79bf86"  # noqa: E501
    )
    assert docker_containers[1].name == "postgres"
    assert docker_containers[1].state == ContainerState.RUNNING
    assert docker_containers[1].image == "postgres:15"
    assert (
        docker_containers[1].image_sha256
        == "a748a13f04094ee02b167d3e2a919368bc5e93cbd2b1c41a6d921dbaa59851ac"
    )
    assert docker_containers[1].status == "Up 28 minutes"
    assert docker_containers[1].label_opencontainers_version is None
    assert docker_containers[1].label_unraid_webui is None
    assert docker_containers[1].label_monitor is False
    assert docker_containers[1].label_name == "Postgres"
    ## Grafana

    assert (
        docker_containers[2].id
        == "4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:cc3843b7435c45ba8ff9c10b7e3c494d51fc303e609d12825b63537be52db369"  # noqa: E501
    )
    assert docker_containers[2].name == "grafana"
    assert docker_containers[2].state == ContainerState.EXITED
    assert docker_containers[2].image == "grafana/grafana-enterprise"
    assert (
        docker_containers[2].image_sha256
        == "32241300d32d708c29a186e61692ff00d6c3f13cb862246326edd4612d735ae5"
    )
    assert docker_containers[2].status == "Up 28 minutes"
    assert docker_containers[2].label_opencontainers_version is None
    assert docker_containers[2].label_unraid_webui is None
    assert docker_containers[2].label_monitor is True
    assert docker_containers[2].label_name == "Grafana Public"


@pytest.mark.parametrize("api_responses", API_RESPONSES)
async def test_start_stop_container(
    api_responses: GraphqlResponses,
    mock_graphql_server: Callable[..., Awaitable[GraphqlServerMocker]],
) -> None:
    """Test docker mutations."""
    mocker = await mock_graphql_server(api_responses)
    session = mocker.create_session()
    api_client = await get_api_client(
        f"{mocker.server.host}:{mocker.server.port}", "test_key", session
    )
    docker_containers = await api_client.query_docker()
    container = await api_client.stop_container(docker_containers[0].id)
    assert container.id == docker_containers[0].id
    assert container.state == ContainerState.EXITED

    container = await api_client.start_container(docker_containers[2].id)
    assert container.id == docker_containers[2].id
    assert container.state == ContainerState.RUNNING


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


def test_convert_bool() -> None:
    """Test str to bool."""
    assert to_bool("True") is True
    assert to_bool("true") is True
    assert to_bool("False") is False
    assert to_bool("false") is False

    assert to_bool(True) is True  # noqa: FBT003
    assert to_bool(False) is False  # noqa: FBT003

    assert to_bool(0) is False
    assert to_bool(1) is True
    assert to_bool(1.5) is True

    assert to_bool("0") is False
    assert to_bool("1") is True
    assert to_bool("1.5") is True

    assert to_bool(None) is None
    assert to_bool("") is None
    assert to_bool({}) is None
    assert to_bool("not bool") is None
