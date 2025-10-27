"""Unraid GraphQL API Client."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, TypeVar

from awesomeversion import AwesomeVersion
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from unraid_api.models import Array, Disk, Metrics, ServerInfo, Share

_LOGGER = logging.getLogger(__name__)


class UnraidGraphQLError(Exception):
    """Raised when the response contains errors."""


class IncompatibleApiError(Exception):
    """Raised when the response contains errors."""


def _import_client_class(
    api_version: AwesomeVersion,
) -> type[UnraidApiClient]:
    if api_version >= AwesomeVersion("4.20.0"):
        from custom_components.unraid_api.api.v4_20 import UnraidApiV420  # noqa: PLC0415

        return UnraidApiV420

    raise IncompatibleApiError


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

    def __init__(self, host: str, api_key: str, session: ClientSession) -> None:
        self.host = host.rstrip("/")
        self.endpoint = self.host + "/graphql"
        self.api_key = api_key
        self.session = session

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
            error_msg = ", ".join(entry.get("message") for entry in result["errors"])
            _LOGGER.error("Error in query response: %s", error_msg)
            raise UnraidGraphQLError(error_msg)

        return model.model_validate(result["data"])

    async def query_api_version(self) -> AwesomeVersion:
        response = await self.call_api(API_VERSION_QUERY, ApiVersionQuery)
        try:
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
