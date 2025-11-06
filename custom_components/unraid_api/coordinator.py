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
from .const import CONF_DOCKER, CONF_DRIVES, CONF_SHARES, CONF_VMS, DOMAIN

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .api import UnraidApiClient
    from .models import Array, Disk, DockerContainer, Metrics, Share, VirtualMachine

_LOGGER = logging.getLogger(__name__)


class UnraidServerData(TypedDict):  # noqa: D101
    metrics: Metrics | None
    array: Array | None
    disks: dict[str, Disk]
    shares: dict[str, Share]
    vms: dict[str, VirtualMachine]
    docker: dict[str, DockerContainer]


class UnraidDataUpdateCoordinator(DataUpdateCoordinator[UnraidServerData]):
    """Update Coordinator."""

    known_disks: set[str]
    known_shares: set[str]
    known_vms: set[str]
    known_docker: set[str]
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
        self.docker_callbacks: set[Callable[[DockerContainer], None]] = set()

    async def _async_setup(self) -> None:
        self.known_disks: set[str] = set()
        self.known_shares: set[str] = set()
        self.known_vms: set[str] = set()
        self.known_docker: set[str] = set()

    async def _async_update_data(self) -> UnraidServerData:
        data = UnraidServerData()
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._update_metrics(data))
                tg.create_task(self._update_array(data))
                if self.config_entry.options.get(CONF_DRIVES, True):
                    tg.create_task(self._update_disks(data))
                if self.config_entry.options.get(CONF_SHARES, True):
                    tg.create_task(self._update_shares(data))
                if self.config_entry.options.get(CONF_VMS, False):
                    tg.create_task(self._update_vms(data))
                if self.config_entry.options.get(CONF_DOCKER, False):
                    tg.create_task(self._update_docker(data))

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
        query_response = await self.api_client.query_vms()

        for vm in query_response:
            vms[vm.id] = vm
            if vm.id not in self.known_vms:
                self.known_vms.add(vm.id)
                self._do_callback(self.vm_callbacks, vm)
        data["vms"] = vms

    async def _update_docker(self, data: UnraidServerData) -> None:
        docker = {}
        query_response = await self.api_client.query_docker_containers()

        for container in query_response:
            docker[container.id] = container
            if container.id not in self.known_docker:
                self.known_docker.add(container.id)
                self._do_callback(self.docker_callbacks, container)
        data["docker"] = docker

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

    def subscribe_docker(self, callback: Callable[[DockerContainer], None]) -> None:
        self.docker_callbacks.add(callback)
        for container_id in self.known_docker:
            self._do_callback([callback], self.data["docker"][container_id])

    async def async_vm_action(self, vm_id: str, action: str) -> bool:
        """Execute an action on a VM."""
        actions = {
            "start": self.api_client.vm_start,
            "stop": self.api_client.vm_stop,
            "reboot": self.api_client.vm_reboot,
            "pause": self.api_client.vm_pause,
            "resume": self.api_client.vm_resume,
            "force_stop": self.api_client.vm_force_stop,
        }
        if action not in actions:
            raise ValueError(f"Unknown VM action: {action}")

        result = await actions[action](vm_id)
        await self.async_request_refresh()
        return result

    async def async_docker_action(self, container_id: str, action: str) -> bool:
        """Execute an action on a Docker container."""
        actions = {
            "start": self.api_client.docker_start,
            "stop": self.api_client.docker_stop,
        }
        if action not in actions:
            raise ValueError(f"Unknown Docker action: {action}")

        result = await actions[action](container_id)
        await self.async_request_refresh()
        return result

    def _do_callback(
        self, callbacks: set[Callable[..., None]], *args: tuple[Any], **kwargs: dict[Any]
    ) -> None:
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                _LOGGER.exception("Error in callback")
