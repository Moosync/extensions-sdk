import {
  HttpRequest,
  HttpResponse,
  BatchHttpRequest,
  BatchHttpResponse,
} from "./protos/extensions_pb.js";

export interface BatchFetchRequest {
  url: string;
  method?: string;
  headers?: Record<string, string>;
  body?: Uint8Array | string;
  timeoutMs?: number;
}

export interface BatchFetchOptions {
  headers?: Record<string, string>;
  timeoutMs?: number;
}

export class BatchFetchResponse {
  readonly status: number;
  readonly statusText: string;
  readonly headers: Record<string, string>;
  readonly body: Uint8Array;

  constructor(resp: HttpResponse) {
    this.status = resp.statusCode;
    this.statusText = resp.statusText;
    this.headers = resp.headers;
    this.body = resp.body;
  }

  get ok(): boolean {
    return this.status >= 200 && this.status < 300;
  }

  async text(): Promise<string> {
    return new TextDecoder().decode(this.body);
  }

  async json<T = any>(): Promise<T> {
    const txt = await this.text();
    return JSON.parse(txt);
  }

  async arrayBuffer(): Promise<ArrayBufferLike> {
    return this.body.buffer.slice(
      this.body.byteOffset,
      this.body.byteOffset + this.body.byteLength,
    );
  }
}

/**
 * Executes multiple HTTP requests in a single host batch call.
 */
export function batchFetch(
  requests: (string | BatchFetchRequest)[],
  options?: BatchFetchOptions,
): Promise<BatchFetchResponse[]> {
  const fns = Host.getFunctions() as any;
  const { batch_http_request } = fns;
  if (!batch_http_request) {
    throw new Error("batch_http_request host function is not available");
  }

  const protoRequests: HttpRequest[] = requests.map((req) => {
    if (typeof req === "string") {
      return new HttpRequest({
        url: req,
        method: "GET",
        headers: options?.headers ?? {},
        timeoutMs: options?.timeoutMs ? BigInt(options.timeoutMs) : undefined,
      });
    }
    const bodyBytes =
      req.body instanceof Uint8Array
        ? req.body
        : typeof req.body === "string"
          ? new TextEncoder().encode(req.body)
          : undefined;

    return new HttpRequest({
      url: req.url,
      method: (req.method ?? "GET").toUpperCase(),
      headers: {
        ...(options?.headers ?? {}),
        ...(req.headers ?? {}),
      },
      body: bodyBytes,
      timeoutMs: req.timeoutMs
        ? BigInt(req.timeoutMs)
        : options?.timeoutMs
          ? BigInt(options.timeoutMs)
          : undefined,
    });
  });

  const batchReq = new BatchHttpRequest({
    requests: protoRequests,
  });

  const bytes = batchReq.toBinary();
  // @ts-ignore
  const mem = Memory.fromBuffer(bytes.buffer);
  const res_offset = batch_http_request(mem.offset);

  // @ts-ignore
  const res_mem = Memory.find(res_offset);
  const res_bytes_buffer = res_mem.readBytes();
  const res_bytes = new Uint8Array(res_bytes_buffer);

  const batchResp = BatchHttpResponse.fromBinary(res_bytes);
  if (batchResp.error) {
    throw new Error(batchResp.error);
  }

  const responses: BatchFetchResponse[] = [];
  for (let i = 0; i < batchResp.responses.length; i++) {
    const item = batchResp.responses[i];
    if (item.result.case === "response" && item.result.value) {
      responses.push(new BatchFetchResponse(item.result.value));
    } else if (item.result.case === "error") {
      throw new Error(`Request #${i} failed: ${item.result.value}`);
    } else {
      throw new Error(`Request #${i} returned empty HTTP result`);
    }
  }

  return Promise.resolve(responses);
}

function resolveUrl(input: string | URL | Request): string {
  if (typeof input === "string") {
    return input;
  }
  if (input instanceof URL) {
    return input.toString();
  }
  if (typeof (input as any)?.url === "string") {
    return (input as any).url;
  }
  return String(input);
}

function resolveMethod(
  input: string | URL | Request,
  init?: RequestInit,
): string {
  if (init?.method) {
    return init.method.toUpperCase();
  }
  if (typeof (input as any)?.method === "string") {
    return (input as any).method.toUpperCase();
  }
  return "GET";
}

function appendHeaders(target: Record<string, string>, source: any): void {
  if (!source) {
    return;
  }
  if (typeof source.forEach === "function") {
    source.forEach((val: string, key: string) => {
      target[key] = val;
    });
    return;
  }
  if (typeof source[Symbol.iterator] === "function") {
    for (const item of source) {
      if (Array.isArray(item) && item.length >= 2) {
        target[item[0]] = item[1];
      }
    }
    return;
  }
  if (typeof source === "object") {
    for (const [key, value] of Object.entries(source)) {
      if (typeof value === "string") {
        target[key] = value;
      }
    }
  }
}

function resolveHeaders(
  input: string | URL | Request,
  init?: RequestInit,
): Record<string, string> {
  const headers: Record<string, string> = {};
  if (typeof (input as any)?.headers === "object") {
    appendHeaders(headers, (input as any).headers);
  }
  if (init?.headers) {
    appendHeaders(headers, init.headers);
  }
  return headers;
}

function resolveBody(
  input: string | URL | Request,
  init?: RequestInit,
): Uint8Array | string | undefined {
  const bodySource =
    init?.body !== undefined
      ? init.body
      : typeof (input as any)?.body !== "undefined"
        ? (input as any).body
        : undefined;

  if (bodySource === undefined || bodySource === null) {
    return undefined;
  }
  if (typeof bodySource === "string") {
    return bodySource;
  }
  if (bodySource instanceof Uint8Array) {
    return bodySource;
  }
  if (bodySource instanceof ArrayBuffer) {
    return new Uint8Array(bodySource);
  }
  if (ArrayBuffer.isView(bodySource)) {
    return new Uint8Array(
      bodySource.buffer,
      bodySource.byteOffset,
      bodySource.byteLength,
    );
  }
  return String(bodySource);
}

function resolveTimeout(init?: RequestInit): number | undefined {
  if (init && typeof (init as any).timeoutMs === "number") {
    return (init as any).timeoutMs;
  }
  return undefined;
}

function toBatchFetchRequest(
  input: string | URL | Request,
  init?: RequestInit,
): BatchFetchRequest {
  return {
    url: resolveUrl(input),
    method: resolveMethod(input, init),
    headers: resolveHeaders(input, init),
    body: resolveBody(input, init),
    timeoutMs: resolveTimeout(init),
  };
}

function toResponse(resp: BatchFetchResponse): Response {
  const textBody = new TextDecoder("utf-8").decode(resp.body);
  const r = new Response(textBody, {
    status: resp.status,
    statusText: resp.statusText,
    headers: resp.headers,
  });

  return r;
}

/**
 * Performs an HTTP request via the Moosync host network runner using a standard Fetch-compatible API.
 */
export async function fetch(
  input: string | URL | Request,
  init?: RequestInit,
): Promise<Response> {
  const batchReq = toBatchFetchRequest(input, init);
  const responses = await batchFetch([batchReq]);
  if (!responses || responses.length === 0) {
    throw new Error("Host runner returned empty response");
  }
  return toResponse(responses[0]);
}

if (typeof globalThis !== "undefined") {
  (globalThis as any).fetch = fetch;
}
