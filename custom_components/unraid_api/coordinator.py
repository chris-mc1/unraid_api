"""Unraid update coordinator."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypedDict, TypeVar

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from awesomeversion import AwesomeVersion
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pydantic_core import ValidationError

from .api import IncompatibleApiError, UnraidAuthError, UnraidGraphQLError
from .const import (
    CONF_DOCKER,
    CONF_DRIVES,
    CONF_POLL_INTERVAL_DISKS,
    CONF_POLL_INTERVAL_DOCKER,
    CONF_POLL_INTERVAL_METRICS,
    CONF_POLL_INTERVAL_SHARES,
    CONF_POLL_INTERVAL_UPS,
    CONF_SHARES,
    DEFAULT_POLL_INTERVAL_DISKS,
    DEFAULT_POLL_INTERVAL_DOCKER,
    DEFAULT_POLL_INTERVAL_METRICS,
    DEFAULT_POLL_INTERVAL_SHARES,
    DEFAULT_POLL_INTERVAL_UPS,
    DOMAIN,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .api import UnraidApiClient
    from .models import Array, Disk, DockerContainer, Metrics, Share, UpsDevice

_LOGGER = logging.getLogger(__name__)


class UnraidServerData(TypedDict):  # noqa: D101
    metrics: Metrics | None
    array: Array | None
    disks: dict[str, Disk]
    shares: dict[str, Share]
    ups_devices: dict[str, UpsDevice]
    docker_containers: dict[str, DockerContainer]


class UnraidMetricsData(TypedDict):  # noqa: D101
    metrics: Metrics | None
    array: Array | None


class UnraidDisksData(TypedDict):  # noqa: D101
    disks: dict[str, Disk]


class UnraidSharesData(TypedDict):  # noqa: D101
    shares: dict[str, Share]


class UnraidDockerData(TypedDict):  # noqa: D101
    docker_containers: dict[str, DockerContainer]


class UnraidUpsData(TypedDict):  # noqa: D101
    ups_devices: dict[str, UpsDevice]


_TData = TypeVar("_TData")


class BaseUnraidCoordinator(DataUpdateCoordinator[_TData]):
    """Base coordinator with shared error handling."""

    api_client: UnraidApiClient
    config_entry: UnraidConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: UnraidConfigEntry,
        api_client: UnraidApiClient,
        name: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{name}",
            update_interval=update_interval,
        )
        self.api_client = api_client

    async def _handle_update_errors(self, exc: Exception) -> None:
        """Handle common update errors."""
        if isinstance(exc, ClientConnectorSSLError):
            _LOGGER.debug("Update: SSL error: %s", str(exc))
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="ssl_error",
                translation_placeholders={"error": str(exc)},
            ) from exc
        if isinstance(exc, (ClientConnectionError, TimeoutError)):
            _LOGGER.debug("Update: Connection error: %s", str(exc))
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(exc)},
            ) from exc
        if isinstance(exc, UnraidAuthError):
            _LOGGER.debug("Update: Auth failed")
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
                translation_placeholders={"error_msg": exc.args[0]},
            ) from exc
        if isinstance(exc, UnraidGraphQLError):
            _LOGGER.debug("Update: GraphQL Error response: %s", exc.response)
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="error_response",
                translation_placeholders={"error_msg": exc.args[0]},
            ) from exc
        if isinstance(exc, ValidationError):
            _LOGGER.debug("Update: invalid data")
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="data_invalid",
            ) from exc
        if isinstance(exc, IncompatibleApiError):
            _LOGGER.debug(
                "Update: Incompatible API, %s < %s",
                exc.version,
                exc.min_version,
            )
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="api_incompatible",
                translation_placeholders={
                    "min_version": exc.min_version,
                    "version": exc.version,
                },
            ) from exc


class UnraidMetricsCoordinator(BaseUnraidCoordinator[UnraidMetricsData]):
    """Coordinator for Metrics (CPU/RAM) and Array data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: UnraidConfigEntry,
        api_client: UnraidApiClient,
    ) -> None:
        interval_seconds = int(
            config_entry.options.get(
                CONF_POLL_INTERVAL_METRICS, DEFAULT_POLL_INTERVAL_METRICS
            )
        )
        super().__init__(
            hass,
            config_entry,
            api_client,
            "metrics",
            timedelta(seconds=interval_seconds),
        )

    async def _async_update_data(self) -> UnraidMetricsData:
        """Fetch metrics and array data."""
        data: UnraidMetricsData = {
            "metrics": None,
            "array": None,
        }
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._update_metrics(data))
                tg.create_task(self._update_array(data))
        except* Exception as exc:
            await self._handle_update_errors(exc.exceptions[0])
            raise

        return data

    async def _update_metrics(self, data: UnraidMetricsData) -> None:
        data["metrics"] = await self.api_client.query_metrics()

    async def _update_array(self, data: UnraidMetricsData) -> None:
        data["array"] = await self.api_client.query_array()


