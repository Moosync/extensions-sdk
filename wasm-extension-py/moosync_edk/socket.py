from core.types.protos import extensions_pb2
from moosync_edk.generated_api import (
    open_client_fd as host_open_client_fd,
    read_sock as host_read_sock,
    write_sock as host_write_sock,
)


class SocketClient:
    def __init__(self, sock_id: int):
        self.sock_id = sock_id

    @classmethod
    def connect(cls, path: str) -> "SocketClient":
        resp = host_open_client_fd(extensions_pb2.OpenClientFdRequest(path=path))
        if not resp or resp.sock_id < 0:
            raise RuntimeError(f"Failed to connect to socket: {path}")
        return cls(resp.sock_id)

    def write(self, data: bytes | str) -> int:
        if isinstance(data, str):
            data = data.encode("utf-8")
        resp = host_write_sock(
            extensions_pb2.WriteSockRequest(
                sock_id=self.sock_id,
                buf=data,
            )
        )
        return resp.bytes_written if resp else 0

    def read(self, read_len: int) -> bytes:
        resp = host_read_sock(
            extensions_pb2.ReadSockRequest(
                sock_id=self.sock_id,
                read_len=read_len,
            )
        )
        return resp.data if resp else b""


def open_sock(path: str) -> SocketClient:
    return SocketClient.connect(path)
