export interface PlatformInfo {
  os: string;
  arch: string;
}

let platformInfo: PlatformInfo | null = null;

export function getPlatform(): PlatformInfo {
  if (!platformInfo) {
    let os = "unknown";
    let arch = "unknown";
    try {
      if (typeof Config !== "undefined" && Config.get) {
        const hostOs = Config.get("os");
        if (hostOs) {
          os = hostOs;
        }
        const hostArch = Config.get("arch");
        if (hostArch) {
          arch = hostArch;
        }
      }
    } catch {}
    platformInfo = { os, arch };
  }
  return platformInfo;
}

const proc: any = (globalThis as any).process ?? {};
if (!proc.platform) {
  Object.defineProperty(proc, "platform", {
    get() {
      return getPlatform().os;
    },
    configurable: true,
  });
}
if (!proc.arch) {
  Object.defineProperty(proc, "arch", {
    get() {
      return getPlatform().arch;
    },
    configurable: true,
  });
}
(globalThis as any).process = proc;
