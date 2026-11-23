import assert from "node:assert/strict";
import { WebSocketManager } from "../lib/src/websocket.js";
import { handleInternalEvent } from "../lib/src/generated_events.js";
import { ExtensionCommand, WsClosed, WsEventRequest } from "../lib/src/protos/extensions_pb.js";

const connId = 99n;
const received = [];
const closed = [];

WebSocketManager.onMessage(connId, (msg) => received.push(msg));
WebSocketManager.onClose(connId, (ev) => closed.push(ev));

const res1 = await handleInternalEvent(
  new ExtensionCommand({
    event: {
      case: "wsEvent",
      value: new WsEventRequest({
        connectionId: connId,
        event: { case: "text", value: "hello-ts" },
      }),
    },
  }),
);
assert.equal(res1?.response.case, "wsEvent");

const res2 = await handleInternalEvent(
  new ExtensionCommand({
    event: {
      case: "wsEvent",
      value: new WsEventRequest({
        connectionId: connId,
        event: { case: "binary", value: new Uint8Array([4, 5]) },
      }),
    },
  }),
);
assert.equal(res2?.response.case, "wsEvent");

const res3 = await handleInternalEvent(
  new ExtensionCommand({
    event: {
      case: "wsEvent",
      value: new WsEventRequest({
        connectionId: connId,
        event: {
          case: "closed",
          value: new WsClosed({ code: 1000, reason: "normal" }),
        },
      }),
    },
  }),
);
assert.equal(res3?.response.case, "wsEvent");

// Subsequent events after close should not invoke callbacks.
await handleInternalEvent(
  new ExtensionCommand({
    event: {
      case: "wsEvent",
      value: new WsEventRequest({
        connectionId: connId,
        event: { case: "text", value: "ignored" },
      }),
    },
  }),
);

assert.equal(received.length, 2);
assert.equal(received[0].isBinary, false);
assert.equal(received[0].text, "hello-ts");
assert.equal(received[1].isBinary, true);
assert.deepEqual(received[1].binary, new Uint8Array([4, 5]));
assert.equal(closed.length, 1);
assert.equal(closed[0].code, 1000);
assert.equal(closed[0].reason, "normal");
