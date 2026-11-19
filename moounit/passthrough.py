import base64
import hashlib
import os
import re
import socket
import ssl
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    HttpRequest,
    HttpResponse,
    HttpResult,
    OpenClientFdRequest,
    OpenClientFdResponse,
    ReadSockRequest,
    ReadSockResponse,
    SystemTimeRequest,
    SystemTimeResponse,
    WriteSockRequest,
    WriteSockResponse,
    WsCloseRequest,
    WsCloseResponse,
    WsConnectRequest,
    WsConnectResponse,
    WsReceiveRequest,
    WsReceiveResponse,
    WsSendRequest,
    WsSendResponse,
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

    def open_client_fd(self, req: OpenClientFdRequest) -> OpenClientFdResponse:
        sock_id = self.open_clientfd(req.path)
        if sock_id < 0:
            raise ConnectionError(f"Failed to connect to socket: {req.path}")
        return OpenClientFdResponse(sock_id=sock_id)

    def write_sock(self, req: WriteSockRequest) -> WriteSockResponse:
        written = self._write_sock_raw(req.sock_id, req.buf)
        if written < 0:
            raise ConnectionError(f"Failed to write to socket: {req.sock_id}")
        return WriteSockResponse(bytes_written=written)

    def read_sock(self, req: ReadSockRequest) -> ReadSockResponse:
        data = self._read_sock_raw(req.sock_id, req.read_len)
        return ReadSockResponse(data=data)

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

    def _write_sock_raw(self, sock_id: int, buf: bytes) -> int:
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

    def _read_sock_raw(self, sock_id: int, read_len: int) -> bytes:
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


def get_real_system_time(_req: SystemTimeRequest | None = None) -> SystemTimeResponse:
    return SystemTimeResponse(timestamp=int(time.time()))


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


def is_host_allowed(host: str, allowed_hosts: list[str] | None) -> bool:
    if not allowed_hosts:
        return False
    host_lower = host.lower()
    for pattern in allowed_hosts:
        p_lower = pattern.lower()
        if p_lower == "*":
            return True
        if p_lower.startswith("*."):
            bare = p_lower[2:]
            if host_lower == bare or host_lower.endswith("." + bare):
                return True
        if p_lower == host_lower:
            return True
    return False


