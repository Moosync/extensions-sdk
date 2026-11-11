import { Duration } from "@bufbuild/protobuf";

export function durationToProto(ms: number): Duration {
  return new Duration({
    seconds: BigInt(Math.floor(ms / 1000)),
    nanos: (ms % 1000) * 1000000,
  });
}
