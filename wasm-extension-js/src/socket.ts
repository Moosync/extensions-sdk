import {
  OpenClientFdRequest,
  WriteSockRequest,
  ReadSockRequest,
} from "./protos/extensions_pb.js";
import {
  hostOpenClientFd as generatedOpenClientFd,
  hostWriteSock as generatedWriteSock,
  hostReadSock as generatedReadSock,
} from "./generated_api.js";

/**
 * Client for reading and writing to a host-mediated local socket / IPC file descriptor.
 */
export class SocketClient {
  constructor(readonly sockId: number) {}

  /**
   * Opens a client socket connection at the specified path via the host.
   */
  static async connect(path: string): Promise<SocketClient> {
    const res = await generatedOpenClientFd(
      new OpenClientFdRequest({
        path,
      }),
    );
    const sockId = Number(res?.sockId ?? -1n);
    if (!res || sockId < 0) {
      throw new Error(`Failed to connect to socket: ${path}`);
    }
    return new SocketClient(sockId);
  }

  /**
   * Writes a byte buffer or UTF-8 string to the socket.
   */
  async write(data: Uint8Array | string): Promise<number> {
    const bytes =
      typeof data === "string" ? new TextEncoder().encode(data) : data;
    const res = await generatedWriteSock(
      new WriteSockRequest({
        sockId: BigInt(this.sockId),
        buf: bytes,
      }),
    );
    return Number(res?.bytesWritten ?? 0n);
  }

  /**
   * Reads up to `readLen` bytes from the socket.
   */
  async read(readLen: number): Promise<Uint8Array> {
    const res = await generatedReadSock(
      new ReadSockRequest({
        sockId: BigInt(this.sockId),
        readLen: BigInt(readLen),
      }),
    );
    return res?.data ?? new Uint8Array(0);
  }
}

/**
 * Opens a client socket at the specified path and returns a {@link SocketClient} handle.
 */
export async function openSock(path: string): Promise<SocketClient> {
  return SocketClient.connect(path);
}