class UnraidDisksCoordinator(BaseUnraidCoordinator[UnraidDisksData]):
    """Coordinator for Disk data."""

    known_disks: set[str]
    disk_callbacks: set[Callable[[Disk], None]]

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: UnraidConfigEntry,
        api_client: UnraidApiClient,
    ) -> None:
        interval_seconds = int(
            config_entry.options.get(CONF_POLL_INTERVAL_DISKS, DEFAULT_POLL_INTERVAL_DISKS)
        )
        super().__init__(
            hass,
            config_entry,
            api_client,
            "disks",
            timedelta(seconds=interval_seconds),
        )
        self.known_disks: set[str] = set()
        self.disk_callbacks: set[Callable[[Disk], None]] = set()

    async def _async_update_data(self) -> UnraidDisksData:
        """Fetch disk data."""
        data: UnraidDisksData = {"disks": {}}
        try:
            await self._update_disks(data)
        except* Exception as exc:
            await self._handle_update_errors(exc.exceptions[0])
            raise

        return data

    async def _update_disks(self, data: UnraidDisksData) -> None:
        disks = {}
        query_response = await self.api_client.query_disks()

        for disk in query_response:
            disks[disk.id] = disk
            if disk.id not in self.known_disks:
                self.known_disks.add(disk.id)
                _do_callback(self.disk_callbacks, disk)
        data["disks"] = disks

    def subscribe_disks(self, callback: Callable[[Disk], None]) -> None:
        """Subscribe to disk updates."""
        self.disk_callbacks.add(callback)
        for disk_id in self.known_disks:
            _do_callback([callback], self.data["disks"][disk_id])


class UnraidSharesCoordinator(BaseUnraidCoordinator[UnraidSharesData]):
    """Coordinator for Share data."""

    known_shares: set[str]
    share_callbacks: set[Callable[[Share], None]]

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: UnraidConfigEntry,
        api_client: UnraidApiClient,
    ) -> None:
        interval_seconds = int(
            config_entry.options.get(CONF_POLL_INTERVAL_SHARES, DEFAULT_POLL_INTERVAL_SHARES)
        )
        super().__init__(
            hass,
            config_entry,
            api_client,
            "shares",
            timedelta(seconds=interval_seconds),
        )
        self.known_shares: set[str] = set()
        self.share_callbacks: set[Callable[[Share], None]] = set()

    async def _async_update_data(self) -> UnraidSharesData:
        """Fetch share data."""
        data: UnraidSharesData = {"shares": {}}
        try:
            await self._update_shares(data)
        except* Exception as exc:
            await self._handle_update_errors(exc.exceptions[0])
            raise

        return data

    async def _update_shares(self, data: UnraidSharesData) -> None:
        shares = {}
        query_response = await self.api_client.query_shares()

        for share in query_response:
            shares[share.name] = share
            if share.name not in self.known_shares:
                self.known_shares.add(share.name)
                _do_callback(self.share_callbacks, share)
        data["shares"] = shares

    def subscribe_shares(self, callback: Callable[[Share], None]) -> None:
        """Subscribe to share updates."""
        self.share_callbacks.add(callback)
        for share_name in self.known_shares:
            _do_callback([callback], self.data["shares"][share_name])


