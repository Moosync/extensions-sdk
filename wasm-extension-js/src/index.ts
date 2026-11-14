// Moosync
// Copyright (C) 2024, 2025  Moosync <support@moosync.app>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

import "fast-text-encoding";
import "./request-ponyfills";
import "./abortcontroller-ponyfills";
import "./platform";

export * from "./generated_api";
export * from "./generated_events";
export type { Extension } from "./generated_events";
export { ChildProcess, spawnProcess } from "./process";
export { SocketClient } from "./socket";
export { WebSocketClient } from "./websocket";
export type { WebSocketMessage } from "./websocket";
export { getPlatform } from "./platform";
export type { PlatformInfo } from "./platform";
export * from "./lrc";
export * from "./http";
export { getCache, setCache } from "./cache";
export * from "./utils";
export * from "./protos/extension_service_pb";
export * from "./protos/extensions_pb";
export * from "./protos/preferences_pb";
export * from "./protos/songs_pb";
export * from "./protos/ui_pb";
export * from "./protos/themes_pb";
export * from "@bufbuild/protobuf";

import * as generatedApi from "./generated_api";
import type { Extension, ExtensionEventMap } from "./generated_events";
import { fetch, batchFetch } from "./http";
import { getCache, setCache } from "./cache";
import { spawnProcess } from "./process";
import {
  ExtensionCommand,
  ExtensionCommandResponse,
} from "./protos/extensions_pb";

let registeredExtension: Extension | undefined;

/**
 * Registers an object or class instance implementing the {@link Extension} interface to handle incoming host events.
 */
export function registerExtension(ext: Extension): void {
  registeredExtension = ext;
}

/**
 * Returns the currently registered extension instance, if any.
 */
export function getRegisteredExtension(): Extension | undefined {
  return registeredExtension;
}

const listeners: Map<keyof ExtensionEventMap, Function> = new Map();

/**
 * Registers a callback handler for a specific incoming extension event from the host.
 */
export function on<K extends keyof ExtensionEventMap>(
  event: K,
  handler: (
    req: ExtensionEventMap[K]["req"]
  ) => Promise<ExtensionEventMap[K]["resp"] | void> | ExtensionEventMap[K]["resp"] | void
): void {
  listeners.set(event, handler);
}

export function callListener(event: string, payload: any): any {
  if (registeredExtension && typeof (registeredExtension as any)[event] === "function") {
    return (registeredExtension as any)[event](payload);
  }
  const handler = listeners.get(event as keyof ExtensionEventMap);
  if (handler) {
    return handler(payload);
  }
  return undefined;
}

export type ExtensionApi = typeof generatedApi & {
  getCache: typeof getCache;
  setCache: typeof setCache;
  spawnProcess: typeof spawnProcess;
  on: typeof on;
  fetch: typeof fetch;
  batchFetch: typeof batchFetch;
};

/**
 * Returns the Moosync Extension API client containing all host command methods, caching helpers, HTTP fetch utilities, and event registration.
 */
export function getApi(): ExtensionApi {
  return {
    ...generatedApi,
    getCache,
    setCache,
    spawnProcess,
    on,
    fetch,
    batchFetch,
  };
}

export async function handle(
  command: ExtensionCommand,
): Promise<ExtensionCommandResponse | undefined> {
  if (!command.event.case) return undefined;

  const caseStr = command.event.case;
  const payload = command.event.value;

  if (payload) {
    const result = await Promise.resolve(callListener(caseStr as any, payload));

    // Construct response based on responseField
    if (result !== undefined) {
      const response = new ExtensionCommandResponse({
        response: {
          case: caseStr as any,
          value: result,
        },
      });
      return response;
    } else {
      const response = new ExtensionCommandResponse({
        response: {
          case: caseStr as any,
          value: {},
        },
      });
      return response;
    }
  }
  return undefined;
}

export async function handle_extension_command(): Promise<number> {
  const bytes = Host.inputBytes();
  if (bytes.byteLength === 0) {
    return 0;
  }

  try {
    const command = ExtensionCommand.fromBinary(new Uint8Array(bytes));
    const response = await handle(command);
    if (response) {
      const binary = response.toBinary();
      const copy = new Uint8Array(binary);
      Host.outputBytes(copy.buffer);
    }
    return 0;
  } catch (e) {
    console.error("Failed to handle extension command", e);
    return 1;
  }
}
