import { Message, MessageType } from "@bufbuild/protobuf";
import { hostGetCache, hostSetCache } from "./generated_api";
import { GetCacheRequest, SetCacheRequest } from "./protos/extensions_pb";

/**
 * Retrieves and deserializes a protobuf message from the host cache by key.
 */
export async function getCache<T extends Message<T>>(
  key: string,
  type: MessageType<T>,
): Promise<T | undefined> {
  const res = await hostGetCache(new GetCacheRequest({ key }));
  if (!res || !res.data || res.data.length === 0) {
    return undefined;
  }
  return type.fromBinary(res.data);
}

/**
 * Serializes and stores a protobuf message in the host cache by key with an optional TTL in seconds.
 */
export async function setCache<T extends Message<T>>(
  key: string,
  data: T,
  ttlSeconds?: number,
): Promise<void> {
  const bytes = data.toBinary();
  await hostSetCache(
    new SetCacheRequest({
      key,
      data: bytes,
      ttlSeconds: ttlSeconds !== undefined ? BigInt(ttlSeconds) : undefined,
    }),
  );
}
