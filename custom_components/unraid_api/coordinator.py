"""Unraid update coordinator."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypedDict

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pydantic_core import ValidationError

from .api import UnraidGraphQLError
from .const import CONF_DRIVES, CONF_SHARES, DOMAIN

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .api import UnraidApiClient
    from .models import ArrayQuery, Disk, Metrics, Share

_LOGGER = logging.getLogger(__name__)


class UnraidServerData(TypedDict):  # noqa: D101
    metrics: Metrics | None
    array: ArrayQuery | None
    disks: dict[str, Disk]
    shares: dict[str, Share]


class UnraidDataUpdateCoordinator(DataUpdateCoordinator[UnraidServerData]):
    """Update Coordinator."""

    known_disks: set[str]
    known_shares: set[str]
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

    async def _async_setup(self) -> None:
        self.known_disks: set[str] = set()
        self.known_shares: set[str] = set()

    async def _async_update_data(self) -> UnraidServerData:
        data = UnraidServerData()
        async with asyncio.TaskGroup() as tg:
            metrics_task = tg.create_task(self._update_metrics())
            array_task = tg.create_task(self._update_array())
            if self.config_entry.options[CONF_DRIVES]:
                disks_task = tg.create_task(self._update_disks())
            if self.config_entry.options[CONF_SHARES]:
                shares_task = tg.create_task(self._update_shares())

        data["metrics"] = metrics_task.result()
        data["array"] = array_task.result()
        if self.config_entry.options[CONF_DRIVES]:
            data["disks"] = disks_task.result()
        if self.config_entry.options[CONF_SHARES]:
            data["shares"] = shares_task.result()
        return data

    async def _update_metrics(self) -> Metrics | None:
        try:
            return (await self.api_client.query_metrics()).metrics
        except (UnraidGraphQLError, ValidationError):
            return None

    async def _update_array(self) -> ArrayQuery | None:
        try:
            return await self.api_client.query_array()
        except (UnraidGraphQLError, ValidationError):
            return None

    async def _update_disks(self) -> dict[str, Disk]:
        disks = {}
        try:
            query_response = await self.api_client.query_disks()
        except (UnraidGraphQLError, ValidationError):
            return disks

        for disk in query_response.array.disks:
            disks[disk.id] = disk
            if disk.id not in self.known_disks:
                self.known_disks.add(disk.id)
                self._do_callback(self.disk_callbacks, disk)

        for disk in query_response.array.parities:
            disks[disk.id] = disk
            if disk.id not in self.known_disks:
                self.known_disks.add(disk.id)
                self._do_callback(self.disk_callbacks, disk)

        for disk in query_response.array.caches:
            disks[disk.id] = disk
            if disk.id not in self.known_disks:
                self.known_disks.add(disk.id)
                self._do_callback(self.disk_callbacks, disk)

        return disks

    async def _update_shares(self) -> dict[str, Share]:
        shares = {}
        try:
            query_response = await self.api_client.query_shares()
        except (UnraidGraphQLError, ValidationError):
            return shares

        for share in query_response.shares:
            shares[share.name] = share
            if share.name not in self.known_shares:
                self.known_shares.add(share.name)
                self._do_callback(self.share_callbacks, share)

        return shares

    def subscribe_disks(self, callback: Callable[[Disk], None]) -> None:
        self.disk_callbacks.add(callback)
        for disk_id in self.known_disks:
            self._do_callback([callback], self.data["disks"][disk_id])

    def subscribe_shares(self, callback: Callable[[Share], None]) -> None:
        self.share_callbacks.add(callback)
        for share_name in self.known_shares:
            self._do_callback([callback], self.data["shares"][share_name])

    def _do_callback(
        self, callbacks: set[Callable[..., None]], *args: tuple[Any], **kwargs: dict[Any]
    ) -> None:
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                _LOGGER.exception("Error in callback")()
