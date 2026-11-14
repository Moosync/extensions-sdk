import { Duration } from "@bufbuild/protobuf";
import { MainCommand, MainCommandResponse } from "./protos/extensions_pb.js";

export async function sendMainCommand(
  command: MainCommand,
): Promise<MainCommandResponse> {
  const fns = Host.getFunctions() as any;
  const { send_main_command } = fns;
  const bytes = command.toBinary();

  // @ts-ignore
  const mem = Memory.fromBuffer(bytes.buffer);
  // @ts-ignore
  const resOffset = send_main_command(mem.offset);
  // @ts-ignore
  const resMem = Memory.find(resOffset);
  const resBytes = new Uint8Array(resMem.readBytes());
  return MainCommandResponse.fromBinary(resBytes);
}

/**
 * Converts milliseconds to a protobuf Duration.
 */
export function durationToProto(ms: number): Duration {
  return new Duration({
    seconds: BigInt(Math.floor(ms / 1000)),
    nanos: (ms % 1000) * 1000000,
  });
}

/**
 * Converts a protobuf Duration to milliseconds.
 */
export function protoToDuration(duration: Duration): number {
  return Number(duration.seconds) * 1000 + Math.floor(duration.nanos / 1000000);
}

