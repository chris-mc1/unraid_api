"""GraphQL API responses for Tests."""

from __future__ import annotations

from typing import ClassVar

from awesomeversion import AwesomeVersion


class GraphqlResponses:
    """Graphql Responses Baseclass."""

    version = AwesomeVersion("4.20.0")
    api_version: ClassVar[dict]
    server_info: ClassVar[dict]
    metrics: ClassVar[dict]
    shares: ClassVar[dict]
    disks: ClassVar[dict]
    array: ClassVar[dict]

    is_unauthenticated = False
    unauthenticated: ClassVar[dict] = {
        "errors": [
            {
                "message": "API key validation failed",
                "locations": [{"line": 3, "column": 3}],
                "path": ["info"],
                "extensions": {
                    "code": "UNAUTHENTICATED",
                    "originalError": {
                        "message": "API key validation failed",
                        "error": "Unauthorized",
                        "statusCode": 401,
                    },
                },
            }
        ],
        "data": None,
    }

    all_error = False
    error: ClassVar[dict] = {
        "errors": [
            {
                "message": "Internal Server error",
                "locations": [{"line": 18, "column": 3}],
                "path": ["info"],
                "extensions": {"code": "INTERNAL_SERVER_ERROR"},
            }
        ],
        "data": None,
    }

    not_found: ClassVar[dict] = {
        "errors": [
            {
                "message": "Cannot query field",
                "locations": [{"line": 3, "column": 5}],
                "extensions": {"code": "GRAPHQL_VALIDATION_FAILED"},
            }
        ]
    }

    def get_response(self, query: str) -> dict:  # noqa: PLR0911
        if self.is_unauthenticated:
            return self.unauthenticated
        if self.all_error:
            return self.error
        match query:
            case "ApiVersion":
                return self.api_version
            case "ServerInfo":
                return self.server_info
            case "Metrics":
                return self.metrics
            case "Shares":
                return self.shares
            case "Disks":
                return self.disks
            case "Array":
                return self.array
            case _:
                return self.not_found


class GraphqlResponses420(GraphqlResponses):
    """Graphql Responses for version 4.20."""

    version = AwesomeVersion("4.20.0")

    def __init__(self) -> None:
        self.api_version = {"data": {"info": {"versions": {"core": {"api": "4.20.0+196bd52"}}}}}
        self.server_info = {
            "data": {
                "server": {"localurl": "http://1.2.3.4", "name": "Test Server"},
                "info": {"versions": {"core": {"unraid": "7.0.1"}}},
            }
        }
        self.metrics = {
            "data": {
                "metrics": {
                    "memory": {
                        "free": 415510528,
                        "total": 16646950912,
                        "active": 12746354688,
                        "percentTotal": 76.56870471583932,
                        "available": 3900596224,
                    },
                    "cpu": {"percentTotal": 5.1},
                }
            }
        }

        self.shares = {
            "data": {
                "shares": [
                    {
                        "name": "Share_1",
                        "free": 523094721,
                        "used": 11474981429,
                        "size": 0,
                        "allocator": "highwater",
                        "floor": "20000000",
                    },
                    {
                        "name": "Share_2",
                        "free": 503491121,
                        "used": 5615496143,
                        "size": 0,
                        "allocator": "highwater",
                        "floor": "0",
                    },
                ]
            }
        }
        self.disks = {
            "data": {
                "array": {
                    "disks": [
                        {
                            "name": "disk1",
                            "status": "DISK_OK",
                            "temp": 34,
                            "fsSize": 5999038075,
                            "fsFree": 464583438,
                            "fsUsed": 5534454637,
                            "type": "DATA",
                            "id": "c6b",
                            "isSpinning": True,
                        },
                    ],
                    "parities": [
                        {
                            "name": "parity",
                            "status": "DISK_OK",
                            "temp": None,
                            "fsSize": None,
                            "fsFree": None,
                            "fsUsed": None,
                            "type": "PARITY",
                            "id": "4d5",
                            "isSpinning": False,
                        }
                    ],
                    "caches": [
                        {
                            "name": "cache",
                            "status": "DISK_OK",
                            "temp": 30,
                            "fsSize": 119949189,
                            "fsFree": 38907683,
                            "fsUsed": 81041506,
                            "type": "CACHE",
                            "id": "8e0",
                            "isSpinning": True,
                        }
                    ],
                }
            }
        }
        self.array = {
            "data": {
                "array": {
                    "state": "STARTED",
                    "capacity": {
                        "kilobytes": {
                            "free": "523094720",
                            "used": "11474981430",
                            "total": "11998076150",
                        }
                    },
                    "parityCheckStatus": {
                        "date": "2025-09-27T22:00:01.000Z",
                        "duration": 5982,
                        "speed": "10",
                        "status": "COMPLETED",
                        "errors": None,
                        "progress": 0,
                    },
                }
            }
        }
        self.not_found = {
            "errors": [
                {
                    "message": "Cannot query field",
                    "locations": [{"line": 3, "column": 5}],
                    "extensions": {"code": "GRAPHQL_VALIDATION_FAILED"},
                }
            ]
        }


class GraphqlResponses410(GraphqlResponses420):
    """Graphql Responses for version 4.10 (Incompatible)."""

    version = AwesomeVersion("4.10.0")

    def __init__(self) -> None:
        self.api_version = {"data": {"info": {"versions": {"core": {"api": "4.10"}}}}}


API_RESPONSES = [GraphqlResponses420]

API_RESPONSES_LATEST = API_RESPONSES[-1]
