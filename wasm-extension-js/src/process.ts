import {
  SpawnProcessRequest,
  WriteProcessStdinRequest,
  ReadProcessStdoutRequest,
  KillProcessRequest,
  GetProcessStatusRequest,
  ProcessEventRequest,
} from "./protos/extensions_pb.js";
import {
  hostSpawnProcess as generatedSpawnProcess,
  writeProcessStdin as generatedWriteProcessStdin,
  readProcessStdout as generatedReadProcessStdout,
  killProcess as generatedKillProcess,
  getProcessStatus as generatedGetProcessStatus,
} from "./generated_api.js";

interface ProcessHandlers {
  onStdout?: (data: Uint8Array) => void | Promise<void>;
  onStderr?: (data: Uint8Array) => void | Promise<void>;
  onExit?: (code: number) => void | Promise<void>;
}

/**
 * Handle to a spawned child process managed by the host.
 */
export class ChildProcess {
  private static handlers = new Map<bigint, ProcessHandlers>();

  constructor(
    readonly id: number,
    readonly pid: number,
  ) {}

  static async handleEvent(req: ProcessEventRequest): Promise<void> {
    const processId = req.processId;
    const entry = this.handlers.get(processId);
    if (!req.event.case) return;

    if (req.event.case === "output") {
      const output = req.event.value;
      if (output.stdout.length > 0 && entry?.onStdout) {
        await entry.onStdout(output.stdout);
      }
      if (output.stderr.length > 0 && entry?.onStderr) {
        await entry.onStderr(output.stderr);
      }
      return;
    }

    if (req.event.case === "exited") {
      this.handlers.delete(processId);
      if (entry?.onExit) {
        await entry.onExit(req.event.value);
      }
    }
  }

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

  private setHandler<K extends keyof ProcessHandlers>(
    key: K,
    callback: ProcessHandlers[K],
  ): void {
    const processId = BigInt(this.id);
    const entry = ChildProcess.handlers.get(processId) ?? {};
    entry[key] = callback;
    ChildProcess.handlers.set(processId, entry);
  }

  /**
   * Registers a callback for stdout chunks emitted by the child process.
   */
  onStdout(callback: (data: Uint8Array) => void | Promise<void>): void {
    this.setHandler("onStdout", callback);
  }

  /**
   * Registers a callback for stderr chunks emitted by the child process.
   */
  onStderr(callback: (data: Uint8Array) => void | Promise<void>): void {
    this.setHandler("onStderr", callback);
  }

  /**
   * Registers a callback invoked when the child process exits.
   */
  onExit(callback: (code: number) => void | Promise<void>): void {
    this.setHandler("onExit", callback);
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