class UnraidDockerCoordinator(BaseUnraidCoordinator[UnraidDockerData]):
    """Coordinator for Docker container data."""

    known_docker_containers: set[str]
    docker_callbacks: set[Callable[[DockerContainer], None]]

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: UnraidConfigEntry,
        api_client: UnraidApiClient,
    ) -> None:
        interval_seconds = int(
            config_entry.options.get(CONF_POLL_INTERVAL_DOCKER, DEFAULT_POLL_INTERVAL_DOCKER)
        )
        super().__init__(
            hass,
            config_entry,
            api_client,
            "docker",
            timedelta(seconds=interval_seconds),
        )
        self.known_docker_containers: set[str] = set()
        self.docker_callbacks: set[Callable[[DockerContainer], None]] = set()

    async def _async_update_data(self) -> UnraidDockerData:
        """Fetch Docker container data."""
        data: UnraidDockerData = {"docker_containers": {}}
        try:
            await self._update_docker(data)
        except* UnraidGraphQLError as exc:
            _LOGGER.warning("Update: Docker GraphQL Error: %s", exc)
            # Don't fail the entire update if Docker query fails
        except* Exception as exc:
            _LOGGER.warning("Update: Docker error: %s", exc, exc_info=True)
            # Don't fail the entire update if Docker query fails

        return data

    async def _update_docker(self, data: UnraidDockerData) -> None:
        containers = {}
        try:
            query_response = await self.api_client.query_docker_containers()
            _LOGGER.debug("Docker query returned %d containers", len(query_response))

            for container in query_response:
                containers[container.id] = container
                _LOGGER.debug(
                    "Processing Docker container: %s (id: %s)", container.name, container.id
                )
                if container.id not in self.known_docker_containers:
                    self.known_docker_containers.add(container.id)
                    _LOGGER.debug("New Docker container discovered: %s", container.name)
                    _do_callback(self.docker_callbacks, container)
        except UnraidGraphQLError as exc:
            _LOGGER.warning("Update: Docker GraphQL Error: %s", exc)
            # Don't fail the entire update if Docker query fails
        except Exception as exc:
            _LOGGER.warning("Update: Docker error: %s", exc, exc_info=True)

        data["docker_containers"] = containers
        _LOGGER.debug("Docker containers in data: %d", len(containers))

    def subscribe_docker(self, callback: Callable[[DockerContainer], None]) -> None:
        """Subscribe to Docker container updates."""
        self.docker_callbacks.add(callback)
        for container_id in self.known_docker_containers:
            _do_callback([callback], self.data["docker_containers"][container_id])


class UnraidUpsCoordinator(BaseUnraidCoordinator[UnraidUpsData]):
    """Coordinator for UPS device data."""

    known_ups_devices: set[str]
    ups_callbacks: set[Callable[[UpsDevice], None]]

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: UnraidConfigEntry,
        api_client: UnraidApiClient,
    ) -> None:
        interval_seconds = int(
            config_entry.options.get(CONF_POLL_INTERVAL_UPS, DEFAULT_POLL_INTERVAL_UPS)
        )
        super().__init__(
            hass,
            config_entry,
            api_client,
            "ups",
            timedelta(seconds=interval_seconds),
        )
        self.known_ups_devices: set[str] = set()
        self.ups_callbacks: set[Callable[[UpsDevice], None]] = set()

    async def _async_update_data(self) -> UnraidUpsData:
        """Fetch UPS device data."""
        data: UnraidUpsData = {"ups_devices": {}}
        try:
            await self._update_ups(data)
        except* UnraidGraphQLError:
            # UPS may not be available, don't fail
            pass
        except* Exception as exc:
            await self._handle_update_errors(exc.exceptions[0])
            raise

        return data

    async def _update_ups(self, data: UnraidUpsData) -> None:
        devices = {}
        try:
            query_response = await self.api_client.query_ups()

            for device in query_response:
                devices[device.id] = device
                if device.id not in self.known_ups_devices:
                    self.known_ups_devices.add(device.id)
                    _do_callback(self.ups_callbacks, device)
        except UnraidGraphQLError:
            pass

        data["ups_devices"] = devices

    def subscribe_ups(self, callback: Callable[[UpsDevice], None]) -> None:
        """Subscribe to UPS device updates."""
        self.ups_callbacks.add(callback)
        for ups_id in self.known_ups_devices:
            _do_callback([callback], self.data["ups_devices"][ups_id])


# Helper method for callbacks
def _do_callback(
    callbacks: set[Callable[..., None]], *args: tuple[Any], **kwargs: dict[Any]
) -> None:
    """Execute callbacks safely."""
    for callback in callbacks:
        try:
            callback(*args, **kwargs)
        except Exception:
            _LOGGER.exception("Error in callback")


