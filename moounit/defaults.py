from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    HttpResponse,
    HttpResult,
    MainCommand,
    MainCommandResponse,
)
from moounit.generated import default_main_command_response


def default_batch_http_response(req: BatchHttpRequest) -> BatchHttpResponse:
    results = []
    for _ in req.requests:
        results.append(
            HttpResult(
                response=HttpResponse(
                    status_code=200,
                    status_text="OK",
                    headers={},
                    body=b"",
                )
            )
        )
    return BatchHttpResponse(responses=results)


def default_system_time() -> int:
    return 0


def default_open_clientfd(_path: str) -> int:
    return 100


def default_write_sock(_sock_id: int, buf: bytes) -> int:
    return len(buf)


def default_read_sock(_sock_id: int, _read_len: int) -> bytes:
    return b""
