#!/usr/bin/env python3
import argparse
import sys
from core.types.protos import extensions_pb2


def main():
    parser = argparse.ArgumentParser(description="Generate manifest.pb")
    parser.add_argument("--out", required=True, help="Output manifest.pb path")
    parser.add_argument("--name", default="", help="Extension package name")
    parser.add_argument("--display-name", default="", help="Display name")
    parser.add_argument("--version", default="0.0.0", help="Version")
    parser.add_argument("--entry", default="", help="Entry wasm filename")
    parser.add_argument("--icon", default="", help="Icon filename")
    parser.add_argument("--author", default="", help="Author")
    parser.add_argument("--description", default="", help="Description")
    parser.add_argument("--allowed-host", action="append", default=[], help="Allowed host")
    parser.add_argument("--allowed-path", action="append", default=[], help="Allowed path pair host:guest")
    parser.add_argument("--scope", action="append", default=[], help="Provider scope")

    args = parser.parse_args()

    m = extensions_pb2.ExtensionManifest()
    m.moosync_extension = True
    m.name = args.name
    m.display_name = args.display_name
    m.version = args.version
    m.extension_entry = args.entry
    if args.icon:
        m.icon = args.icon
    if args.author:
        m.author = args.author
    if args.description:
        m.description = args.description

    scope_map = {
        name.lower(): val
        for name, val in extensions_pb2.ExtensionProviderScope.items()
    }
    for s in args.scope:
        norm = s.strip().lower()
        if norm in scope_map:
            m.scopes.append(scope_map[norm])
        else:
            raise ValueError(f"Unknown provider scope: '{s}'. Valid: {list(scope_map.keys())}")

    if args.allowed_host or args.allowed_path:
        perms = extensions_pb2.ManifestPermissions()
        for host in args.allowed_host:
            perms.hosts.append(host)
        for path_pair in args.allowed_path:
            if ":" in path_pair:
                k, v = path_pair.split(":", 1)
                perms.paths[k] = v
        m.permissions.CopyFrom(perms)

    with open(args.out, "wb") as f:
        f.write(m.SerializeToString())


if __name__ == "__main__":
    main()
