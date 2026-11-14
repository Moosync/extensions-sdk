package api

import "errors"

type SocketClient struct {
	SockID int64
}

func ConnectSocket(path string) (*SocketClient, error) {
	sockID := OpenClientFd(path)
	if sockID < 0 {
		return nil, errors.New("failed to connect to socket")
	}
	return &SocketClient{
		SockID: sockID,
	}, nil
}

func (c *SocketClient) Write(data []byte) (int64, error) {
	return WriteSock(c.SockID, data), nil
}

func (c *SocketClient) Read(readLen uint64) ([]byte, error) {
	return ReadSock(c.SockID, readLen), nil
}
