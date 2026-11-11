import {
  SpawnProcessRequest,
  WriteProcessStdinRequest,
  ReadProcessStdoutRequest,
  KillProcessRequest,
  GetProcessStatusRequest,
  NotifyPlayerEventRequest,
  PlayerEvent,
} from "./protos/extensions_pb.js";
import {
  spawnProcess as generatedSpawnProcess,
  writeProcessStdin as generatedWriteProcessStdin,
  readProcessStdout as generatedReadProcessStdout,
  killProcess as generatedKillProcess,
  getProcessStatus as generatedGetProcessStatus,
  notifyPlayerEvent as generatedNotifyPlayerEvent,
} from "./generated_api.js";

export class ChildProcess {
  constructor(
    readonly id: number,
    readonly pid: number,
  ) {}

  async writeStdin(data: Uint8Array | string): Promise<number> {
    const bytes = typeof data === "string" ? new TextEncoder().encode(data) : data;
    const res = await generatedWriteProcessStdin(
      new WriteProcessStdinRequest({
        processId: BigInt(this.id),
        data: bytes,
      }),
    );
    return Number(res?.bytesWritten ?? 0n);
  }

  async readStdout(maxBytes?: number): Promise<Uint8Array> {
    const res = await generatedReadProcessStdout(
      new ReadProcessStdoutRequest({
        processId: BigInt(this.id),
        maxBytes: maxBytes !== undefined ? BigInt(maxBytes) : undefined,
      }),
    );
    return res?.data ?? new Uint8Array(0);
  }

  async readStdoutString(maxBytes?: number): Promise<string> {
    const bytes = await this.readStdout(maxBytes);
    return new TextDecoder().decode(bytes);
  }

  async kill(): Promise<boolean> {
    const res = await generatedKillProcess(
      new KillProcessRequest({
        processId: BigInt(this.id),
      }),
    );
    return res?.success ?? false;
  }

  async getStatus(): Promise<{ isRunning: boolean; exitCode?: number }> {
    const res = await generatedGetProcessStatus(
      new GetProcessStatusRequest({
        processId: BigInt(this.id),
      }),
    );
    return {
      isRunning: res?.isRunning ?? false,
      exitCode: res?.exitCode,
    };
  }
}

export async function spawnProcess(options: {
  path: string;
  args?: string[];
  env?: Record<string, string>;
}): Promise<ChildProcess> {
  const res = await generatedSpawnProcess(
    new SpawnProcessRequest({
      path: options.path,
      args: options.args ?? [],
      env: options.env ?? {},
    }),
  );
  if (!res) {
    throw new Error("Failed to spawn process: no response from host");
  }
  return new ChildProcess(Number(res.processId), res.pid);
}

export async function notifyPlayerEvent(event: PlayerEvent): Promise<void> {
  await generatedNotifyPlayerEvent(new NotifyPlayerEventRequest({ event }));
}
