import {
  openClientFd as generatedOpenClientFd,
  writeSock as generatedWriteSock,
  readSock as generatedReadSock,
} from "./generated_api.js";

/**
 * Client for reading and writing to a host-mediated local socket / IPC file descriptor.
 */
export class SocketClient {
  constructor(readonly sockId: number) {}

  /**
   * Opens a client socket connection at the specified path via the host.
   */
  static connect(path: string): SocketClient {
    const sockId = generatedOpenClientFd(path);
    if (sockId < 0) {
      throw new Error(`Failed to connect to socket: ${path}`);
    }
    return new SocketClient(sockId);
  }

  /**
   * Writes a byte buffer or UTF-8 string to the socket.
   */
  write(data: Uint8Array | string): number {
    const bytes = typeof data === "string" ? new TextEncoder().encode(data) : data;
    return generatedWriteSock(this.sockId, bytes);
  }

  /**
   * Reads up to `readLen` bytes from the socket.
   */
  read(readLen: number): Uint8Array {
    return generatedReadSock(this.sockId, readLen);
  }
}
