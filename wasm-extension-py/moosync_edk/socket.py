from moosync_edk.generated_api import open_clientfd, read_sock, write_sock


class SocketClient:
    def __init__(self, sock_id: int):
        self.sock_id = sock_id

    @classmethod
    def connect(cls, path: str) -> "SocketClient":
        sock_id = open_clientfd(path)
        if sock_id < 0:
            raise RuntimeError(f"Failed to connect to socket: {path}")
        return cls(sock_id)

    def write(self, data: bytes | str) -> int:
        if isinstance(data, str):
            data = data.encode("utf-8")
        return write_sock(self.sock_id, data)

    def read(self, read_len: int) -> bytes:
        return read_sock(self.sock_id, read_len)
