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
import { Message } from "@bufbuild/protobuf";
import {
  ExtensionAccountDetail,
  ExtensionProviderScope,
  PlayerState,
  PreferenceArgs,
  RequestedPlaylistsResponse,
  RequestedPlaylistSongsResponse,
  RequestedRecommendationsResponse,
  RequestedSearchResultResponse,
  PlaybackDetailsRequestedResponse,
  CustomRequest,
  CustomRequestResponse,
  RequestedPlaylistFromUrlResponse,
  RequestedSongFromIdResponse,
  RequestedSongFromUrlResponse,
  ContextMenuReturnType,
  MainCommand,
  ExtensionCommand,
  ExtensionCommandResponse,
  UpdateAccountsRequest,

  RequestedPlaylistsRequest,
  RequestedPlaylistSongsRequest,
  RequestedPlaylistFromUrlRequest,
  RequestedSearchResultRequest,
  RequestedRecommendationsRequest,
  RequestedSongFromUrlRequest,
  RequestedArtistSongsRequest,
  RequestedAlbumSongsRequest,
  RequestedSongFromIdRequest,
  RequestedSongContextMenuRequest,
  RequestedPlaylistContextMenuRequest,
  ContextMenuActionRequest,
  RequestedLyricsRequest,
  SongQueueChangedRequest,
  SeekedRequest,
  VolumeChangedRequest,
  PlayerStateChangedRequest,
  SongChangedRequest,
  PreferenceChangedRequest,
  PlaybackDetailsRequestedRequest,
  SongAddedRequest,
  SongRemovedRequest,
  PlaylistAddedRequest,
  PlaylistRemovedRequest,
  GetAccountsRequest,
  GetAccountsResponse,
  OauthCallbackRequest,
  PerformAccountLoginRequest,
  ScrobbleRequest,
  GetProviderScopesRequest,
  GetProviderScopesResponse,
  PerformAccountLoginResponse,
  OauthCallbackResponse,
  ScrobbleResponse,
  PlaylistRemovedResponse,
  PlaylistAddedResponse,
  SongRemovedResponse,
  SongAddedResponse,
  PreferenceChangedResponse,
  SeekedResponse,
  SongChangedResponse,
  PlayerStateChangedResponse,
  SongQueueChangedResponse,
  VolumeChangedResponse,
  ContextMenuActionResponse,

  RegisterOauthRequest,
  MainCommandResponse,
  RegisterUserPreferenceRequest,
  UnregisterUserPreferenceRequest,
  OpenExternalUrlRequest,
  AddPlaylistRequest,
  AddSongsRequest,
  AddToPlaylistRequest,
  GetPreferenceRequest,
  GetSecureRequest,
  GetSongRequest,
  GetCurrentSongRequest,
  GetPlayerStateRequest,
  GetVolumeRequest,
  GetTimeRequest,
  GetQueueRequest,
  PreferenceData,
} from "./protos/extensions_pb";
import {
  Album,
  Artist,
  Song,
  Playlist,
  Genre,
  GetSongOptions,
} from "./protos/songs_pb";
import { PreferenceUiData } from "./protos/ui_pb";

export {
  Song,
  Album,
  Artist,
  Playlist,
  Genre,
  PreferenceUiData,
  ExtensionAccountDetail,
  PreferenceArgs,
};



// Define ExtensionContext locally if not in protos
export class ExtensionContext { }

export interface AccountLoginArgs {
  packageName: string;
  accountId: string;
  loginStatus: boolean;
}

type ExtensionEventOneOf = ExtensionCommand["event"];
export type ExtensionEventCase = Exclude<ExtensionEventOneOf["case"], undefined>;
export type EventPayload<K extends ExtensionEventCase> = Extract<ExtensionEventOneOf, { case: K }>["value"];

type ExtensionResponseOneOf = ExtensionCommandResponse["response"];
export type ResponsePayload<K extends ExtensionEventCase> = Extract<ExtensionResponseOneOf, { case: K }>["value"];

export interface ExtensionAPI {
  on<K extends ExtensionEventCase>(
    event: K,
    cb: (req: EventPayload<K>) => ResponsePayload<K> | Promise<ResponsePayload<K>> | void
  ): void;


