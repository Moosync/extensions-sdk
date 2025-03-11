import { ExtensionAPI } from "./types";
export interface MoosyncExtensionTemplate {
    onStarted: () => Promise<void>;
}
export declare const api: ExtensionAPI;
export declare function callListener(event: string, ...args: unknown[]): Promise<any>;
export declare function open_sock(path: string): any;
export declare function write_sock(sock_id: number, buf: string): any;
export declare function read_sock(sock_id: number, read_len: number): any;
export declare function hash(hash_type: "SHA1" | "SHA256" | "SHA512", data: string): ArrayBuffer;
//# sourceMappingURL=api.d.ts.map