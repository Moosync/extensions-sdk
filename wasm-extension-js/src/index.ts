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

export * from "./api";
export * from "./protos/extensions_pb";
export * from "./protos/songs_pb";
export * from "./protos/ui_pb";
export * from "./protos/themes_pb";
export * from "@bufbuild/protobuf";

import { callListener } from "./api";
import {
  ExtensionCommand,
  ExtensionCommandResponse,
} from "./protos/extensions_pb";
import { Message } from "@bufbuild/protobuf";

function handle(
  command: ExtensionCommand,
): ExtensionCommandResponse | undefined {
  if (!command.event.case) return undefined;

  const caseStr = command.event.case;
  const payload = command.event.value;

  if (payload) {
    try {
      // payload.constructor is the Message Class (e.g. RequestedPlaylistsRequest)
      // This matches the key used in api.on()
      const result = callListener(caseStr as any, payload);

      // Construct response based on responseField
      if (result !== undefined) {
        const response = new ExtensionCommandResponse({
          response: {
            case: caseStr as any,
            value: result
          }
        });
        return response;
      } else {
        const response = new ExtensionCommandResponse({
          response: {
            case: caseStr as any,
            value: {}
          }
        });
        return response;
      }

    } catch (e) {
      console.error("Error handling command", e);
    }
  }
  return undefined;
}

export function handle_extension_command(): number {
  const bytes = Host.inputBytes();
  if (bytes.byteLength === 0) {
    return 0;
  }

  try {
    const command = ExtensionCommand.fromBinary(new Uint8Array(bytes));
    const response = handle(command);
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

