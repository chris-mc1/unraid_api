"""Unraid update coordinator."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypedDict

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from awesomeversion import AwesomeVersion
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DOCKER_MODE,
    CONF_DRIVES,
    CONF_SHARES,
    DOCKER_MODE_ENABLED_ONLY,
    DOCKER_MODE_EXCEPT_DISABLED,
    DOCKER_MODE_OFF,
    DOMAIN,
)
from .exceptions import (
    GraphQLError,
    GraphQLMultiError,
    GraphQLUnauthorizedError,
    IncompatibleApiError,
    UnraidApiError,
    UnraidApiInvalidResponseError,
)
from .models import CpuMetricsSubscription, DockerContainer, MemorySubscription, MetricsArray

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .api import UnraidApiClient
    from .entity import UnraidBaseEntity
    from .models import Disk, MetricsArray, Share, UpsDevice

_LOGGER = logging.getLogger(__name__)


class Container(TypedDict):  # noqa: D101
    device_info: DeviceInfo
    entities: list[UnraidBaseEntity]


class UnraidServerData(TypedDict):  # noqa: D101
    metrics_array: MetricsArray
    disks: dict[str, Disk]
    shares: dict[str, Share]
    ups_devices: dict[str, UpsDevice]
    docker_containers: dict[str, DockerContainer]
    cpu_metrics: CpuMetricsSubscription
    cpu_usage: float
    memory: MemorySubscription


class UnraidDataUpdateCoordinator(DataUpdateCoordinator[UnraidServerData]):
    """Update Coordinator."""

    known_disks: set[str]
    known_shares: set[str]
    known_ups_devices: set[str]
    config_entry: UnraidConfigEntry
    _websocket_error_logged: bool = True

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
        self.docker_callbacks: set[Callable[[DockerContainer], None]] = set()

    async def _async_setup(self) -> None:
        self.known_disks: set[str] = set()
        self.known_shares: set[str] = set()
        self.known_ups_devices: set[str] = set()
        self.data = UnraidServerData()

        await self._connect_websocket()

    async def _connect_websocket(self) -> None:
        try:
            await self.api_client.start_websocket()

            await self.api_client.subscribe_cpu_usage(self._cpu_usage_callback)
            await self.api_client.subscribe_memory(self._memory_callback)
            if self.api_client.version >= AwesomeVersion("4.26.0"):
                await self.api_client.subscribe_cpu_metrics(self._cpu_metrics_callback)
        except (
            ClientConnectionError,
            TimeoutError,
        ):
            if self._websocket_error_logged:
                self.logger.debug("Websocket: Connection failed", exc_info=True)
            else:
                self._websocket_error_logged = True
                self.logger.exception("Websocket: Connection failed")
        except (GraphQLError, GraphQLMultiError) as exc:
            if self._websocket_error_logged:
                self.logger.debug("Websocket: GraphQL Error response: %s", str(exc))
            else:
                self._websocket_error_logged = True
                self.logger.error("Websocket: GraphQL Error response: %s", str(exc))  # noqa: TRY400
        else:
            self.logger.info("Websocket: Connected")
            self._websocket_error_logged = False

    async def _async_update_data(self) -> UnraidServerData:
        if self._websocket_error_logged and not self.api_client.websocket_connected:
            await self._connect_websocket()
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._update_metrics())
                if self.config_entry.options[CONF_DRIVES]:
                    tg.create_task(self._update_disks())
                if self.config_entry.options[CONF_SHARES]:
                    tg.create_task(self._update_shares())
                if self.api_client.version >= AwesomeVersion("4.26.0"):
                    tg.create_task(self._update_ups())
                if self.config_entry.options[CONF_DOCKER_MODE] not in DOCKER_MODE_OFF:
                    tg.create_task(self._update_docker())

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

        return self.data

    async def _update_metrics(self) -> None:
        data = await self.api_client.query_metrics_array()
        self.data["metrics_array"] = data

        if not self.api_client.websocket_connected:
            self.data["cpu_usage"] = data.cpu_percent_total
            self.data["memory"] = MemorySubscription(
                total=data.memory_total,
                active=data.memory_active,
                available=data.memory_available,
                percent_total=data.memory_percent_total,
            )

        if (
            self.api_client.version >= AwesomeVersion("4.26.0")
            or not self.api_client.websocket_connected
        ):
            self.data["cpu_metrics"] = CpuMetricsSubscription(
                power=data.cpu_power, temp=data.cpu_temp
            )

    async def _update_disks(self) -> None:
        disks = {}
        query_response = await self.api_client.query_disks()

        for disk in query_response:
            disks[disk.id] = disk
            if disk.id not in self.known_disks:
                self.known_disks.add(disk.id)
                self._do_callback(self.disk_callbacks, disk)
        self.data["disks"] = disks

    async def _update_shares(self) -> None:
        shares = {}
        query_response = await self.api_client.query_shares()

        for share in query_response:
            shares[share.name] = share
            if share.name not in self.known_shares:
                self.known_shares.add(share.name)
                self._do_callback(self.share_callbacks, share)
        self.data["shares"] = shares

    async def _update_ups(self) -> None:
        devices = {}
        try:
            query_response = await self.api_client.query_ups()

            for device in query_response:
                devices[device.id] = device
                if device.id not in self.known_ups_devices:
                    self.known_ups_devices.add(device.id)
                    self._do_callback(self.ups_callbacks, device)
        except UnraidApiError as exc:
            _LOGGER.debug("UPS Update: %s", str(exc), exc_info=True)

        self.data["ups_devices"] = devices

    async def _update_docker(self) -> None:
        containers: dict[str, DockerContainer] = {}
        query_response = await self.api_client.query_docker()

        for container in query_response:
            if (
                self.config_entry.options[CONF_DOCKER_MODE] == DOCKER_MODE_ENABLED_ONLY
                and not container.label_monitor
            ):
                continue
            if (
                self.config_entry.options[CONF_DOCKER_MODE] == DOCKER_MODE_EXCEPT_DISABLED
                and container.label_monitor is False
            ):
                continue

            container_name = container.label_name or container.name
            if container_name in containers:
                _LOGGER.warning("Duplicate container name %s", container_name)
                containers.pop(container_name)
                continue
            containers[container_name] = container

        self.data["docker_containers"] = containers
        found_containers = set(containers.keys())
        known_containers = set(self.config_entry.runtime_data.containers.keys())
        new_containers = found_containers - known_containers
        removed_containers = known_containers - found_containers

        for container_name in new_containers:
            container = containers[container_name]
            device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{self.config_entry.entry_id}_docker_{container_name}")},
                name=f"{self.config_entry.runtime_data.device_info['name']} {container_name}",
                via_device=(DOMAIN, self.config_entry.entry_id),
                entry_type=DeviceEntryType.SERVICE,
            )
            if container.label_unraid_webui:
                device_info["configuration_url"] = container.label_unraid_webui
            if container.label_opencontainers_version:
                device_info["sw_version"] = container.label_opencontainers_version

            self.config_entry.runtime_data.containers[container_name] = Container(
                device_info=device_info, entities=[]
            )
            self._do_callback(self.docker_callbacks, container_name)

        for container_name in removed_containers:
            _LOGGER.debug("Removing Docker container: %s", container_name)
            container = self.config_entry.runtime_data.containers.pop(container_name)
            for entity in container["entities"]:
                await entity.async_remove()

            device_registry = dr.async_get(self.hass)
            device = device_registry.async_get_device(
                identifiers={(DOMAIN, f"{self.config_entry.entry_id}_docker_{container_name}")}
            )
            if device:
                device_registry.async_update_device(
                    device_id=device.id,
                    remove_config_entry_id=self.config_entry.entry_id,
                )

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

    def subscribe_docker(self, callback: Callable[[str], None]) -> None:
        self.docker_callbacks.add(callback)
        for container_name in self.config_entry.runtime_data.containers:
            self._do_callback([callback], container_name)

    def _cpu_metrics_callback(self, data: CpuMetricsSubscription) -> None:
        self.data["cpu_metrics"] = data
        self.async_update_listeners()

    def _cpu_usage_callback(self, data: float) -> None:
        self.data["cpu_usage"] = data
        self.async_update_listeners()

    def _memory_callback(self, data: MemorySubscription) -> None:
        self.data["memory"] = data
        self.async_update_listeners()

    def _do_callback(
        self, callbacks: set[Callable[..., None]], *args: tuple[Any], **kwargs: dict[Any]
    ) -> None:
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                _LOGGER.exception("Error in callback")

    async def start_container(self, container_name: str) -> None:
        container = self.data["docker_containers"][container_name]
        updated_container = await self.api_client.start_container(container.id)
        self.data["docker_containers"][container_name] = updated_container
        self.async_update_listeners()

    async def stop_container(self, container_name: str) -> None:
        container = self.data["docker_containers"][container_name]
        updated_container = await self.api_client.stop_container(container.id)
        self.data["docker_containers"][container_name] = updated_container
        self.async_update_listeners()
