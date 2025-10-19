"""API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .const import ARRAY_QUERY, DISKS_QUERY, METRICS_QUERY, SERVER_INFO_QUERY, SHARES_QUERY
from .models import ArrayQuery, DiskQuery, MetricsQuery, ServerInfoQuery, SharesQuery

if TYPE_CHECKING:
    from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)


class UnraidGraphQLError(Exception):
    """Raised when the response contains errors."""


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
        variables: dict[str, Any] | None = None,
    ) -> dict:
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
            error_msg = ", ".join({entry.get("message") for entry in result["errors"]})
            _LOGGER.error("Error in query response: %s", error_msg)
            raise UnraidGraphQLError(error_msg)
        return result["data"]

    async def query_server_info(self) -> ServerInfoQuery:
        response = await self.call_api(SERVER_INFO_QUERY)
        return ServerInfoQuery.model_validate(response)

    async def query_metrics(self) -> MetricsQuery:
        response = await self.call_api(METRICS_QUERY)
        return MetricsQuery.model_validate(response)

    async def query_shares(self) -> SharesQuery:
        response = await self.call_api(SHARES_QUERY)
        return SharesQuery.model_validate(response)

    async def query_disks(self) -> DiskQuery:
        response = await self.call_api(DISKS_QUERY)
        return DiskQuery.model_validate(response)

    async def query_array(self) -> ArrayQuery:
        response = await self.call_api(ARRAY_QUERY)
        return ArrayQuery.model_validate(response)
