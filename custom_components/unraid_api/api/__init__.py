"""Unraid GraphQL API Client."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from abc import abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import yarl
from awesomeversion import AwesomeVersion
from pydantic import BaseModel, ValidationError

from custom_components.unraid_api.exceptions import (
    GraphQLError,
    GraphQLInvalidMessageError,
    GraphQLMultiError,
    GraphQLUnauthorizedError,
    IncompatibleApiError,
    UnraidApiInvalidResponseError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aiohttp import ClientSession, ClientWebSocketResponse, WSMessage

    from custom_components.unraid_api.models import (
        CpuMetricsSubscription,
        Disk,
        MemorySubscription,
        MetricsArray,
        ServerInfo,
        Share,
        UpsDevice,
    )

_LOGGER = logging.getLogger(__name__)


class GraphQLWebsocketMessageType(StrEnum):
    """GraphQL WebSocket message Types."""

    CONNECTION_INIT = "connection_init"
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    NEXT = "next"
    ERROR = "error"
    COMPLETE = "complete"


GRAPHQL_WS_PROTOCOL = "graphql-transport-ws"


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


def _parse_ws_message(message: WSMessage) -> dict:
    try:
        message_dict = message.json()
    except json.JSONDecodeError as exc:
        raise GraphQLInvalidMessageError(message=message) from exc

    type_ = message_dict.get("type")
    if not type_ or type_ not in {t.value for t in GraphQLWebsocketMessageType}:
        raise GraphQLInvalidMessageError(message=message)

    return message_dict


async def get_api_client(host: str, api_key: str, session: ClientSession) -> UnraidApiClient:
    """Get Unraid API Client."""
    client = UnraidApiClient(host, api_key, session)
    api_version = await client.query_api_version()
    loop = asyncio.get_event_loop()
    cls = await loop.run_in_executor(None, _import_client_class, api_version)
    return cls(host, api_key, session)


class UnraidApiClientBase:
    """Unraid GraphQL API Client base."""

    version: AwesomeVersion
    _ws: ClientWebSocketResponse | None = None
    _ws_connected: bool = False
    _ws_subscription_callbacks: dict[str, Callable[[Any], None]]

    def __init__(self, host: str, api_key: str, session: ClientSession) -> None:
        self.host = _normalize_url(host)
        self.endpoint = self.host / "graphql"
        self.ws_endpoint = self.endpoint.with_scheme(
            "wss" if self.endpoint.scheme == "https" else "ws"
        )
        self.api_key = api_key
        self.session = session

    async def call_api[T: BaseModel](
        self,
        query: str,
        model: type[T] | None,
        variables: dict[str, Any] | None = None,
    ) -> T:
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
            if model is not None:
                return model.model_validate(result["data"])
        except ValidationError as exc:
            raise UnraidApiInvalidResponseError(response=response) from exc
        return None

    async def start_websocket(self) -> None:
        if self._ws:
            return

        self._ws_subscription_callbacks = {}
        self._ws = await self.session.ws_connect(
            self.ws_endpoint,
            protocols=(GRAPHQL_WS_PROTOCOL,),
        )

        # send init
        await self._ws.send_json(
            {
                "type": GraphQLWebsocketMessageType.CONNECTION_INIT,
                "payload": {
                    "x-api-key": self.api_key,
                },
            }
        )
        ack_message = _parse_ws_message(await self._ws.receive(timeout=2))
        if ack_message["type"] != GraphQLWebsocketMessageType.CONNECTION_ACK:
            msg = f"Unexpected message type. Expected: {ack_message['type']}"
            raise GraphQLError(msg)

        self._ws_connected = True

        self._ws_recv_task = asyncio.create_task(self._ws_recv_loop())

    async def stop_websocket(self) -> None:
        self._ws_connected = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._ws_recv_task:
            self._ws_recv_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._ws_recv_task
            self._ws_recv_task = None

    @property
    def websocket_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed and self._ws_connected

    async def _ws_recv_loop(self) -> None:
        try:
            async for message in self._ws:
                try:
                    await self._handel_ws_message(message)
                except GraphQLInvalidMessageError as exc:
                    _LOGGER.debug("Websocket: Invalid Message: %s", exc.message)
                except (GraphQLError, GraphQLMultiError) as exc:
                    _LOGGER.debug("Websocket: GraphQL Error response: %s", str(exc))
        except asyncio.CancelledError:
            _LOGGER.debug("Receive loop cancelled")
            raise
        except Exception:
            _LOGGER.exception("Receive loop exception")
        finally:
            self._ws_connected = False
            await self._ws.close()
            self._ws = None
            self._ws_subscription_callbacks = None

    async def _handel_ws_message(self, message: WSMessage) -> None:
        message_dict = _parse_ws_message(message)

        type_ = message_dict.get("type")
        payload = message_dict.get("payload", {})

        if type_ == GraphQLWebsocketMessageType.NEXT:
            if "data" not in payload:
                raise GraphQLInvalidMessageError(message=message)
            try:
                self._ws_subscription_callbacks[message_dict["id"]](payload["data"])
            except KeyError as exc:
                raise GraphQLInvalidMessageError(message=message) from exc

        elif type_ == GraphQLWebsocketMessageType.COMPLETE:
            return

        elif type_ == GraphQLWebsocketMessageType.PING:
            await self._ws.send_json({"type": GraphQLWebsocketMessageType.PONG.value})

        elif type_ == GraphQLWebsocketMessageType.ERROR:
            raise GraphQLMultiError(errors_dicts=payload, data=message_dict)

    async def _subscribe(
        self, query: str, operation_name: str, callback: Callable[[float], None]
    ) -> None:
        if not self._ws_connected:
            msg = "Websocket not connected"
            raise RuntimeError(msg)

        op_id = str(uuid4())
        self._ws_subscription_callbacks[op_id] = callback
        payload: dict[str, Any] = {
            "id": op_id,
            "type": GraphQLWebsocketMessageType.SUBSCRIBE.value,
            "payload": {"query": query, "operationName": operation_name},
        }
        await self._ws.send_json(payload)


class UnraidApiClient(UnraidApiClientBase):
    """Unraid GraphQL API Client."""

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

    @abstractmethod
    async def subscribe_cpu_usage(self, callback: Callable[[float], None]) -> None:
        pass

    @abstractmethod
    async def subscribe_cpu_metrics(
        self, callback: Callable[[CpuMetricsSubscription], None]
    ) -> None:
        pass

    @abstractmethod
    async def subscribe_memory(self, callback: Callable[[MemorySubscription], None]) -> None:
        pass

    @abstractmethod
    async def start_parity_check(self) -> None:
        pass

    @abstractmethod
    async def cancel_parity_check(self) -> None:
        pass

    @abstractmethod
    async def pause_parity_check(self) -> None:
        pass

    @abstractmethod
    async def resume_parity_check(self) -> None:
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
