/// <reference types="@types/node/web-globals/fetch.d.ts" />

export class Request implements globalThis.Request {
  readonly url: string;
  readonly method: string;
  readonly headers: Headers;
  readonly body: any;
  readonly mode: globalThis.Request["mode"];
  readonly credentials: globalThis.Request["credentials"];
  readonly cache: globalThis.Request["cache"];
  readonly redirect: globalThis.Request["redirect"];
  readonly referrer: string;
  readonly referrerPolicy: globalThis.Request["referrerPolicy"];
  readonly keepalive: boolean;
  readonly duplex: globalThis.Request["duplex"];
  readonly integrity: string;
  readonly signal: AbortSignal;
  readonly destination: globalThis.Request["destination"];
  private _bodyUsed: boolean = false;

  constructor(input: string | URL | Request, init: RequestInit = {}) {
    let url = "";
    let method = "GET";
    let headers: any = null;
    let body: any = null;

    if (typeof input === "string") {
      url = input;
    } else if (typeof URL !== "undefined" && input instanceof URL) {
      url = input.toString();
    } else if (input && typeof input === "object") {
      url = (input as any).url || "";
      method = (input as any).method || "GET";
      headers = (input as any).headers;
      body = (input as any).body;
    }

    if (init.method) {
      method = init.method;
    }
    this.method = method.toUpperCase();

    // Headers
    const HeadersCtor =
      typeof Headers !== "undefined" ? Headers : (globalThis as any).Headers;
    if (HeadersCtor) {
      this.headers = new HeadersCtor(
        init.headers !== undefined ? init.headers : headers,
      );
    } else {
      this.headers = (init.headers || headers || {}) as any;
    }

    // Body
    if (init.body !== undefined) {
      body = init.body;
    }

    if (
      ["GET", "HEAD"].includes(this.method) &&
      body !== null &&
      body !== undefined
    ) {
      throw new TypeError("Request with GET/HEAD method cannot have body.");
    }
    this.body = body ?? null;

    this.url = url;

    // Standard properties
    this.mode = init.mode ?? ("cors" as globalThis.Request["mode"]);
    this.credentials =
      init.credentials ?? ("same-origin" as globalThis.Request["credentials"]);
    this.cache = init.cache ?? ("default" as globalThis.Request["cache"]);
    this.redirect =
      init.redirect ?? ("follow" as globalThis.Request["redirect"]);
    this.destination =
      (init as any).destination ?? ("" as globalThis.Request["destination"]);
    this.referrer = init.referrer ?? "about:client";
    this.referrerPolicy =
      (init as any).referrerPolicy ??
      ("" as globalThis.Request["referrerPolicy"]);
    this.keepalive = init.keepalive ?? false;
    this.duplex =
      (init as any).duplex ?? ("half" as globalThis.Request["duplex"]);
    this.integrity = init.integrity ?? "";
    this.signal = init.signal ?? new AbortController().signal;
  }

  get bodyUsed(): boolean {
    return this._bodyUsed;
  }

  clone(): globalThis.Request {
    if (this._bodyUsed) {
      throw new TypeError("Cannot clone a used request body.");
    }
    return new Request(this.url, {
      method: this.method,
      headers: this.headers,
      body: this.body,
      mode: this.mode,
      credentials: this.credentials,
      cache: this.cache,
      redirect: this.redirect,
      referrer: this.referrer,
      referrerPolicy: this.referrerPolicy,
      keepalive: this.keepalive,
      integrity: this.integrity,
      signal: this.signal,
    } as RequestInit);
  }

  async text(): Promise<string> {
    if (this._bodyUsed) throw new TypeError("Body has already been consumed.");
    this._bodyUsed = true;

    if (this.body === null || this.body === undefined) return "";
    if (typeof this.body === "string") return this.body;
    if (this.body instanceof ArrayBuffer) {
      return new TextDecoder().decode(this.body);
    }
    if (ArrayBuffer.isView(this.body)) {
      const u8 = new Uint8Array(
        this.body.buffer as ArrayBuffer,
        this.body.byteOffset,
        this.body.byteLength,
      );
      return new TextDecoder().decode(u8);
    }
    return String(this.body);
  }

  async json(): Promise<any> {
    const raw = await this.text();
    return JSON.parse(raw);
  }

  async arrayBuffer(): Promise<ArrayBuffer> {
    if (this._bodyUsed) throw new TypeError("Body has already been consumed.");
    this._bodyUsed = true;

    if (this.body === null || this.body === undefined)
      return new ArrayBuffer(0);
    if (this.body instanceof ArrayBuffer) return this.body;

    if (ArrayBuffer.isView(this.body)) {
      const u8 = new Uint8Array(
        this.body.buffer as ArrayBuffer,
        this.body.byteOffset,
        this.body.byteLength,
      );
      return u8.slice().buffer as ArrayBuffer;
    }

    const str = typeof this.body === "string" ? this.body : String(this.body);
    const encoded = new TextEncoder().encode(str);
    return encoded.buffer as ArrayBuffer;
  }

  // Required by modern WHATWG Body interface
  async bytes(): Promise<Uint8Array> {
    const buffer = await this.arrayBuffer();
    return new Uint8Array(buffer);
  }

  async blob(): Promise<any> {
    throw new Error("Blob is not supported in this environment");
  }

  async formData(): Promise<any> {
    throw new Error("FormData is not supported in this environment");
  }
}

if (typeof globalThis !== "undefined") {
  globalThis.Request = Request;
}
