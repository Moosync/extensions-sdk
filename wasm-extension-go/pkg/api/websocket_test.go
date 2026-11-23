package api

import (
	"testing"

	extensions "github.com/moosync/moosync/types/extensions"
)

func TestWebSocketManagerHandleEvent(t *testing.T) {
	mgr := getWebSocketManager()
	const connID uint64 = 42

	var received []WebSocketMessage
	var closedEvents []WsCloseEvent

	mgr.OnMessage(connID, func(msg WebSocketMessage) {
		received = append(received, msg)
	})
	mgr.OnClose(connID, func(ev WsCloseEvent) {
		closedEvents = append(closedEvents, ev)
	})

	mgr.handleEvent(&extensions.WsEventRequest{
		ConnectionId: connID,
		Event:        &extensions.WsEventRequest_Text{Text: "hello"},
	})
	mgr.handleEvent(&extensions.WsEventRequest{
		ConnectionId: connID,
		Event:        &extensions.WsEventRequest_Binary{Binary: []byte{1, 2, 3}},
	})

	code := uint32(1000)
	reason := "done"
	mgr.handleEvent(&extensions.WsEventRequest{
		ConnectionId: connID,
		Event: &extensions.WsEventRequest_Closed{
			Closed: &extensions.WsClosed{
				Code:   &code,
				Reason: &reason,
			},
		},
	})

	// Subsequent events after close should not be delivered.
	mgr.handleEvent(&extensions.WsEventRequest{
		ConnectionId: connID,
		Event:        &extensions.WsEventRequest_Text{Text: "ignored"},
	})

	if len(received) != 2 {
		t.Fatalf("expected 2 messages, got %d", len(received))
	}
	if received[0].IsBinary || received[0].Text != "hello" {
		t.Fatalf("unexpected first message: %+v", received[0])
	}
	if !received[1].IsBinary || len(received[1].Binary) != 3 {
		t.Fatalf("unexpected second message: %+v", received[1])
	}
	if len(closedEvents) != 1 || *closedEvents[0].Code != 1000 || *closedEvents[0].Reason != "done" {
		t.Fatalf("unexpected closed events: %+v", closedEvents)
	}
}
