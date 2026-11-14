import {
  WsConnectRequest,
  WsSendRequest,
  WsReceiveRequest,
  WsCloseRequest,
} from "./protos/extensions_pb.js";
import {
  wsConnect as generatedWsConnect,
  wsSend as generatedWsSend,
  wsReceive as generatedWsReceive,
  wsClose as generatedWsClose,
} from "./generated_api.js";

export interface WebSocketMessage {
  isBinary: boolean;
  text?: string;
  binary?: Uint8Array;
}

/**
 * Client for managing a host-mediated WebSocket connection.
 */
export class WebSocketClient {
  constructor(readonly connectionId: bigint) {}

  /**
   * Opens a new WebSocket connection to the specified URL via the host.
   */
  static async connect(url: string): Promise<WebSocketClient> {
    const res = await generatedWsConnect(new WsConnectRequest({ url }));
    if (!res) {
      throw new Error("Failed to connect websocket: no response from host");
    }
    return new WebSocketClient(res.connectionId);
  }

  /**
   * Sends a UTF-8 text frame over the WebSocket connection.
   */
  async sendText(text: string): Promise<void> {
    await generatedWsSend(
      new WsSendRequest({
        connectionId: this.connectionId,
        payload: { case: "text", value: text },
      }),
    );
  }

  /**
   * Sends a binary frame over the WebSocket connection.
   */
  async sendBinary(data: Uint8Array): Promise<void> {
    await generatedWsSend(
      new WsSendRequest({
        connectionId: this.connectionId,
        payload: { case: "binary", value: data },
      }),
    );
  }

  /**
   * Waits for and receives the next message frame from the WebSocket connection.
   */
  async receive(timeoutMs?: number): Promise<WebSocketMessage | undefined> {
    const res = await generatedWsReceive(
      new WsReceiveRequest({
        connectionId: this.connectionId,
        timeoutMs: timeoutMs != null ? BigInt(timeoutMs) : undefined,
      }),
    );
    if (!res || !res.payload.case) {
      return undefined;
    }
    if (res.payload.case === "text") {
      return {
        isBinary: false,
        text: res.payload.value,
      };
    }
    if (res.payload.case === "binary") {
      return {
        isBinary: true,
        binary: res.payload.value,
      };
    }
    return undefined;
  }

  /**
   * Closes the WebSocket connection with an optional close code and reason.
   */
  async close(code?: number, reason?: string): Promise<void> {
    await generatedWsClose(
      new WsCloseRequest({
        connectionId: this.connectionId,
        code: code ?? undefined,
        reason: reason ?? undefined,
      }),
    );
  }
}
