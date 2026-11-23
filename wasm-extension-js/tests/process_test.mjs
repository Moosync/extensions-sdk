import assert from "node:assert/strict";
import { ChildProcess } from "../lib/src/process.js";
import { handleInternalEvent } from "../lib/src/generated_events.js";
import {
  ExtensionCommand,
  ProcessEventRequest,
  ProcessOutput,
} from "../lib/src/protos/extensions_pb.js";

const proc = new ChildProcess(55, 1234);
const stdoutChunks = [];
const stderrChunks = [];
const exitCodes = [];

proc.onStdout((data) => stdoutChunks.push(Buffer.from(data).toString("utf8")));
proc.onStderr((data) => stderrChunks.push(Buffer.from(data).toString("utf8")));
proc.onExit((code) => exitCodes.push(code));

const res1 = await handleInternalEvent(
  new ExtensionCommand({
    event: {
      case: "processEvent",
      value: new ProcessEventRequest({
        processId: 55n,
        event: {
          case: "output",
          value: new ProcessOutput({
            stdout: new TextEncoder().encode("out-ts"),
            stderr: new TextEncoder().encode("err-ts"),
          }),
        },
      }),
    },
  }),
);
assert.equal(res1?.response.case, "processEvent");

const res2 = await handleInternalEvent(
  new ExtensionCommand({
    event: {
      case: "processEvent",
      value: new ProcessEventRequest({
        processId: 55n,
        event: { case: "exited", value: 9 },
      }),
    },
  }),
);
assert.equal(res2?.response.case, "processEvent");

// Subsequent events after exit should not invoke callbacks.
await handleInternalEvent(
  new ExtensionCommand({
    event: {
      case: "processEvent",
      value: new ProcessEventRequest({
        processId: 55n,
        event: {
          case: "output",
          value: new ProcessOutput({
            stdout: new TextEncoder().encode("ignored"),
          }),
        },
      }),
    },
  }),
);

assert.deepEqual(stdoutChunks, ["out-ts"]);
assert.deepEqual(stderrChunks, ["err-ts"]);
assert.deepEqual(exitCodes, [9]);
