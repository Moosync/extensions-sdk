from typing import Optional, Type, TypeVar
from google.protobuf.message import Message
from core.types.protos import extensions_pb2
from moosync_edk.generated_api import get_cache as host_get_cache, set_cache as host_set_cache

T = TypeVar("T", bound=Message)

def get_cache(key: str, message_type: Type[T]) -> Optional[T]:
    """Retrieves and deserializes a protobuf message from the host cache by key."""
    req = extensions_pb2.GetCacheRequest(key=key)
    resp = host_get_cache(req)
    if not resp or not resp.data:
        return None
    msg = message_type()
    msg.ParseFromString(resp.data)
    return msg

def set_cache(key: str, data: T, ttl_seconds: Optional[int] = None) -> bool:
    """Serializes and stores a protobuf message in the host cache by key with an optional TTL in seconds."""
    req = extensions_pb2.SetCacheRequest(
        key=key,
        data=data.SerializeToString(),
        ttl_seconds=ttl_seconds,
    )
    resp = host_set_cache(req)
    return resp.success if resp else False
