"""Helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiohttp import ClientConnectionError, ClientConnectorSSLError
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .exceptions import GraphQLError, GraphQLMultiError, GraphQLUnauthorizedError

if TYPE_CHECKING:
    from collections.abc import Callable

from . import _LOGGER


def error_handler[T](func: Callable[[], T]) -> Callable:
    """Handle API errors and raise HomeAssistantError."""

    async def decorated(*args: tuple[Any], **kwargs: dict[str, Any]) -> T:
        try:
            return await func(*args, **kwargs)
        except ClientConnectorSSLError as exc:
            _LOGGER.debug("Button: SSL error: %s", str(exc))
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="ssl_error",
                translation_placeholders={"error": str(exc)},
            ) from exc
        except (ClientConnectionError, TimeoutError) as exc:
            _LOGGER.debug("Button: Connection error: %s", str(exc))
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(exc)},
            ) from exc
        except GraphQLUnauthorizedError as exc:
            _LOGGER.debug("Button: Auth failed")
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
                translation_placeholders={"error_msg": str(exc)},
            ) from exc
        except (GraphQLError, GraphQLMultiError) as exc:
            _LOGGER.debug("Button: GraphQL Error response: %s", str(exc))
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="error_response",
                translation_placeholders={"error_msg": str(exc)},
            ) from exc

    return decorated