# Legacy coordinator for backward compatibility (will be removed in future)
class UnraidDataUpdateCoordinator(BaseUnraidCoordinator[UnraidServerData]):
    """Legacy Update Coordinator - kept for backward compatibility."""

    known_disks: set[str]
    known_shares: set[str]
    known_ups_devices: set[str]
    known_docker_containers: set[str]

    def __init__(
        self, hass: HomeAssistant, config_entry: UnraidConfigEntry, api_client: UnraidApiClient
    ) -> None:
        super().__init__(
            hass,
            config_entry,
            api_client,
            "legacy",
            timedelta(minutes=1),
        )
        self.disk_callbacks: set[Callable[[Disk], None]] = set()
        self.share_callbacks: set[Callable[[Share], None]] = set()
        self.ups_callbacks: set[Callable[[UpsDevice], None]] = set()
        self.docker_callbacks: set[Callable[[DockerContainer], None]] = set()

    async def _async_setup(self) -> None:
        self.known_disks: set[str] = set()
        self.known_shares: set[str] = set()
        self.known_ups_devices: set[str] = set()
        self.known_docker_containers: set[str] = set()

    async def _async_update_data(self) -> UnraidServerData:
        data: UnraidServerData = {
            "metrics": None,
            "array": None,
            "disks": {},
            "shares": {},
            "ups_devices": {},
            "docker_containers": {},
        }
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._update_metrics(data))
                tg.create_task(self._update_array(data))
                if self.config_entry.options[CONF_DRIVES]:
                    tg.create_task(self._update_disks(data))
                if self.config_entry.options[CONF_SHARES]:
                    tg.create_task(self._update_shares(data))
                if self.config_entry.options[CONF_DOCKER]:
                    tg.create_task(self._update_docker(data))
                if self.api_client.version >= AwesomeVersion("4.26.0"):
                    tg.create_task(self._update_ups(data))

        except* Exception as exc:
            await self._handle_update_errors(exc.exceptions[0])
            raise

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
                _do_callback(self.disk_callbacks, disk)
        data["disks"] = disks

    async def _update_shares(self, data: UnraidServerData) -> None:
        shares = {}
        query_response = await self.api_client.query_shares()

        for share in query_response:
            shares[share.name] = share
            if share.name not in self.known_shares:
                self.known_shares.add(share.name)
                _do_callback(self.share_callbacks, share)
        data["shares"] = shares

    async def _update_ups(self, data: UnraidServerData) -> None:
        devices = {}
        try:
            query_response = await self.api_client.query_ups()

            for device in query_response:
                devices[device.id] = device
                if device.id not in self.known_ups_devices:
                    self.known_ups_devices.add(device.id)
                    _do_callback(self.ups_callbacks, device)
        except UnraidGraphQLError:
            pass

        data["ups_devices"] = devices

    async def _update_docker(self, data: UnraidServerData) -> None:
        containers = {}
        try:
            query_response = await self.api_client.query_docker_containers()
            _LOGGER.debug("Docker query returned %d containers", len(query_response))

            for container in query_response:
                containers[container.id] = container
                _LOGGER.debug(
                    "Processing Docker container: %s (id: %s)", container.name, container.id
                )
                if container.id not in self.known_docker_containers:
                    self.known_docker_containers.add(container.id)
                    _LOGGER.debug("New Docker container discovered: %s", container.name)
                    _do_callback(self.docker_callbacks, container)
        except UnraidGraphQLError as exc:
            _LOGGER.warning("Update: Docker GraphQL Error: %s", exc)
        except Exception as exc:
            _LOGGER.warning("Update: Docker error: %s", exc, exc_info=True)

        data["docker_containers"] = containers
        _LOGGER.debug("Docker containers in data: %d", len(containers))

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

    def subscribe_docker(self, callback: Callable[[DockerContainer], None]) -> None:
        self.docker_callbacks.add(callback)
        for container_id in self.known_docker_containers:
            self._do_callback([callback], self.data["docker_containers"][container_id])

    def _do_callback(
        self, callbacks: set[Callable[..., None]], *args: tuple[Any], **kwargs: dict[Any]
    ) -> None:
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                _LOGGER.exception("Error in callback")
