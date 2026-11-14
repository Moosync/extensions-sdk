import base64
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
        self.connections: dict[int, socket.socket] = {}
        self.next_id = 1

    def ws_connect(self, req: WsConnectRequest) -> WsConnectResponse:
        url = req.url
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        if not is_host_allowed(host, self.allowed_hosts):
            raise PermissionError(
                f"Host '{host}' is not allowed by extension manifest permissions.hosts"
            )

        scheme = (parsed.scheme or "ws").lower()
        port = parsed.port or (443 if scheme == "wss" else 80)
        sock = socket.create_connection((host, port), timeout=5.0)
        if scheme == "wss":
            ctx = ssl.create_default_context()
            sock = ctx.wrap_socket(sock, server_hostname=host)

        sec_key = base64.b64encode(os.urandom(16)).decode("ascii")
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"

        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {parsed.netloc}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {sec_key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        sock.sendall(handshake.encode("ascii"))

        resp_data = bytearray()
        while b"\r\n\r\n" not in resp_data:
            chunk = sock.recv(4096)
            if not chunk:
                break
            resp_data.extend(chunk)

        header_text = resp_data.decode("latin1", errors="replace")
        status_line = header_text.split("\r\n")[0]
        if "101" not in status_line:
            sock.close()
            raise ConnectionError(f"WebSocket handshake failed: {status_line}")

        conn_id = self.next_id
        self.next_id += 1
        self.connections[conn_id] = sock
        return WsConnectResponse(connection_id=conn_id)

    def ws_send(self, req: WsSendRequest) -> WsSendResponse:
        conn_id = req.connection_id
        sock = self.connections.get(conn_id)
        if not sock:
            raise ConnectionError(f"WebSocket connection {conn_id} not found")

        field = req.WhichOneof("payload")
        if field == "text":
            data = req.text.encode("utf-8")
            opcode = 1
        elif field == "binary":
            data = req.binary
            opcode = 2
        else:
            data = b""
            opcode = 1

        mask = os.urandom(4)
        masked_data = bytearray(data[i] ^ mask[i % 4] for i in range(len(data)))
        length = len(data)

        header = bytearray([0x80 | opcode])
        if length < 126:
            header.append(0x80 | length)
        elif length <= 0xFFFF:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))

        header.extend(mask)
        header.extend(masked_data)
        sock.sendall(header)
        return WsSendResponse(success=True)

    def ws_receive(self, req: WsReceiveRequest) -> WsReceiveResponse:
        conn_id = req.connection_id
        sock = self.connections.get(conn_id)
        if not sock:
            raise ConnectionError(f"WebSocket connection {conn_id} not found")

        timeout_s = (
            (req.timeout_ms / 1000.0)
            if req.HasField("timeout_ms") and req.timeout_ms > 0
            else 1.0
        )
        sock.settimeout(timeout_s)

        try:
            head = sock.recv(2)
            if not head or len(head) < 2:
                return WsReceiveResponse()
            byte1, byte2 = head[0], head[1]
            opcode = byte1 & 0x0F
            is_masked = bool(byte2 & 0x80)
            payload_len = byte2 & 0x7F

            if payload_len == 126:
                ext_len = sock.recv(2)
                payload_len = struct.unpack("!H", ext_len)[0]
            elif payload_len == 127:
                ext_len = sock.recv(8)
                payload_len = struct.unpack("!Q", ext_len)[0]

            mask_key = sock.recv(4) if is_masked else b""

            payload = bytearray()
            while len(payload) < payload_len:
                chunk = sock.recv(min(payload_len - len(payload), 4096))
                if not chunk:
                    break
                payload.extend(chunk)

            if is_masked and mask_key:
                payload = bytearray(
                    payload[i] ^ mask_key[i % 4] for i in range(len(payload))
                )

            if opcode == 1:
                return WsReceiveResponse(
                    text=payload.decode("utf-8", errors="replace")
                )
            elif opcode == 2:
                return WsReceiveResponse(binary=bytes(payload))
            elif opcode == 8:
                self.ws_close(WsCloseRequest(connection_id=conn_id))
                return WsReceiveResponse()
            elif opcode == 9:
                sock.sendall(bytearray([0x8A, 0x00]))
                return self.ws_receive(req)
        except socket.timeout:
            return WsReceiveResponse()
        except Exception:
            return WsReceiveResponse()

        return WsReceiveResponse()

    def ws_close(self, req: WsCloseRequest) -> WsCloseResponse:
        conn_id = req.connection_id
        sock = self.connections.pop(conn_id, None)
        if sock:
            try:
                sock.sendall(bytearray([0x88, 0x00]))
                sock.close()
            except Exception:
                pass
        return WsCloseResponse(success=True)

    def close_all(self):
        for s in list(self.connections.values()):
            try:
                s.close()
            except Exception:
                pass
        self.connections.clear()

