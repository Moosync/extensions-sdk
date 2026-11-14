package api

import (
	"errors"

	extensions "github.com/moosync/moosync/types/extensions"
	"google.golang.org/protobuf/proto"
)

// GetCache retrieves and unmarshals a protobuf message from the host cache by key.
func GetCache[T proto.Message](key string) (T, error) {
	var zero T
	resp, err := HostGetCache(&extensions.GetCacheRequest{Key: key})
	if err != nil {
		return zero, err
	}
	if len(resp.Data) == 0 {
		return zero, nil
	}
	msg := zero.ProtoReflect().New().Interface().(T)
	if err := proto.Unmarshal(resp.Data, msg); err != nil {
		return zero, err
	}
	return msg, nil
}

// SetCache marshals and stores a protobuf message in the host cache by key with an optional TTL in seconds.
func SetCache[T proto.Message](key string, data T, ttlSeconds *uint64) error {
	bytes, err := proto.Marshal(data)
	if err != nil {
		return err
	}
	resp, err := HostSetCache(&extensions.SetCacheRequest{
		Key:        key,
		Data:       bytes,
		TtlSeconds: ttlSeconds,
	})
	if err != nil {
		return err
	}
	if !resp.Success {
		return errors.New("failed to set cache")
	}
	return nil
}
