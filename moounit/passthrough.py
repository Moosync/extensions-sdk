import hashlib
import os
import re
import socket
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    HttpRequest,
    HttpResponse,
    HttpResult,
)

ENV_VAR_REGEX = re.compile(r"\{([A-Z_][A-Z0-9_]*)\}")


def resolve_allowed_paths(permissions_paths: dict[str, str]) -> dict[str, str]:
    """
    Resolves environment variables in allowed_paths keys and checks existence.
    Returns mapping of real system directory path -> mapped virtual path (e.g. '/').
    """
    resolved = {}
    for key, value in permissions_paths.items():
        parsed = ENV_VAR_REGEX.sub(
            lambda m: os.environ.get(m.group(1), ""),
            key,
        )
        if parsed and os.path.exists(parsed):
            resolved[parsed] = value
    return resolved


class RealSocketManager:
    def __init__(self, allowed_paths: dict[str, str]):
        self.allowed_paths = resolve_allowed_paths(allowed_paths)
        self.sockets: list[socket.socket | None] = []

    def open_clientfd(self, sock_path: str) -> int:
        # Match sock_path against allowed_paths
        for host_dir, virtual_dir in self.allowed_paths.items():
            if sock_path.startswith(virtual_dir):
                rel_path = sock_path[len(virtual_dir) :].lstrip("/")
                real_path = os.path.join(host_dir, rel_path)
                if os.path.exists(real_path):
                    try:
                        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        s.settimeout(5.0)
                        s.connect(real_path)
                        self.sockets.append(s)
                        return len(self.sockets) - 1
                    except Exception as e:
                        print(
                            f"RealSocketManager: Failed to connect to {real_path}: {e}"
                        )
                        return -1

        # Direct fallback check for host path
        if os.path.exists(sock_path):
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(5.0)
                s.connect(sock_path)
                self.sockets.append(s)
                return len(self.sockets) - 1
            except Exception as e:
                print(f"RealSocketManager: Failed to connect to {sock_path}: {e}")
                return -1

        return -1

    def write_sock(self, sock_id: int, buf: bytes) -> int:
        if sock_id < 0 or sock_id >= len(self.sockets):
            return -1
        sock = self.sockets[sock_id]
        if not sock:
            return -1
        try:
            sock.sendall(buf)
            return len(buf)
        except Exception as e:
            print(f"RealSocketManager: write error on {sock_id}: {e}")
            return -1

    def read_sock(self, sock_id: int, read_len: int) -> bytes:
        if sock_id < 0 or sock_id >= len(self.sockets):
            return b""
        sock = self.sockets[sock_id]
        if not sock:
            return b""
        if read_len <= 0:
            return b""
        data = bytearray()
        while len(data) < read_len:
            to_read = min(read_len - len(data), 4096)
            try:
                chunk = sock.recv(to_read)
                if not chunk:
                    break
                data.extend(chunk)
            except Exception as e:
                print(f"RealSocketManager: read error on {sock_id}: {e}")
                break
        return bytes(data)

    def close_all(self):
        for s in self.sockets:
            if s:
                try:
                    s.close()
                except Exception:
                    pass
        self.sockets.clear()


def get_real_system_time() -> int:
    return int(time.time())


def get_real_hash(hash_type: str, data: bytes) -> bytes:
    try:
        h = hashlib.new(hash_type)
        h.update(data)
        return h.digest()
    except Exception as e:
        print(f"Real hash calculation failed for {hash_type}: {e}")
        return b""


def execute_single_http_request(req: HttpRequest) -> HttpResult:
    try:
        method = req.method.upper() if req.method else "GET"
        body = req.body if req.body else None
        headers = dict(req.headers)
        timeout = (
            (req.timeout_ms / 1000.0) if req.timeout_ms and req.timeout_ms > 0 else 30.0
        )

        request = urllib.request.Request(
            url=req.url,
            data=body,
            headers=headers,
            method=method,
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            status_text = response.msg if hasattr(response, "msg") else "OK"
            resp_headers = {k: v for k, v in response.headers.items()}
            resp_body = response.read()

            return HttpResult(
                response=HttpResponse(
                    status_code=status_code,
                    status_text=str(status_text),
                    headers=resp_headers,
                    body=resp_body,
                )
            )
    except urllib.error.HTTPError as e:
        resp_headers = (
            {k: v for k, v in e.headers.items()} if hasattr(e, "headers") else {}
        )
        resp_body = e.read() if hasattr(e, "read") else b""
        return HttpResult(
            response=HttpResponse(
                status_code=e.code,
                status_text=str(e.reason),
                headers=resp_headers,
                body=resp_body,
            )
        )
    except Exception as e:
        return HttpResult(error=str(e))


def execute_real_batch_http_request(batch: BatchHttpRequest) -> BatchHttpResponse:
    with ThreadPoolExecutor(max_workers=min(len(batch.requests) or 1, 10)) as executor:
        results = list(executor.map(execute_single_http_request, batch.requests))
    return BatchHttpResponse(responses=results)
