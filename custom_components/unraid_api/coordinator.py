"""Unraid update coordinator."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypedDict

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pydantic_core import ValidationError

from .api import IncompatibleApiError, UnraidAuthError, UnraidGraphQLError
from .const import CONF_DRIVES, CONF_SHARES, DOMAIN

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .api import UnraidApiClient
    from .models import Array, Disk, DockerContainer, Metrics, Share, UPSDevice, VirtualMachine

_LOGGER = logging.getLogger(__name__)


class UnraidServerData(TypedDict):  # noqa: D101
    metrics: Metrics | None
    array: Array | None
    disks: dict[str, Disk]
    shares: dict[str, Share]
    ups_devices: list[UPSDevice]
    uptime_since: str | None  # ISO timestamp when system started
    vms: dict[str, VirtualMachine]
    containers: dict[str, DockerContainer]


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
        self.vm_callbacks: set[Callable[[VirtualMachine], None]] = set()
        self.container_callbacks: set[Callable[[DockerContainer], None]] = set()

    async def _async_setup(self) -> None:
        self.known_disks: set[str] = set()
        self.known_shares: set[str] = set()
        self.known_vms: set[str] = set()
        self.known_containers: set[str] = set()

    async def _async_update_data(self) -> UnraidServerData:
        data = UnraidServerData()
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._update_metrics(data))
                tg.create_task(self._update_array(data))
                tg.create_task(self._update_ups(data))
                tg.create_task(self._update_uptime(data))
                tg.create_task(self._update_vms(data))
                tg.create_task(self._update_containers(data))
                if self.config_entry.options[CONF_DRIVES]:
                    tg.create_task(self._update_disks(data))
                if self.config_entry.options[CONF_SHARES]:
                    tg.create_task(self._update_shares(data))

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
        except* UnraidAuthError as exc:
            _LOGGER.debug("Update: Auth failed")
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
                translation_placeholders={"error_msg": exc.args[0]},
            ) from exc
        except* UnraidGraphQLError as exc:
            _LOGGER.debug("Update: GraphQL Error response: %s", exc.exceptions[0].response)
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="error_response",
                translation_placeholders={"error_msg": exc.exceptions[0].args[0]},
            ) from exc
        except* ValidationError as exc:
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

    async def _update_ups(self, data: UnraidServerData) -> None:
        try:
            data["ups_devices"] = await self.api_client.query_ups_devices()
        except UnraidGraphQLError:
            # UPS might not be available on all systems
            _LOGGER.debug("No UPS devices found or UPS query failed")
            data["ups_devices"] = []

    async def _update_uptime(self, data: UnraidServerData) -> None:
        server_info = await self.api_client.query_server_info()
        data["uptime_since"] = server_info.uptime

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

    async def _update_vms(self, data: UnraidServerData) -> None:
        vms = {}
        try:
            query_response = await self.api_client.query_vms()
            for vm in query_response:
                vms[vm.id] = vm
                if vm.id not in self.known_vms:
                    self.known_vms.add(vm.id)
                    self._do_callback(self.vm_callbacks, vm)
        except UnraidGraphQLError as exc:
            # VMs might not be available on all systems
            _LOGGER.debug("No VMs found or VM query failed: %s", exc)
        data["vms"] = vms

    async def _update_containers(self, data: UnraidServerData) -> None:
        containers = {}
        try:
            query_response = await self.api_client.query_docker_containers()
            for container in query_response:
                containers[container.id] = container
                if container.id not in self.known_containers:
                    self.known_containers.add(container.id)
                    self._do_callback(self.container_callbacks, container)
        except UnraidGraphQLError:
            # Docker might not be available on all systems
            _LOGGER.debug("No containers found or Docker query failed")
        data["containers"] = containers

    def subscribe_disks(self, callback: Callable[[Disk], None]) -> None:
        self.disk_callbacks.add(callback)
        for disk_id in self.known_disks:
            self._do_callback([callback], self.data["disks"][disk_id])

    def subscribe_shares(self, callback: Callable[[Share], None]) -> None:
        self.share_callbacks.add(callback)
        for share_name in self.known_shares:
            self._do_callback([callback], self.data["shares"][share_name])

    def subscribe_vms(self, callback: Callable[[VirtualMachine], None]) -> None:
        self.vm_callbacks.add(callback)
        for vm_id in self.known_vms:
            self._do_callback([callback], self.data["vms"][vm_id])

    def subscribe_containers(self, callback: Callable[[DockerContainer], None]) -> None:
        self.container_callbacks.add(callback)
        for container_id in self.known_containers:
            self._do_callback([callback], self.data["containers"][container_id])

    def _do_callback(
        self, callbacks: set[Callable[..., None]], *args: tuple[Any], **kwargs: dict[Any]
    ) -> None:
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                _LOGGER.exception("Error in callback")
