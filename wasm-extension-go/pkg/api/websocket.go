package api

import (
	"sync"

	extensions "github.com/moosync/moosync/types/extensions"
)

type WebSocketMessage struct {
	IsBinary bool
	Text     string
	Binary   []byte
}

type WsCloseEvent struct {
	Code   *uint32
	Reason *string
	Error  *string
}

type wsConnectionHandlers struct {
	onMessage func(WebSocketMessage)
	onClose   func(WsCloseEvent)
}

type WebSocketManager struct {
	mu       sync.Mutex
	handlers map[uint64]*wsConnectionHandlers
}

var defaultWebSocketManager = &WebSocketManager{
	handlers: make(map[uint64]*wsConnectionHandlers),
}

func getWebSocketManager() *WebSocketManager {
	return defaultWebSocketManager
}

func (m *WebSocketManager) updateHandler(connectionID uint64, fn func(*wsConnectionHandlers)) {
	m.mu.Lock()
	defer m.mu.Unlock()
	entry, ok := m.handlers[connectionID]
	if !ok {
		entry = &wsConnectionHandlers{}
		m.handlers[connectionID] = entry
	}
	fn(entry)
}

func (m *WebSocketManager) OnMessage(connectionID uint64, cb func(WebSocketMessage)) {
	m.updateHandler(connectionID, func(entry *wsConnectionHandlers) {
		entry.onMessage = cb
	})
}

func (m *WebSocketManager) OnClose(connectionID uint64, cb func(WsCloseEvent)) {
	m.updateHandler(connectionID, func(entry *wsConnectionHandlers) {
		entry.onClose = cb
	})
}

func (m *WebSocketManager) Remove(connectionID uint64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.handlers, connectionID)
}

func (m *WebSocketManager) getMessageHandler(connectionID uint64) func(WebSocketMessage) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if entry, ok := m.handlers[connectionID]; ok {
		return entry.onMessage
	}
	return nil
}

func (m *WebSocketManager) handleEvent(req *extensions.WsEventRequest) {
	if req == nil {
		return
	}
	switch ev := req.Event.(type) {
	case *extensions.WsEventRequest_Text:
		if cb := m.getMessageHandler(req.ConnectionId); cb != nil {
			cb(WebSocketMessage{IsBinary: false, Text: ev.Text})
		}
	case *extensions.WsEventRequest_Binary:
		if cb := m.getMessageHandler(req.ConnectionId); cb != nil {
			cb(WebSocketMessage{IsBinary: true, Binary: ev.Binary})
		}
	case *extensions.WsEventRequest_Closed:
		m.mu.Lock()
		var cb func(WsCloseEvent)
		if entry, ok := m.handlers[req.ConnectionId]; ok {
			cb = entry.onClose
			delete(m.handlers, req.ConnectionId)
		}
		m.mu.Unlock()
		if cb != nil && ev.Closed != nil {
			cb(WsCloseEvent{
				Code:   ev.Closed.Code,
				Reason: ev.Closed.Reason,
				Error:  ev.Closed.Error,
			})
		}
	}
}

type WebSocketClient struct {
	ConnectionID uint64
}

func ConnectWebSocket(url string) (*WebSocketClient, error) {
	resp, err := WsConnect(&extensions.WsConnectRequest{
		Url: url,
	})
	if err != nil {
		return nil, err
	}
	return &WebSocketClient{
		ConnectionID: resp.ConnectionId,
	}, nil
}

func (c *WebSocketClient) OnMessage(cb func(WebSocketMessage)) {
	defaultWebSocketManager.OnMessage(c.ConnectionID, cb)
}

func (c *WebSocketClient) OnClose(cb func(WsCloseEvent)) {
	defaultWebSocketManager.OnClose(c.ConnectionID, cb)
}

func (c *WebSocketClient) SendText(text string) error {
	_, err := WsSend(&extensions.WsSendRequest{
		ConnectionId: c.ConnectionID,
		Payload: &extensions.WsSendRequest_Text{
			Text: text,
		},
	})
	return err
}

func (c *WebSocketClient) SendBinary(data []byte) error {
	_, err := WsSend(&extensions.WsSendRequest{
		ConnectionId: c.ConnectionID,
		Payload: &extensions.WsSendRequest_Binary{
			Binary: data,
		},
	})
	return err
}

func (c *WebSocketClient) Close(code *uint32, reason *string) error {
	defaultWebSocketManager.Remove(c.ConnectionID)
	_, err := WsClose(&extensions.WsCloseRequest{
		ConnectionId: c.ConnectionID,
		Code:         code,
		Reason:       reason,
	})
	return err
}
