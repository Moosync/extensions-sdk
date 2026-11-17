package api

import (
	"errors"

	extensions "github.com/moosync/moosync/types/extensions"
)

type SocketClient struct {
	SockID int64
}

func ConnectSocket(path string) (*SocketClient, error) {
	resp, err := HostOpenClientFd(&extensions.OpenClientFdRequest{
		Path: path,
	})
	if err != nil {
		return nil, err
	}
	if resp.SockId < 0 {
		return nil, errors.New("failed to connect to socket")
	}
	return &SocketClient{
		SockID: resp.SockId,
	}, nil
}

func OpenSock(path string) (*SocketClient, error) {
	return ConnectSocket(path)
}

func (c *SocketClient) Write(data []byte) (int64, error) {
	resp, err := HostWriteSock(&extensions.WriteSockRequest{
		SockId: c.SockID,
		Buf:    data,
	})
	if err != nil {
		return 0, err
	}
	return resp.BytesWritten, nil
}

func (c *SocketClient) Read(readLen uint64) ([]byte, error) {
	resp, err := HostReadSock(&extensions.ReadSockRequest{
		SockId:  c.SockID,
		ReadLen: readLen,
	})
	if err != nil {
		return nil, err
	}
	return resp.Data, nil
}
