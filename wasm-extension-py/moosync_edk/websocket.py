from typing import Optional
from core.types.protos import extensions_pb2
from moosync_edk.generated_api import ws_connect, ws_send, ws_receive, ws_close

class WebSocketMessage:
    def __init__(self, text: Optional[str] = None, binary: Optional[bytes] = None):
        self.text = text
        self.binary = binary

    @property
    def is_binary(self) -> bool:
        return self.binary is not None

class WebSocketClient:
    def __init__(self, connection_id: int):
        self.connection_id = connection_id

    @classmethod
    def connect(cls, url: str) -> "WebSocketClient":
        req = extensions_pb2.WsConnectRequest(url=url)
        resp = ws_connect(req)
        if not resp:
            raise RuntimeError("Failed to connect websocket: no response from host")
        return cls(resp.connection_id)

    def send_text(self, text: str) -> None:
        req = extensions_pb2.WsSendRequest(connection_id=self.connection_id, text=text)
        ws_send(req)

    def send_binary(self, data: bytes) -> None:
        req = extensions_pb2.WsSendRequest(connection_id=self.connection_id, binary=data)
        ws_send(req)

    def receive(self, timeout_ms: Optional[int] = None) -> Optional[WebSocketMessage]:
        req = extensions_pb2.WsReceiveRequest(connection_id=self.connection_id, timeout_ms=timeout_ms)
        resp = ws_receive(req)
        if not resp:
            return None
        field = resp.WhichOneof("payload")
        if field == "text":
            return WebSocketMessage(text=resp.text)
        elif field == "binary":
            return WebSocketMessage(binary=resp.binary)
        return None

    def close(self, code: Optional[int] = None, reason: Optional[str] = None) -> None:
        req = extensions_pb2.WsCloseRequest(connection_id=self.connection_id, code=code, reason=reason)
        ws_close(req)
