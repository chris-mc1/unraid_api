"""GraphQL API responses for Tests."""

from __future__ import annotations

from typing import ClassVar

from awesomeversion import AwesomeVersion


class GraphqlResponses:
    """Graphql Responses Baseclass."""

    version = AwesomeVersion("4.20.0")
    api_version: ClassVar[dict]
    server_info: ClassVar[dict]
    metrics_array: ClassVar[dict]
    shares: ClassVar[dict]
    disks: ClassVar[dict]
    ups: ClassVar[dict]
    docker_containers: ClassVar[dict]

    cpu_percent_total: ClassVar[list[dict]]
    cpu_metrics: ClassVar[list[dict]]
    memory: ClassVar[list[dict]]

    start_container: ClassVar[dict]
    stop_container: ClassVar[dict]

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

    def get_response(self, query: str) -> dict:  # noqa: PLR0911, PLR0912
        try:
            if self.is_unauthenticated:
                return self.unauthenticated
            if self.all_error:
                return self.error
            match query:
                case "ApiVersion":
                    return self.api_version
                case "ServerInfo":
                    return self.server_info
                case "MetricsArray":
                    return self.metrics_array
                case "Shares":
                    return self.shares
                case "Disks":
                    return self.disks
                case "UpsDevices":
                    return self.ups
                case "DockerContainers":
                    return self.docker_containers
                case "DockerStart":
                    return self.start_container
                case "DockerStop":
                    return self.stop_container
                case _:
                    return self.not_found
        except ArithmeticError:
            return self.error

    def get_subscription(self, query: str, index: int = 0) -> dict:
        match query:
            case "CpuUsage":
                return self.cpu_percent_total[index]
            case "CpuMetrics":
                return self.cpu_metrics[index]
            case "Memory":
                return self.memory[index]


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
        self.metrics_array = {
            "data": {
                "metrics": {
                    "memory": {
                        "total": 16646950912,
                        "active": 12746354688,
                        "percentTotal": 76.56870471583932,
                        "available": 3900596224,
                    },
                    "cpu": {"percentTotal": 5.1},
                },
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
                },
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
        self.docker_containers = {
            "data": {
                "docker": {
                    "containers": [
                        {
                            "id": "4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:9591842fdb0e817f385407d6eb71d0070bcdfd3008506d5e7e53c3036939c2b0",  # noqa: E501
                            "names": ["/homeassistant"],
                            "state": "RUNNING",
                            "labels": {
                                "org.opencontainers.image.authors": "The Home Assistant Authors",
                                "org.opencontainers.image.created": "2026-02-13 20:09:43+00:00",
                                "org.opencontainers.image.description": "Open-source home automation platform running on Python 3",  # noqa: E501
                                "org.opencontainers.image.documentation": "https://www.home-assistant.io/docs/",
                                "org.opencontainers.image.licenses": "Apache-2.0",
                                "org.opencontainers.image.source": "https://github.com/home-assistant/core",
                                "org.opencontainers.image.title": "Home Assistant",
                                "org.opencontainers.image.url": "https://www.home-assistant.io/",
                                "org.opencontainers.image.version": "2026.2.2",
                                "net.unraid.docker.icon": "",
                                "net.unraid.docker.managed": "composeman",
                                "net.unraid.docker.shell": "",
                                "net.unraid.docker.webui": "homeassistant.unraid.lan",
                            },
                            "image": "ghcr.io/home-assistant/home-assistant:stable",
                            "imageId": "sha256:e0477b544d48b26ad81e2132b8ce36f0a20dfd7eb44de9c40718fa78dc92e24d",  # noqa: E501
                            "status": "Up 28 minutes",
                        },
                        {
                            "id": "4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:db6215c5578bd28bc78fab45e16b7a2d6d94ec3bb3b23a5ad5b8b4979e79bf86",  # noqa: E501
                            "names": ["/postgres"],
                            "state": "RUNNING",
                            "labels": {
                                "net.unraid.docker.icon": "",
                                "net.unraid.docker.managed": "composeman",
                                "net.unraid.docker.shell": "",
                                "net.unraid.docker.webui": "",
                                "io.home-assistant.unraid_api.name": "Postgres",
                                "io.home-assistant.unraid_api.monitor": "false",
                            },
                            "image": "postgres:15",
                            "imageId": "sha256:a748a13f04094ee02b167d3e2a919368bc5e93cbd2b1c41a6d921dbaa59851ac",  # noqa: E501
                            "status": "Up 28 minutes",
                        },
                        {
                            "id": "4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:cc3843b7435c45ba8ff9c10b7e3c494d51fc303e609d12825b63537be52db369",  # noqa: E501
                            "names": ["/grafana"],
                            "state": "EXITED",
                            "labels": {
                                "net.unraid.docker.icon": "",
                                "net.unraid.docker.managed": "composeman",
                                "net.unraid.docker.shell": "",
                                "net.unraid.docker.webui": "",
                                "io.home-assistant.unraid_api.name": "Grafana Public",
                                "io.home-assistant.unraid_api.monitor": "true",
                            },
                            "image": "grafana/grafana-enterprise",
                            "imageId": "sha256:32241300d32d708c29a186e61692ff00d6c3f13cb862246326edd4612d735ae5",  # noqa: E501
                            "status": "Up 28 minutes",
                        },
                    ]
                }
            }
        }

        ## Subscription
        self.cpu_percent_total = [
            {"systemMetricsCpu": {"percentTotal": 5.1}},
            {"systemMetricsCpu": {"percentTotal": 7.5}},
        ]
        self.memory = [
            {
                "systemMetricsMemory": {
                    "total": 16644698112,
                    "percentTotal": 70.72346589159935,
                    "active": 11771707392,
                    "available": 4872990720,
                }
            },
            {
                "systemMetricsMemory": {
                    "total": 16644698112,
                    "percentTotal": 71.88141588085776,
                    "active": 11964444672,
                    "available": 4680253440,
                }
            },
        ]

        ## Mutations
        self.start_container = {
            "data": {
                "docker": {
                    "start": {
                        "id": "4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:cc3843b7435c45ba8ff9c10b7e3c494d51fc303e609d12825b63537be52db369",  # noqa: E501
                        "names": ["/grafana"],
                        "state": "RUNNING",
                        "labels": {},
                        "image": "grafana/grafana-enterprise",
                        "imageId": "sha256:32241300d32d708c29a186e61692ff00d6c3f13cb862246326edd4612d735ae5",  # noqa: E501
                        "status": "Up 28 minutes",
                    }
                }
            }
        }
        self.stop_container = {
            "data": {
                "docker": {
                    "stop": {
                        "id": "4d5df9c6bac5b77205f8e09cbe31fbd230d7735625d8853c7740893ab1c98e65:9591842fdb0e817f385407d6eb71d0070bcdfd3008506d5e7e53c3036939c2b0",  # noqa: E501
                        "names": ["/homeassistant"],
                        "state": "EXITED",
                        "labels": {},
                        "image": "ghcr.io/home-assistant/home-assistant:stable",
                        "imageId": "sha256:e0477b544d48b26ad81e2132b8ce36f0a20dfd7eb44de9c40718fa78dc92e24d",  # noqa: E501
                        "status": "Up 28 minutes",
                    }
                }
            }
        }


class GraphqlResponses426(GraphqlResponses420):
    """Graphql Responses for version 4.26."""

    version = AwesomeVersion("4.26.0")

    def __init__(self) -> None:
        super().__init__()

        ## Queries
        self.api_version = {"data": {"info": {"versions": {"core": {"api": "4.26.0"}}}}}
        self.metrics_array = {
            "data": {
                "metrics": {
                    "memory": {
                        "total": 16646950912,
                        "active": 12746354688,
                        "percentTotal": 76.56870471583932,
                        "available": 3900596224,
                    },
                    "cpu": {"percentTotal": 5.1},
                },
                "info": {"cpu": {"packages": {"power": [2.8], "temp": [31]}}},
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
                },
            }
        }
        self.ups = {
            "data": {
                "upsDevices": [
                    {
                        "battery": {"chargeLevel": 100, "estimatedRuntime": 25, "health": "Good"},
                        "power": {
                            "loadPercentage": 20,
                            "outputVoltage": 120.5,
                            "inputVoltage": 232,
                        },
                        "model": "Back-UPS ES 650G2",
                        "name": "Back-UPS ES 650G2",
                        "status": "ONLINE",
                        "id": "Back-UPS ES 650G2",
                    }
                ]
            }
        }

        ## Subscription
        self.cpu_metrics = [
            {"systemMetricsCpuTelemetry": {"temp": [31], "power": [2.8]}},
            {"systemMetricsCpuTelemetry": {"temp": [35], "power": [3.5]}},
        ]


class GraphqlResponses429(GraphqlResponses426):
    """Graphql Responses for version 4.29."""

    version = AwesomeVersion("4.29.0")

    def __init__(self) -> None:
        super().__init__()
        ## Queries
        self.api_version = {"data": {"info": {"versions": {"core": {"api": "4.29.0"}}}}}


class GraphqlResponses410(GraphqlResponses420):
    """Graphql Responses for version 4.10 (Incompatible)."""

    version = AwesomeVersion("4.10.0")

    def __init__(self) -> None:
        self.api_version = {"data": {"info": {"versions": {"core": {"api": "4.10.0"}}}}}


API_RESPONSES = [GraphqlResponses420, GraphqlResponses426]

API_RESPONSES_LATEST = API_RESPONSES[-1]