class RealWebSocketManager:
    def __init__(self, allowed_hosts: list[str] | None = None):
        self.allowed_hosts = allowed_hosts
        self.connections: dict[int, Any] = {}
        self.next_id = 1

    def ws_connect(self, req: WsConnectRequest) -> WsConnectResponse:
        import websocket

        url = req.url
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        if not is_host_allowed(host, self.allowed_hosts):
            raise PermissionError(
                f"Host '{host}' is not allowed by extension manifest permissions.hosts"
            )

        header_list = [f"{k}: {v}" for k, v in req.headers.items()]
        subprotocols = list(req.protocols) if req.protocols else None

        ws = websocket.create_connection(
            url,
            timeout=5.0,
            header=header_list,
            subprotocols=subprotocols,
        )

        conn_id = self.next_id
        self.next_id += 1
        self.connections[conn_id] = ws
        return WsConnectResponse(connection_id=conn_id)

    def ws_send(self, req: WsSendRequest) -> WsSendResponse:
        import websocket

        conn_id = req.connection_id
        ws = self.connections.get(conn_id)
        if not ws:
            raise ConnectionError(f"WebSocket connection {conn_id} not found")

        field = req.WhichOneof("payload")
        if field == "text":
            ws.send(req.text, opcode=websocket.ABNF.OPCODE_TEXT)
        elif field == "binary":
            ws.send_binary(req.binary)

        return WsSendResponse(success=True)

    def ws_receive(self, req: WsReceiveRequest) -> WsReceiveResponse:
        import websocket

        conn_id = req.connection_id
        ws = self.connections.get(conn_id)
        if not ws:
            raise ConnectionError(f"WebSocket connection {conn_id} not found")

        timeout_s = (
            (req.timeout_ms / 1000.0)
            if req.HasField("timeout_ms") and req.timeout_ms > 0
            else 1.0
        )
        ws.settimeout(timeout_s)

        try:
            opcode, data = ws.recv_data()
            if opcode == websocket.ABNF.OPCODE_TEXT:
                text_str = data.decode("utf-8", errors="replace")
                return WsReceiveResponse(text=text_str)
            elif opcode == websocket.ABNF.OPCODE_BINARY:
                return WsReceiveResponse(binary=data)
            elif opcode == websocket.ABNF.OPCODE_CLOSE:
                self.ws_close(WsCloseRequest(connection_id=conn_id))
                return WsReceiveResponse()
            elif opcode == websocket.ABNF.OPCODE_PING:
                ws.pong(data)
                return self.ws_receive(req)
        except (websocket.WebSocketTimeoutException, socket.timeout):
            return WsReceiveResponse()
        except (websocket.WebSocketConnectionClosedException, ConnectionError):
            return WsReceiveResponse()
        except Exception:
            return WsReceiveResponse()

        return WsReceiveResponse()

    def ws_close(self, req: WsCloseRequest) -> WsCloseResponse:
        conn_id = req.connection_id
        ws = self.connections.pop(conn_id, None)
        if ws:
            try:
                code = req.code if req.HasField("code") else 1000
                reason = req.reason.encode("utf-8") if req.HasField("reason") else b""
                ws.close(status=code, reason=reason)
            except Exception:
                pass
        return WsCloseResponse(success=True)

    def close_all(self):
        for ws in list(self.connections.values()):
            try:
                ws.close()
            except Exception:
                pass
        self.connections.clear()


import subprocess
import select
from core.types.protos.extensions_pb2 import (
    BinaryPermission,
    SpawnProcessRequest,
    SpawnProcessResponse,
    WriteProcessStdinRequest,
    WriteProcessStdinResponse,
    ReadProcessStdoutRequest,
    ReadProcessStdoutResponse,
    KillProcessRequest,
    KillProcessResponse,
    GetProcessStatusRequest,
    GetProcessStatusResponse,
)

SUPPORTED_HASH_ALGORITHMS = {
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
    "md5": hashlib.md5,
}


