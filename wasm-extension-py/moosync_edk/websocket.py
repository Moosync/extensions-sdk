from collections.abc import Callable
from core.types.protos import extensions_pb2
from moosync_edk.generated_api import ws_connect, ws_send, ws_close


class WebSocketMessage:
    def __init__(self, text: str | None = None, binary: bytes | None = None):
        self.text = text
        self.binary = binary

    @property
    def is_binary(self) -> bool:
        return self.binary is not None


class WsCloseEvent:
    def __init__(
        self,
        code: int | None = None,
        reason: str | None = None,
        error: str | None = None,
    ):
        self.code = code
        self.reason = reason
        self.error = error


class _ConnectionHandlers:
    def __init__(self) -> None:
        self.on_message: Callable[[WebSocketMessage], None] | None = None
        self.on_close: Callable[[WsCloseEvent], None] | None = None


class WebSocketManager:
    _handlers: dict[int, _ConnectionHandlers] = {}

    @classmethod
    def on_message(
        cls, connection_id: int, callback: Callable[[WebSocketMessage], None]
    ) -> None:
        entry = cls._handlers.setdefault(connection_id, _ConnectionHandlers())
        entry.on_message = callback

    @classmethod
    def on_close(
        cls, connection_id: int, callback: Callable[[WsCloseEvent], None]
    ) -> None:
        entry = cls._handlers.setdefault(connection_id, _ConnectionHandlers())
        entry.on_close = callback

    @classmethod
    def remove(cls, connection_id: int) -> None:
        cls._handlers.pop(connection_id, None)

    @classmethod
    def _handle_event(cls, req: extensions_pb2.WsEventRequest) -> None:
        connection_id = req.connection_id
        field = req.WhichOneof("event")
        if field == "text":
            entry = cls._handlers.get(connection_id)
            if entry and entry.on_message:
                entry.on_message(WebSocketMessage(text=req.text))
        elif field == "binary":
            entry = cls._handlers.get(connection_id)
            if entry and entry.on_message:
                entry.on_message(WebSocketMessage(binary=req.binary))
        elif field == "closed":
            entry = cls._handlers.pop(connection_id, None)
            if entry and entry.on_close:
                closed = req.closed
                entry.on_close(
                    WsCloseEvent(
                        code=closed.code if closed.HasField("code") else None,
                        reason=closed.reason if closed.HasField("reason") else None,
                        error=closed.error if closed.HasField("error") else None,
                    )
                )


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

    def on_message(self, callback: Callable[[WebSocketMessage], None]) -> None:
        WebSocketManager.on_message(self.connection_id, callback)

    def on_close(self, callback: Callable[[WsCloseEvent], None]) -> None:
        WebSocketManager.on_close(self.connection_id, callback)

    def send_text(self, text: str) -> None:
        req = extensions_pb2.WsSendRequest(connection_id=self.connection_id, text=text)
        ws_send(req)

    def send_binary(self, data: bytes) -> None:
        req = extensions_pb2.WsSendRequest(connection_id=self.connection_id, binary=data)
        ws_send(req)

    def close(self, code: int | None = None, reason: str | None = None) -> None:
        WebSocketManager.remove(self.connection_id)
        req = extensions_pb2.WsCloseRequest(
            connection_id=self.connection_id, code=code, reason=reason
        )
        ws_close(req)
