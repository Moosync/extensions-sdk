#!/usr/bin/env python3
import argparse
import json
import os
import sys

# Ensure external repos with protos (e.g. moosync) are in sys.path
for p in list(sys.path):
    for entry in os.listdir(p) if os.path.isdir(p) else []:
        if entry.startswith("moosync"):
            full_entry = os.path.join(p, entry)
            if full_entry not in sys.path:
                sys.path.insert(0, full_entry)

try:
    from core.types.protos import extensions_pb2
except ImportError:
    from moosync.core.types.protos import extensions_pb2


VALID_HASH_ALGORITHMS = {"sha256", "sha512", "md5"}


def normalize_directory(path_str):
    """Returns normalized directory of a path."""
    clean = path_str.replace("\\", "/").rstrip("/")
    if "/" in clean:
        return clean.rsplit("/", 1)[0]
    return clean


def is_path_covered(target_dir, allowed_paths):
    """
    Checks if target_dir is covered by any path in allowed_paths.
    Matches either source or target (guest) paths.
    """
    target_clean = target_dir.replace("\\", "/").rstrip("/")
    for p in allowed_paths:
        src = p.get("source", "").replace("\\", "/").rstrip("/")
        tgt = p.get("target", "").replace("\\", "/").rstrip("/")

        for base in [src, tgt]:
            if not base:
                continue
            if target_clean == base or target_clean.startswith(base + "/"):
                return True
    return False


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

    # JSON-based permission inputs
    parser.add_argument("--hosts-json", default="", help="JSON array of HostPermission")
    parser.add_argument("--paths-json", default="", help="JSON array of PathPermission")
    parser.add_argument("--binaries-json", default="", help="JSON array of BinaryPermission")
    parser.add_argument("--scopes-json", default="", help="JSON array of ScopePermission")

    # Legacy CLI arguments for fallback compatibility
    parser.add_argument("--allowed-host", action="append", default=[], help="Allowed host")
    parser.add_argument("--allowed-path", action="append", default=[], help="Allowed path pair host:guest")
    parser.add_argument("--binary", action="append", default=[], help="Allowed binary hash")
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

    # Process Scopes
    scopes_data = json.loads(args.scopes_json) if args.scopes_json else []
    for s in args.scope:
        scopes_data.append({"scope": s, "justification": ""})

    for s_item in scopes_data:
        raw_scope = str(s_item.get("scope", "")).strip().lower()
        if raw_scope.startswith("provider_scopes."):
            raw_scope = raw_scope.split(".", 1)[1]
        if raw_scope not in scope_map:
            raise ValueError(f"Unknown provider scope: '{raw_scope}'. Valid: {list(scope_map.keys())}")

        sp = m.scopes.add()
        sp.scope = scope_map[raw_scope]
        sp.justification = s_item.get("justification", "").strip()

    # Process Allowed Paths
    paths_data = json.loads(args.paths_json) if args.paths_json else []
    for p_pair in args.allowed_path:
        if ":" in p_pair:
            k, v = p_pair.split(":", 1)
            paths_data.append({"source": k, "target": v, "justification": ""})

    # Process Allowed Hosts
    hosts_data = json.loads(args.hosts_json) if args.hosts_json else []
    for h in args.allowed_host:
        hosts_data.append({"host": h, "justification": ""})

    # Process Binaries
    binaries_data = json.loads(args.binaries_json) if args.binaries_json else []
    for b in args.binary:
        binaries_data.append({
            "name": b,
            "path": b,
            "hashes": {"sha256": b.strip().lower()},
            "justification": "",
        })

    # Validate Binaries & directory containment in allowed_paths
    for b_item in binaries_data:
        b_name = b_item.get("name") or b_item.get("path", "")
        b_path = b_item.get("path") or b_name
        if not b_path:
            raise ValueError("Binary must specify a valid name or path.")

        hashes = b_item.get("hashes", {})
        valid_hashes = {
            alg.lower(): h.strip().lower()
            for alg, h in hashes.items()
            if alg.lower() in VALID_HASH_ALGORITHMS and h.strip()
        }
        if not valid_hashes:
            raise ValueError(
                f"Binary '{b_path}' must have at least one valid hash among {sorted(VALID_HASH_ALGORITHMS)}. Found: {hashes}"
            )
        b_item["valid_hashes"] = valid_hashes

        # Check binary directory presence in allowed_paths
        binary_dir = normalize_directory(b_path)
        if binary_dir and not is_path_covered(binary_dir, paths_data):
            raise ValueError(
                f"Binary '{b_path}' is located in directory '{binary_dir}', but this directory is not in allowed_paths! "
                f"You must add '{binary_dir}' to allowed_paths."
            )

    # Populate ManifestPermissions
    if hosts_data or paths_data or binaries_data:
        perms = extensions_pb2.ManifestPermissions()

        for h_item in hosts_data:
            host_val = h_item.get("host", "").strip()
            if not host_val:
                continue
            hp = perms.hosts.add()
            hp.host = host_val
            hp.justification = h_item.get("justification", "").strip()

        for p_item in paths_data:
            source_val = p_item.get("source", "").strip()
            target_val = p_item.get("target", "").strip()
            if not source_val or not target_val:
                continue
            pp = perms.paths.add()
            pp.source = source_val
            pp.target = target_val
            pp.justification = p_item.get("justification", "").strip()

        for b_item in binaries_data:
            b_path = b_item.get("path") or b_item.get("name", "")
            bp = perms.binaries.add()
            bp.name = b_path
            bp.justification = b_item.get("justification", "").strip()
            for alg, h in b_item["valid_hashes"].items():
                bp.hashes[alg] = h

        m.permissions.CopyFrom(perms)

    with open(args.out, "wb") as f:
        f.write(m.SerializeToString())


if __name__ == "__main__":
    main()
