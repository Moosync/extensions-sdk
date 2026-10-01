from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    MainCommand,
    MainCommandResponse,
)


class Scope(Enum):
    SESSION = "session"
    LOCAL = "local"


@dataclass
class Expectation:
    command: MainCommand
    response: MainCommandResponse | Callable[[], MainCommandResponse]
    times: int


@dataclass
class SystemTimeExpectation:
    return_value: int | Callable[[], int]
    times: int


@dataclass
class HashExpectation:
    hash_type: str
    data: bytes
    return_value: bytes | Callable[[], bytes]
    times: int


@dataclass
class OpenClientFdExpectation:
    path: str
    return_value: int | Callable[[], int]
    times: int


@dataclass
class WriteSockExpectation:
    sock_id: int
    buf: bytes
    return_value: int | Callable[[], int]
    times: int


@dataclass
class ReadSockExpectation:
    sock_id: int
    read_len: int
    return_value: bytes | Callable[[], bytes]
    times: int


@dataclass
class BatchHttpRequestExpectation:
    requests: BatchHttpRequest
    response: BatchHttpResponse | Callable[[], BatchHttpResponse]
    times: int


@dataclass
class ReplayIgnoreRule:
    request_filter: Any
    ignore_fields: list[str] = field(default_factory=list)
    regex: str | None = None
    remaining_times: int = -1
    test_name: str | None = None
