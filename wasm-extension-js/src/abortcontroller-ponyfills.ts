// Define barebones dummy signal & controller if missing
if (typeof globalThis !== "undefined") {
  (globalThis as any).AbortSignal = class AbortSignal {
    readonly aborted: boolean = false;
    readonly reason: any = undefined;
    addEventListener() {}
    removeEventListener() {}
    dispatchEvent() {
      return true;
    }
  };

  (globalThis as any).AbortController = class AbortController {
    readonly signal = new (globalThis as any).AbortSignal();
    abort() {
      console.error("AbortController is not supported in this environment");
    }
  };
}
