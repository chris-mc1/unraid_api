"""Unraid API Exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import aiohttp
    from awesomeversion import AwesomeVersion


class UnraidApiError(Exception):
    """Base exception for Unraid API Errors."""


class UnraidApiInvalidResponseError(UnraidApiError):
    """Invalid response format."""

    def __init__(self, response: aiohttp.ClientResponse) -> None:
        self.response = response

    def __str__(self) -> str:
        return "Invalid response format."


class IncompatibleApiError(UnraidApiError):
    """Incompatible API version."""

    def __init__(self, version: AwesomeVersion, min_version: AwesomeVersion, *args: Any) -> None:
        self.version = version
        self.min_version = min_version

    def __str__(self) -> str:
        return f"Incompatible API version (Current: {self.version}, minimum: {self.min_version})"


class GraphQLBaseError(UnraidApiError):
    """Base exception for GraphQL Errors."""


class GraphQLError(GraphQLBaseError):
    """GraphQl Error."""

    message: str
    locations: list[dict[str, int]] | None = None
    path: list[str] | None = None
    extensions: dict[str, object] | None = None
    original: dict[str, object] | None = None

    def __init__(
        self,
        error: dict[str, Any],
    ) -> None:
        self.message = error["message"]
        self.locations = error.get("locations")
        self.path = error.get("path")
        self.extensions = error.get("extensions")
        self.original = error

    def __str__(self) -> str:
        return self.message


class GraphQLUnauthorizedError(GraphQLError):
    """Unauthorized."""


class GraphQLMultiError(GraphQLBaseError):
    """Multiple GraphQl Errors."""

    errors: list[GraphQLError]

    def __init__(self, errors_dicts: list[dict[str, Any]], data: dict[str, Any] | None) -> None:
        self.errors = [GraphQLError(e) for e in errors_dicts]
        self.data = data

    def __str__(self) -> str:
        return "; ".join(str(e) for e in self.errors)


class GraphQLInvalidMessageError(GraphQLBaseError):
    """Invalid message format."""

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return "Invalid message format."
