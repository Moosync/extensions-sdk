package api

import (
	extensions "github.com/moosync/moosync/types/extensions"
)

type WebSocketMessage struct {
	IsBinary bool
	Text     string
	Binary   []byte
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

func (c *WebSocketClient) Receive(timeoutMs *uint64) (*WebSocketMessage, error) {
	resp, err := WsReceive(&extensions.WsReceiveRequest{
		ConnectionId: c.ConnectionID,
		TimeoutMs:    timeoutMs,
	})
	if err != nil {
		return nil, err
	}
	if resp.Payload == nil {
		return nil, nil
	}
	switch p := resp.Payload.(type) {
	case *extensions.WsReceiveResponse_Text:
		return &WebSocketMessage{
			IsBinary: false,
			Text:     p.Text,
		}, nil
	case *extensions.WsReceiveResponse_Binary:
		return &WebSocketMessage{
			IsBinary: true,
			Binary:   p.Binary,
		}, nil
	default:
		return nil, nil
	}
}

func (c *WebSocketClient) Close(code *uint32, reason *string) error {
	_, err := WsClose(&extensions.WsCloseRequest{
		ConnectionId: c.ConnectionID,
		Code:         code,
		Reason:       reason,
	})
	return err
}