  getSong(options: GetSongOptions): Song[];
  getCurrentSong(): Song | undefined;
  getPlayerState(): PlayerState;
  getVolume(): number;
  getTime(): number;
  getQueue(): Song[];
  getContext(): ExtensionContext;

  updateAccounts(accountId?: string): void;
  registerOauth(url: string): boolean;
  registerUserPreferences(preferences: PreferenceUiData[]): void;
  unregisterUserPreferences(preferenceIds: string[]): void;
  openExternalUrl(url: string): void;
  addPlaylist(playlist: Playlist): void;
  addSongs(songs: Song[]): void;
  addToPlaylist(req: AddToPlaylistRequest): void;
  getPreference(data: PreferenceData): PreferenceData;
  getSecure(data: PreferenceData): PreferenceData;
}

var LISTENERS: Record<string, Function>;

// Helper for sending main command
function sendMainCommand(cmd: MainCommand): MainCommandResponse {
  const fns = Host.getFunctions() as any;
  const { send_main_command } = fns;

  const bytes = cmd.toBinary();

  // @ts-ignore
  const mem = Memory.fromBuffer(bytes.buffer);

  // @ts-ignore
  const res_offset = send_main_command(mem.offset);

  // @ts-ignore
  const res_mem = Memory.find(res_offset);
  const res_bytes_buffer = res_mem.readBytes();
  const res_bytes = new Uint8Array(res_bytes_buffer);

  return MainCommandResponse.fromBinary(res_bytes);
}

class Api implements ExtensionAPI {
  on<K extends ExtensionEventCase>(event: K, cb: (req: EventPayload<K>) => ResponsePayload<K> | Promise<ResponsePayload<K>> | void): void {
    if (!LISTENERS) {
      LISTENERS = {};
    }
    LISTENERS[event] = cb;
  }

  getContext(): ExtensionContext {
    return new ExtensionContext();
  }

  updateAccounts(accountId?: string): void {
    const cmd = new MainCommand({
      command: {
        case: "updateAccounts",
        value: new UpdateAccountsRequest({ account: accountId })
      }
    });
    sendMainCommand(cmd);
  }

  registerOauth(url: string): boolean {
    const cmd = new MainCommand({
      command: {
        case: "registerOauth",
        value: new RegisterOauthRequest({ url })
      }
    });
    const res = sendMainCommand(cmd);
    if (res.response.case === "registerOauth") {
      return res.response.value.success;
    }
    return false;
  }

  registerUserPreferences(preferences: PreferenceUiData[]): void {
    const cmd = new MainCommand({
      command: {
        case: "registerUserPreference",
        value: new RegisterUserPreferenceRequest({ prefs: preferences })
      }
    });
    sendMainCommand(cmd);
  }

  unregisterUserPreferences(preferenceIds: string[]): void {
    const cmd = new MainCommand({
      command: {
        case: "unregisterUserPreference",
        value: new UnregisterUserPreferenceRequest({ keys: preferenceIds })
      }
    });
    sendMainCommand(cmd);
  }

  openExternalUrl(url: string): void {
    const cmd = new MainCommand({
      command: {
        case: "openExternalUrl",
        value: new OpenExternalUrlRequest({ url })
      }
    });
    sendMainCommand(cmd);
  }

  addPlaylist(playlist: Playlist): void {
    const cmd = new MainCommand({
      command: {
        case: "addPlaylist",
        value: new AddPlaylistRequest({ playlist })
      }
    });
    sendMainCommand(cmd);
  }

  addSongs(songs: Song[]): void {
    const cmd = new MainCommand({
      command: {
        case: "addSongs",
        value: new AddSongsRequest({ songs })
      }
    });
    sendMainCommand(cmd);
  }

  addToPlaylist(req: AddToPlaylistRequest): void {
    const cmd = new MainCommand({
      command: {
        case: "addToPlaylist",
        value: req
      }
    });
    sendMainCommand(cmd);
  }

