import {
  SpawnProcessRequest,
  WriteProcessStdinRequest,
  ReadProcessStdoutRequest,
  KillProcessRequest,
  GetProcessStatusRequest,
} from "./protos/extensions_pb.js";
import {
  hostSpawnProcess as generatedSpawnProcess,
  writeProcessStdin as generatedWriteProcessStdin,
  readProcessStdout as generatedReadProcessStdout,
  killProcess as generatedKillProcess,
  getProcessStatus as generatedGetProcessStatus,
} from "./generated_api.js";

/**
 * Handle to a spawned child process managed by the host.
 */
export class ChildProcess {
  constructor(
    readonly id: number,
    readonly pid: number,
  ) {}

  /**
   * Writes bytes or a UTF-8 string to the child process's standard input stream.
   */
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

  /**
   * Reads raw bytes from the child process's standard output stream.
   */
  async readStdout(maxBytes?: number): Promise<Uint8Array> {
    const res = await generatedReadProcessStdout(
      new ReadProcessStdoutRequest({
        processId: BigInt(this.id),
        maxBytes: maxBytes !== undefined ? BigInt(maxBytes) : undefined,
      }),
    );
    return res?.data ?? new Uint8Array(0);
  }

  /**
   * Reads output from the child process's standard output stream decoded as a UTF-8 string.
   */
  async readStdoutString(maxBytes?: number): Promise<string> {
    const bytes = await this.readStdout(maxBytes);
    return new TextDecoder().decode(bytes);
  }

  /**
   * Terminates the running child process on the host.
   */
  async kill(): Promise<boolean> {
    const res = await generatedKillProcess(
      new KillProcessRequest({
        processId: BigInt(this.id),
      }),
    );
    return res?.success ?? false;
  }

  /**
   * Queries whether the child process is still running and its exit code if exited.
   */
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

/**
 * Spawns a permitted external binary on the host and returns a {@link ChildProcess} handle.
 */
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
