import {
  WsConnectRequest,
  WsSendRequest,
  WsCloseRequest,
  WsEventRequest,
} from "./protos/extensions_pb.js";
import {
  wsConnect as generatedWsConnect,
  wsSend as generatedWsSend,
  wsClose as generatedWsClose,
} from "./generated_api.js";

export interface WebSocketMessage {
  isBinary: boolean;
  text?: string;
  binary?: Uint8Array;
}

export interface WsCloseEvent {
  code?: number;
  reason?: string;
  error?: string;
}

interface ConnectionHandlers {
  onMessage?: (message: WebSocketMessage) => void | Promise<void>;
  onClose?: (event: WsCloseEvent) => void | Promise<void>;
}

/**
 * Manages active WebSocket connection callbacks for host-pushed events.
 */
export class WebSocketManager {
  private static handlers = new Map<bigint, ConnectionHandlers>();

  private static setHandler<K extends keyof ConnectionHandlers>(
    connectionId: bigint,
    key: K,
    callback: ConnectionHandlers[K],
  ): void {
    const entry = this.handlers.get(connectionId) ?? {};
    entry[key] = callback;
    this.handlers.set(connectionId, entry);
  }

  static onMessage(
    connectionId: bigint,
    callback: (message: WebSocketMessage) => void | Promise<void>,
  ): void {
    this.setHandler(connectionId, "onMessage", callback);
  }

  static onClose(
    connectionId: bigint,
    callback: (event: WsCloseEvent) => void | Promise<void>,
  ): void {
    this.setHandler(connectionId, "onClose", callback);
  }

  static remove(connectionId: bigint): void {
    this.handlers.delete(connectionId);
  }

  static async handleEvent(req: WsEventRequest): Promise<void> {
    const connectionId = req.connectionId;
    const entry = this.handlers.get(connectionId);
    if (!req.event.case) return;

    if (req.event.case === "text") {
      if (entry?.onMessage) {
        await entry.onMessage({ isBinary: false, text: req.event.value });
      }
      return;
    }

    if (req.event.case === "binary") {
      if (entry?.onMessage) {
        await entry.onMessage({ isBinary: true, binary: req.event.value });
      }
      return;
    }

    if (req.event.case === "closed") {
      this.handlers.delete(connectionId);
      if (entry?.onClose) {
        const closed = req.event.value;
        await entry.onClose({
          code: closed.code,
          reason: closed.reason,
          error: closed.error,
        });
      }
    }
  }
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
   * Registers a callback invoked when a text or binary frame is received.
   */
  onMessage(
    callback: (message: WebSocketMessage) => void | Promise<void>,
  ): void {
    WebSocketManager.onMessage(this.connectionId, callback);
  }

  /**
   * Registers a callback invoked when the WebSocket connection closes or errors.
   */
  onClose(callback: (event: WsCloseEvent) => void | Promise<void>): void {
    WebSocketManager.onClose(this.connectionId, callback);
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
   * Closes the WebSocket connection with an optional close code and reason.
   */
  async close(code?: number, reason?: string): Promise<void> {
    WebSocketManager.remove(this.connectionId);
    await generatedWsClose(
      new WsCloseRequest({
        connectionId: this.connectionId,
        code: code ?? undefined,
        reason: reason ?? undefined,
      }),
    );
  }
}
