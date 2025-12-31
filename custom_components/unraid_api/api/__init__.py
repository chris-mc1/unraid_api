"""Unraid GraphQL API Client."""

from __future__ import annotations

import asyncio
import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from awesomeversion import AwesomeVersion
from pydantic import BaseModel, ValidationError
from yarl import URL

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from unraid_api.models import Array, Disk, DockerContainer, Metrics, ServerInfo, Share, UpsDevice

_LOGGER = logging.getLogger(__name__)


def normalize_url(host: str) -> str:
    """
    Normalize and validate the Unraid server URL.
    
    Args:
        host: User-provided host URL (may include scheme, port, trailing slashes)
        
    Returns:
        Normalized URL string ready for API calls
        
    Raises:
        ValueError: If the URL cannot be normalized or is invalid
    """
    if not host or not host.strip():
        raise ValueError("Host URL cannot be empty")
    
    host = host.strip()
    
    try:
        # Parse the URL
        url = URL(host)
        
        # If no scheme provided, default to http
        if not url.scheme:
            url = URL(f"http://{host}")
        elif url.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {url.scheme}. Must be http or https")
        
        # Validate we have a hostname/IP
        if not url.host:
            raise ValueError("URL must include a hostname or IP address")
        
        # Normalize: remove trailing slashes, ensure proper format
        normalized = url.with_path("").with_query(None).with_fragment(None)
        
        _LOGGER.debug("Normalized URL: %s -> %s", host, str(normalized))
        return str(normalized)
        
    except Exception as exc:
        _LOGGER.error("Failed to normalize URL '%s': %s", host, exc)
        raise ValueError(f"Invalid URL format: {host}") from exc


class UnraidGraphQLError(Exception):
    """Raised when the response contains errors."""

    def __init__(self, response: dict, *args: Any) -> None:
        self.response = response
        error_msg = ", ".join({entry.get("message") for entry in response["errors"]})
        super().__init__(error_msg, *args)


class UnraidAuthError(UnraidGraphQLError):
    """Raised when the request was unauthorized."""


class IncompatibleApiError(Exception):
    """Raised when the response contains errors."""

    def __init__(self, version: AwesomeVersion, min_version: AwesomeVersion, *args: Any) -> None:
        self.version = version
        self.min_version = min_version
        super().__init__(*args)


def _import_client_class(
    api_version: AwesomeVersion,
) -> type[UnraidApiClient]:
    if api_version >= AwesomeVersion("4.26.0"):
        from custom_components.unraid_api.api.v4_26 import UnraidApiV426  # noqa: PLC0415

        return UnraidApiV426
    if api_version >= AwesomeVersion("4.20.0"):
        from custom_components.unraid_api.api.v4_20 import UnraidApiV420  # noqa: PLC0415

        return UnraidApiV420

    raise IncompatibleApiError(version=api_version, min_version=AwesomeVersion("4.20.0"))


async def get_api_client(host: str, api_key: str, session: ClientSession) -> UnraidApiClient:
    """Get Unraid API Client."""
    client = UnraidApiClient(host, api_key, session)
    api_version = await client.query_api_version()
    loop = asyncio.get_event_loop()
    cls = await loop.run_in_executor(None, _import_client_class, api_version)
    return cls(host, api_key, session)


_T = TypeVar("_T", bound=BaseModel)


class UnraidApiClient:
    """Unraid GraphQL API Client."""

    version: AwesomeVersion

    def __init__(self, host: str, api_key: str, session: ClientSession) -> None:
        # Normalize the host URL
        normalized_host = normalize_url(host)
        self.host = normalized_host
        
        # Construct the GraphQL endpoint using yarl.URL for proper path joining
        base_url = URL(normalized_host)
        self.endpoint = str(base_url / "graphql")
        
        self.api_key = api_key
        self.session = session
        
        _LOGGER.debug("Initialized API client - Host: %s, Endpoint: %s", self.host, self.endpoint)
        
        _LOGGER.debug("Initialized API client - Host: %s, Endpoint: %s", self.host, self.endpoint)

    async def call_api(
        self,
        query: str,
        model: type[_T],
        variables: dict[str, Any] | None = None,
    ) -> _T:
        response = await self.session.post(
            self.endpoint,
            json={"query": query, "variables": variables or {}},
            headers={
                "x-api-key": self.api_key,
                "Origin": self.host,
                "content-type": "application/json",
            },
        )
        result = await response.json()
        if "errors" in result:
            try:
                if result["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED":
                    raise UnraidAuthError(response=result)
            except KeyError:
                pass
            raise UnraidGraphQLError(response=result)

        return model.model_validate(result["data"])

    async def query_api_version(self) -> AwesomeVersion:
        try:
            response = await self.call_api(API_VERSION_QUERY, ApiVersionQuery)
            return AwesomeVersion(response.info.versions.core.api.split("+")[0])
        except ValidationError:
            return AwesomeVersion("")

    @abstractmethod
    async def query_server_info(self) -> ServerInfo:
        pass

    @abstractmethod
    async def query_metrics(self) -> Metrics:
        pass

    @abstractmethod
    async def query_shares(self) -> list[Share]:
        pass

    @abstractmethod
    async def query_disks(self) -> list[Disk]:
        pass

    @abstractmethod
    async def query_array(self) -> Array:
        pass

    @abstractmethod
    async def query_ups(self) -> list[UpsDevice]:
        pass

    @abstractmethod
    async def query_docker_containers(self) -> list[DockerContainer]:
        pass

    @abstractmethod
    async def start_docker_container(self, container_id: str) -> None:
        pass

    @abstractmethod
    async def stop_docker_container(self, container_id: str) -> None:
        pass


## Queries

API_VERSION_QUERY = """
query ApiVersion {
  info {
    versions {
      core {
        api
      }
    }
  }
}
"""

## Api Models


class ApiVersionQuery(BaseModel):  # noqa: D101
    info: Info


class Info(BaseModel):  # noqa: D101
    versions: InfoVersions


class InfoVersions(BaseModel):  # noqa: D101
    core: InfoVersionsCore


class InfoVersionsCore(BaseModel):  # noqa: D101
    api: str
