"""Unraid update coordinator."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypedDict

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from awesomeversion import AwesomeVersion
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_DRIVES, CONF_SHARES, DOMAIN
from .exceptions import (
    GraphQLError,
    GraphQLMultiError,
    GraphQLUnauthorizedError,
    IncompatibleApiError,
    UnraidApiError,
    UnraidApiInvalidResponseError,
)
from .models import Metrics

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .api import UnraidApiClient
    from .models import Array, Disk, Metrics, Share, UpsDevice

_LOGGER = logging.getLogger(__name__)


class UnraidServerData(TypedDict):  # noqa: D101
    metrics: Metrics | None
    array: Array | None
    disks: dict[str, Disk]
    shares: dict[str, Share]
    ups_devices: dict[str, UpsDevice]


class UnraidDataUpdateCoordinator(DataUpdateCoordinator[UnraidServerData]):
    """Update Coordinator."""

    known_disks: set[str]
    known_shares: set[str]
    known_ups_devices: set[str]
    config_entry: UnraidConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: UnraidConfigEntry, api_client: UnraidApiClient
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )
        self.api_client = api_client
        self.disk_callbacks: set[Callable[[Disk], None]] = set()
        self.share_callbacks: set[Callable[[Share], None]] = set()
        self.ups_callbacks: set[Callable[[UpsDevice], None]] = set()

    async def _async_setup(self) -> None:
        self.known_disks: set[str] = set()
        self.known_shares: set[str] = set()
        self.known_ups_devices: set[str] = set()

    async def _async_update_data(self) -> UnraidServerData:
        data = UnraidServerData()
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._update_metrics(data))
                tg.create_task(self._update_array(data))
                if self.config_entry.options[CONF_DRIVES]:
                    tg.create_task(self._update_disks(data))
                if self.config_entry.options[CONF_SHARES]:
                    tg.create_task(self._update_shares(data))
                if self.api_client.version >= AwesomeVersion("4.26.0"):
                    tg.create_task(self._update_ups(data))

        except* ClientConnectorSSLError as exc:
            _LOGGER.debug("Update: SSL error: %s", str(exc))
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="ssl_error",
                translation_placeholders={"error": str(exc)},
            ) from exc
        except* (
            ClientConnectionError,
            TimeoutError,
        ) as exc:
            _LOGGER.debug("Update: Connection error: %s", str(exc))
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(exc)},
            ) from exc
        except* GraphQLUnauthorizedError as exc:
            _LOGGER.debug("Update: Auth failed")
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
                translation_placeholders={"error_msg": (exc)},
            ) from exc
        except* (GraphQLError, GraphQLMultiError) as exc:
            _LOGGER.debug("Update: GraphQL Error response: %s", str(exc))
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="error_response",
                translation_placeholders={"error_msg": str(exc)},
            ) from exc
        except* UnraidApiInvalidResponseError as exc:
            _LOGGER.debug("Update: invalid data")
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="data_invalid",
            ) from exc
        except* IncompatibleApiError as exc:
            _LOGGER.debug(
                "Update: Incompatible API, %s < %s",
                exc.exceptions[0].version,
                exc.exceptions[0].min_version,
            )
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="api_incompatible",
                translation_placeholders={
                    "min_version": exc.exceptions[0].min_version,
                    "version": exc.exceptions[0].version,
                },
            ) from exc

        return data

    async def _update_metrics(self, data: UnraidServerData) -> None:
        data["metrics"] = await self.api_client.query_metrics()

    async def _update_array(self, data: UnraidServerData) -> None:
        data["array"] = await self.api_client.query_array()

    async def _update_disks(self, data: UnraidServerData) -> None:
        disks = {}
        query_response = await self.api_client.query_disks()

        for disk in query_response:
            disks[disk.id] = disk
            if disk.id not in self.known_disks:
                self.known_disks.add(disk.id)
                self._do_callback(self.disk_callbacks, disk)
        data["disks"] = disks

    async def _update_shares(self, data: UnraidServerData) -> None:
        shares = {}
        query_response = await self.api_client.query_shares()

        for share in query_response:
            shares[share.name] = share
            if share.name not in self.known_shares:
                self.known_shares.add(share.name)
                self._do_callback(self.share_callbacks, share)
        data["shares"] = shares

    async def _update_ups(self, data: UnraidServerData) -> None:
        devices = {}
        try:
            query_response = await self.api_client.query_ups()

            for device in query_response:
                devices[device.id] = device
                if device.id not in self.known_ups_devices:
                    self.known_ups_devices.add(device.id)
                    self._do_callback(self.ups_callbacks, device)
        except UnraidApiError:
            pass

        data["ups_devices"] = devices

    def subscribe_disks(self, callback: Callable[[Disk], None]) -> None:
        self.disk_callbacks.add(callback)
        for disk_id in self.known_disks:
            self._do_callback([callback], self.data["disks"][disk_id])

    def subscribe_shares(self, callback: Callable[[Share], None]) -> None:
        self.share_callbacks.add(callback)
        for share_name in self.known_shares:
            self._do_callback([callback], self.data["shares"][share_name])

    def subscribe_ups(self, callback: Callable[[UpsDevice], None]) -> None:
        self.ups_callbacks.add(callback)
        for ups_id in self.known_ups_devices:
            self._do_callback([callback], self.data["ups_devices"][ups_id])

    def _do_callback(
        self, callbacks: set[Callable[..., None]], *args: tuple[Any], **kwargs: dict[Any]
    ) -> None:
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                _LOGGER.exception("Error in callback")
