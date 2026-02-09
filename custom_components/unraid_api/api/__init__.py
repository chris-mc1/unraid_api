"""Unraid GraphQL API Client."""

from __future__ import annotations

import asyncio
import json
import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

import yarl
from awesomeversion import AwesomeVersion
from pydantic import BaseModel, ValidationError

from custom_components.unraid_api.exceptions import (
    GraphQLError,
    GraphQLMultiError,
    GraphQLUnauthorizedError,
    IncompatibleApiError,
    UnraidApiInvalidResponseError,
)

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from custom_components.unraid_api.models import (
        Disk,
        MetricsArray,
        ServerInfo,
        Share,
        UpsDevice,
    )

_LOGGER = logging.getLogger(__name__)


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


def _normalize_url(url_str: str) -> yarl.URL:
    url_str = url_str if "://" in url_str else f"http://{url_str}"
    url = yarl.URL(url_str)
    return url.origin()


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
        self.host = _normalize_url(host)
        self.endpoint = self.host / "graphql"
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
                "Origin": str(self.host),
                "content-type": "application/json",
            },
        )

        response.raise_for_status()

        try:
            result = await response.json()
        except json.JSONDecodeError as exc:
            raise UnraidApiInvalidResponseError(response=response) from exc

        if "errors" in result:
            try:
                if result["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED":
                    raise GraphQLUnauthorizedError(result["errors"][0])
            except (KeyError, IndexError):
                pass

            if len(result["errors"]) > 1:
                raise GraphQLMultiError(result["errors"])
            raise GraphQLError(result["errors"][0])
        try:
            return model.model_validate(result["data"])
        except ValidationError as exc:
            raise UnraidApiInvalidResponseError(response=response) from exc

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
    async def query_metrics_array(self) -> MetricsArray:
        pass

    @abstractmethod
    async def query_shares(self) -> list[Share]:
        pass

    @abstractmethod
    async def query_disks(self) -> list[Disk]:
        pass

    @abstractmethod
    async def query_ups(self) -> list[UpsDevice]:
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