class RealProcessManager:
    def __init__(self, allowed_binaries: list[BinaryPermission] | None = None):
        self.processes: dict[int, subprocess.Popen] = {}
        self.mapped_paths: dict[str, str] = {}
        self.allowed_binaries: list[BinaryPermission] = allowed_binaries or []
        self.next_id = 1

    def resolve_path(self, path: str) -> str:
        for guest_path, host_path in self.mapped_paths.items():
            if path == guest_path:
                return host_path
            if path.startswith(guest_path.rstrip('/') + '/'):
                rel = path[len(guest_path.rstrip('/') + '/'):]
                return os.path.join(host_path, rel)
        return path

    def is_in_allowed(self, resolved_bin: str) -> bool:
        if not self.mapped_paths:
            return False
        real_target = os.path.realpath(resolved_bin)
        for base in set(self.mapped_paths.values()):
            real_base = os.path.realpath(base)
            try:
                if os.path.commonpath([real_base, real_target]) == real_base:
                    return True
            except ValueError:
                continue
        return False

    def verify_binary_hash(self, resolved_bin: str, requested_path: str) -> None:
        if not self.is_in_allowed(resolved_bin):
            raise PermissionError(
                f"Binary '{requested_path}' ({resolved_bin}) is not inside any allowed_paths"
            )

        real_bin = os.path.realpath(resolved_bin)
        matching_perm = None
        for perm in self.allowed_binaries:
            if perm.name == requested_path:
                matching_perm = perm
                break
            resolved_perm = self.resolve_path(perm.name)
            if os.path.realpath(resolved_perm) == real_bin or real_bin.endswith(perm.name):
                matching_perm = perm
                break

        if matching_perm is None:
            raise PermissionError(
                f"Binary '{requested_path}' is not permitted by manifest permissions.binaries"
            )

        if not matching_perm.hashes:
            raise PermissionError(
                f"Binary '{requested_path}' has no hashes declared in manifest permissions.binaries"
            )

        with open(real_bin, "rb") as f:
            file_bytes = f.read()

        for algo, expected_hash in matching_perm.hashes.items():
            hasher_fn = SUPPORTED_HASH_ALGORITHMS.get(algo.lower())
            if hasher_fn is None:
                raise PermissionError(
                    f"Unsupported hash algorithm '{algo}' for binary '{requested_path}'"
                )
            computed = hasher_fn(file_bytes).hexdigest()
            if computed.lower() != expected_hash.lower():
                raise PermissionError(
                    f"Binary hash mismatch for '{requested_path}' ({algo}): "
                    f"expected {expected_hash}, got {computed}"
                )

    def spawn_process(self, req: SpawnProcessRequest) -> SpawnProcessResponse:
        resolved_bin = self.resolve_path(req.path)
        self.verify_binary_hash(resolved_bin, req.path)
        if os.path.isfile(resolved_bin):
            try:
                os.chmod(resolved_bin, 0o755)
            except Exception:
                pass
        resolved_args = [self.resolve_path(arg) for arg in req.args]
        cmd = [resolved_bin] + resolved_args
        env = dict(os.environ)
        env.update(req.env)
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )
        proc_id = self.next_id
        self.next_id += 1
        self.processes[proc_id] = proc
        return SpawnProcessResponse(
            process_id=proc_id,
            pid=proc.pid,
        )

    def write_process_stdin(self, req: WriteProcessStdinRequest) -> WriteProcessStdinResponse:
        proc = self.processes.get(req.process_id)
        if not proc or not proc.stdin or proc.poll() is not None:
            return WriteProcessStdinResponse(bytes_written=0)
        try:
            proc.stdin.write(req.data)
            proc.stdin.flush()
            return WriteProcessStdinResponse(bytes_written=len(req.data))
        except Exception:
            return WriteProcessStdinResponse(bytes_written=0)

    def read_process_stdout(self, req: ReadProcessStdoutRequest) -> ReadProcessStdoutResponse:
        proc = self.processes.get(req.process_id)
        if not proc or not proc.stdout:
            return ReadProcessStdoutResponse(data=b)
        max_bytes = req.max_bytes if req.HasField(max_bytes) and req.max_bytes > 0 else 4096
        try:
            rlist, _, _ = select.select([proc.stdout], [], [], 0.1)
            if rlist:
                data = os.read(proc.stdout.fileno(), max_bytes)
                return ReadProcessStdoutResponse(data=data)
        except Exception:
            pass
        return ReadProcessStdoutResponse(data=b)

    def kill_process(self, req: KillProcessRequest) -> KillProcessResponse:
        proc = self.processes.get(req.process_id)
        if not proc:
            return KillProcessResponse(success=False)
        try:
            proc.terminate()
            proc.wait(timeout=1.0)
            return KillProcessResponse(success=True)
        except Exception:
            try:
                proc.kill()
                return KillProcessResponse(success=True)
            except Exception:
                return KillProcessResponse(success=False)

    def get_process_status(self, req: GetProcessStatusRequest) -> GetProcessStatusResponse:
        proc = self.processes.get(req.process_id)
        if not proc:
            return GetProcessStatusResponse(is_running=False)
        exit_code = proc.poll()
        is_running = exit_code is None
        return GetProcessStatusResponse(
            is_running=is_running,
            exit_code=exit_code if exit_code is not None else None,
        )

    def close_all(self):
        for proc in list(self.processes.values()):
            try:
                proc.terminate()
                proc.wait(timeout=0.5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self.processes.clear()
