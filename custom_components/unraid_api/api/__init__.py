"""Unraid GraphQL API Client."""

from __future__ import annotations

import asyncio
import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar
from urllib.parse import urlparse

from awesomeversion import AwesomeVersion
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from unraid_api.models import Array, Disk, Metrics, ServerInfo, Share

_LOGGER = logging.getLogger(__name__)


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


async def detect_ssl_redirect(host: str, session: ClientSession) -> str | None:
    """
    Detect if HTTP redirects to HTTPS and return the resolved URL.

    Returns the resolved URL if a redirect is detected, None otherwise.
    This handles Unraid servers that redirect HTTP to HTTPS (often to myunraid.net domains).
    """
    parsed = urlparse(host)

    # Only check for redirects if using HTTP
    if parsed.scheme != "http":
        return None

    try:
        # Make a HEAD request to check for redirects without following them
        async with session.head(
            f"{host}/graphql",
            allow_redirects=False,
            timeout=10,
        ) as response:
            if response.status in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if location and location.startswith("https://"):
                    # Extract the base URL from the redirect location
                    redirect_parsed = urlparse(location)
                    resolved_url = f"{redirect_parsed.scheme}://{redirect_parsed.netloc}"
                    _LOGGER.debug(
                        "Detected SSL redirect from %s to %s",
                        host,
                        resolved_url,
                    )
                    return resolved_url
    except Exception:  # noqa: BLE001
        _LOGGER.debug("SSL redirect detection failed for %s", host)

    return None


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