  getPreference(data: PreferenceData): PreferenceData {
    const cmd = new MainCommand({
      command: {
        case: "getPreference",
        value: new GetPreferenceRequest({ data })
      }
    });
    const res = sendMainCommand(cmd);
    if (res.response.case === "getPreference") {
      return res.response.value.data ?? new PreferenceData();
    }
    return new PreferenceData();
  }

  getSecure(data: PreferenceData): PreferenceData {
    const cmd = new MainCommand({
      command: {
        case: "getSecure",
        value: new GetSecureRequest({ data })
      }
    });
    const res = sendMainCommand(cmd);
    if (res.response.case === "getSecure") {
      return res.response.value.data ?? new PreferenceData();
    }
    return new PreferenceData();
  }

  getSong(options: GetSongOptions): Song[] {
    const cmd = new MainCommand({
      command: {
        case: "getSong",
        value: new GetSongRequest({ options })
      }
    });
    const res = sendMainCommand(cmd);
    if (res.response.case === "getSong") {
      return res.response.value.songs;
    }
    return [];
  }

  getCurrentSong(): Song | undefined {
    const cmd = new MainCommand({
      command: {
        case: "getCurrentSong",
        value: new GetCurrentSongRequest()
      }
    });
    const res = sendMainCommand(cmd);
    if (res.response.case === "getCurrentSong") {
      return res.response.value.song;
    }
    return undefined;
  }

  getPlayerState(): PlayerState {
    const cmd = new MainCommand({
      command: {
        case: "getPlayerState",
        value: new GetPlayerStateRequest()
      }
    });
    const res = sendMainCommand(cmd);
    if (res.response.case === "getPlayerState") {
      return res.response.value.state;
    }
    return PlayerState.PAUSED;
  }

  getVolume(): number {
    const cmd = new MainCommand({
      command: {
        case: "getVolume",
        value: new GetVolumeRequest()
      }
    });
    const res = sendMainCommand(cmd);
    if (res.response.case === "getVolume") {
      return res.response.value.volume;
    }
    return 0;
  }

  getTime(): number {
    const cmd = new MainCommand({
      command: {
        case: "getTime",
        value: new GetTimeRequest()
      }
    });
    const res = sendMainCommand(cmd);
    if (res.response.case === "getTime") {
      return res.response.value.time;
    }
    return 0;
  }

  getQueue(): Song[] {
    const cmd = new MainCommand({
      command: {
        case: "getQueue",
        value: new GetQueueRequest()
      }
    });
    sendMainCommand(cmd);
    return [];
  }
}

let apiInstance: ExtensionAPI;
export function getApi(): ExtensionAPI {
  if (!apiInstance) {
    apiInstance = new Api();
  }
  return apiInstance;
}

export function callListener(event: ExtensionEventCase, ...args: unknown[]) {
  if (LISTENERS && LISTENERS[event]) {
    return LISTENERS[event](...args);
  }
}

export function open_sock(path: string) {
  const { open_clientfd } = Host.getFunctions() as any;
  // @ts-ignore
  const msg = Memory.fromString(path);
  const offset = open_clientfd(msg.offset);
  // @ts-ignore
  const response = Memory.find(offset).readString();
  return JSON.parse(response);
}

export function write_sock(sock_id: number, buf: string) {
  const { write_sock } = Host.getFunctions() as any;
  // @ts-ignore
  const msg = Memory.fromString(buf);
  const offset = write_sock(sock_id, msg.offset);
  // @ts-ignore
  const response = Memory.find(offset).readString();
  return JSON.parse(response);
}

export function read_sock(sock_id: number, read_len: number) {
  const { read_sock } = Host.getFunctions() as any;
  const offset = read_sock(sock_id, read_len);
  // @ts-ignore
  const response = Memory.find(offset).readString();
  return JSON.parse(response);
}

export function hash(hash_type: "SHA1" | "SHA256" | "SHA512", data: string) {
  const { hash } = Host.getFunctions() as any;
  // @ts-ignore
  const hash_type_msg = Memory.fromString(hash_type);
  // @ts-ignore
  const data_msg = Memory.fromString(data);
  const offset = hash(hash_type_msg.offset, data_msg.offset);
  // @ts-ignore
  const response = Memory.find(offset).readBytes();
  return response;
}
