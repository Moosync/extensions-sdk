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

export class WebSocketClient {
  constructor(readonly connectionId: bigint) {}

  static async connect(url: string): Promise<WebSocketClient> {
    const res = await generatedWsConnect(new WsConnectRequest({ url }));
    if (!res) {
      throw new Error("Failed to connect websocket: no response from host");
    }
    return new WebSocketClient(res.connectionId);
  }

  async sendText(text: string): Promise<void> {
    await generatedWsSend(
      new WsSendRequest({
        connectionId: this.connectionId,
        payload: { case: "text", value: text },
      }),
    );
  }

  async sendBinary(data: Uint8Array): Promise<void> {
    await generatedWsSend(
      new WsSendRequest({
        connectionId: this.connectionId,
        payload: { case: "binary", value: data },
      }),
    );
  }

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
