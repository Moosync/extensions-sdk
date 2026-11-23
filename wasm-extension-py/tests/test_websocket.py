import unittest
from core.types.protos import extensions_pb2
from moosync_edk.websocket import WebSocketManager


class TestWebSocketManager(unittest.TestCase):
    def test_handle_event_text_binary_and_closed(self):
        conn_id = 77
        received = []
        closed = []

        WebSocketManager.on_message(conn_id, received.append)
        WebSocketManager.on_close(conn_id, closed.append)

        WebSocketManager._handle_event(
            extensions_pb2.WsEventRequest(connection_id=conn_id, text="hi")
        )
        WebSocketManager._handle_event(
            extensions_pb2.WsEventRequest(connection_id=conn_id, binary=b"\x01\x02")
        )
        WebSocketManager._handle_event(
            extensions_pb2.WsEventRequest(
                connection_id=conn_id,
                closed=extensions_pb2.WsClosed(code=1001, reason="going away"),
            )
        )
        WebSocketManager._handle_event(
            extensions_pb2.WsEventRequest(connection_id=conn_id, text="after-close")
        )

        self.assertEqual(len(received), 2)
        self.assertFalse(received[0].is_binary)
        self.assertEqual(received[0].text, "hi")
        self.assertTrue(received[1].is_binary)
        self.assertEqual(received[1].binary, b"\x01\x02")
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0].code, 1001)
        self.assertEqual(closed[0].reason, "going away")
        self.assertIsNone(closed[0].error)


if __name__ == "__main__":
    unittest.main()
