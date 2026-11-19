"""
Rule for generating manifest.pb for Moosync extensions natively in Starlark.
"""

def _normalize_scopes(scopes):
    if not scopes:
        return []
    res = []
    if type(scopes) == "dict":
        for k, v in scopes.items():
            if type(k) == "tuple" or type(k) == "list":
                for s in k:
                    res.append({"scope": str(s), "justification": str(v)})
            else:
                res.append({"scope": str(k), "justification": str(v)})
    elif type(scopes) == "list":
        for item in scopes:
            if type(item) == "dict":
                just = item.get("justification", "")
                if "scopes" in item:
                    for s in item["scopes"]:
                        res.append({"scope": str(s), "justification": str(just)})
                elif "scope" in item:
                    res.append({"scope": str(item["scope"]), "justification": str(just)})
            else:
                res.append({"scope": str(item), "justification": ""})
    return res

def _normalize_hosts(hosts):
    if not hosts:
        return []
    res = []
    if type(hosts) == "dict":
        for k, v in hosts.items():
            if type(k) == "tuple" or type(k) == "list":
                for h in k:
                    res.append({"host": str(h), "justification": str(v)})
            else:
                res.append({"host": str(k), "justification": str(v)})
    elif type(hosts) == "list":
        for item in hosts:
            if type(item) == "dict":
                just = item.get("justification", "")
                if "hosts" in item:
                    for h in item["hosts"]:
                        res.append({"host": str(h), "justification": str(just)})
                elif "host" in item:
                    res.append({"host": str(item["host"]), "justification": str(just)})
            else:
                res.append({"host": str(item), "justification": ""})
    return res

def _normalize_paths(paths):
    if not paths:
        return []
    res = []
    if type(paths) == "dict":
        for k, v in paths.items():
            if type(v) == "dict" and "target" in v:
                res.append({"source": str(k), "target": str(v["target"]), "justification": str(v.get("justification", ""))})
            elif type(v) == "string":
                if ":" in str(k):
                    src, tgt = str(k).split(":", 1)
                    res.append({"source": src, "target": tgt, "justification": str(v)})
                else:
                    res.append({"source": str(k), "target": str(v), "justification": ""})
    elif type(paths) == "list":
        for item in paths:
            if type(item) == "dict":
                just = item.get("justification", "")
                if "paths" in item:
                    for p in item["paths"]:
                        res.append({"source": str(p["source"]), "target": str(p["target"]), "justification": str(just)})
                elif "source" in item and "target" in item:
                    res.append({"source": str(item["source"]), "target": str(item["target"]), "justification": str(just)})
    return res

def _normalize_binaries(binaries):
    if not binaries:
        return []
    res = []
    if type(binaries) == "dict":
        for b_name, b_cfg in binaries.items():
            if type(b_cfg) == "dict":
                hashes = {}
                for alg in ["sha256", "sha512", "md5"]:
                    if alg in b_cfg:
                        hashes[alg] = str(b_cfg[alg])
                if "hashes" in b_cfg and type(b_cfg["hashes"]) == "dict":
                    for alg, h in b_cfg["hashes"].items():
                        hashes[alg] = str(h)
                res.append({
                    "name": str(b_name),
                    "path": str(b_cfg.get("path", b_name)),
                    "hashes": hashes,
                    "justification": str(b_cfg.get("justification", "")),
                })
    elif type(binaries) == "list":
        for item in binaries:
            if type(item) == "dict":
                b_name = str(item.get("name", item.get("path", "")))
                b_path = str(item.get("path", b_name))
                hashes = {}
                for alg in ["sha256", "sha512", "md5"]:
                    if alg in item:
                        hashes[alg] = str(item[alg])
                if "hashes" in item and type(item["hashes"]) == "dict":
                    for alg, h in item["hashes"].items():
                        hashes[alg] = str(h)
                res.append({
                    "name": b_name,
                    "path": b_path,
                    "hashes": hashes,
                    "justification": str(item.get("justification", "")),
                })
            else:
                res.append({
                    "name": str(item),
                    "path": str(item),
                    "hashes": {"sha256": str(item)},
                    "justification": "",
                })
    return res

def _moosync_extension_package_impl(ctx):
    out_files = []

    def expand(val):
        if not val:
            return val
        return ctx.expand_location(val, targets = ctx.attr.data)

    icon_val = None
    if ctx.file.icon_file:
        icon_out = ctx.actions.declare_file(ctx.file.icon_file.basename)
        ctx.actions.run_shell(
            inputs = [ctx.file.icon_file],
            outputs = [icon_out],
            command = "cp '{}' '{}'".format(ctx.file.icon_file.path, icon_out.path),
            mnemonic = "CopyIcon",
        )
        out_files.append(icon_out)
        icon_val = ctx.file.icon_file.basename
    elif ctx.attr.icon_val:
        icon_val = expand(ctx.attr.icon_val)

    out_pb = ctx.actions.declare_file("manifest.pb")
    out_files.append(out_pb)

    args = ctx.actions.args()
    args.add("--out", out_pb.path)
    args.add("--name", expand(ctx.attr.package_name_val) if ctx.attr.package_name_val else "")
    args.add("--display-name", expand(ctx.attr.display_name_val) if ctx.attr.display_name_val else "")
    args.add("--version", expand(ctx.attr.version_val) if ctx.attr.version_val else "0.0.0")
    args.add("--entry", ctx.file.extension_entry.basename)

    if icon_val:
        args.add("--icon", icon_val)

    if ctx.attr.hosts_json:
        args.add("--hosts-json", ctx.attr.hosts_json)
    elif ctx.attr.allowed_hosts_val:
        for host in ctx.attr.allowed_hosts_val:
            args.add("--allowed-host", expand(host))

    if ctx.attr.paths_json:
        args.add("--paths-json", ctx.attr.paths_json)
    elif ctx.attr.allowed_paths_val:
        for k, v in ctx.attr.allowed_paths_val.items():
            args.add("--allowed-path", "{}:{}".format(expand(k), expand(v)))

    if ctx.attr.binaries_json:
        args.add("--binaries-json", ctx.attr.binaries_json)
    elif ctx.attr.binaries_val:
        for b in ctx.attr.binaries_val:
            args.add("--binary", expand(b))

    if ctx.attr.scopes_json:
        args.add("--scopes-json", ctx.attr.scopes_json)
    elif ctx.attr.scopes_val:
        for scope in ctx.attr.scopes_val:
            args.add("--scope", expand(scope))

    ctx.actions.run(
        inputs = [ctx.file.extension_entry],
        outputs = [out_pb],
        executable = ctx.executable._gen_manifest,
        arguments = [args],
        mnemonic = "GenManifestPb",
    )

    return [DefaultInfo(files = depset(out_files))]

moosync_extension_package = rule(
    implementation = _moosync_extension_package_impl,
    attrs = {
        "extension_entry": attr.label(allow_single_file = True, mandatory = True),
        "data": attr.label_list(allow_files = True),
        "package_name_val": attr.string(),
        "package_name_file": attr.label(allow_single_file = True),
        "display_name_val": attr.string(),
        "display_name_file": attr.label(allow_single_file = True),
        "version_val": attr.string(),
        "version_file": attr.label(allow_single_file = True),
        "icon_val": attr.string(),
        "icon_file": attr.label(allow_single_file = True),
        "allowed_hosts_val": attr.string_list(),
        "allowed_hosts_file": attr.label(allow_single_file = True),
        "allowed_paths_val": attr.string_dict(),
        "allowed_paths_file": attr.label(allow_single_file = True),
        "binaries_val": attr.string_list(default = []),
        "binaries_file": attr.label(allow_single_file = True),
        "scopes_val": attr.string_list(default = []),
        "scopes_file": attr.label(allow_single_file = True),
        "hosts_json": attr.string(default = ""),
        "paths_json": attr.string(default = ""),
        "binaries_json": attr.string(default = ""),
        "scopes_json": attr.string(default = ""),
        "_gen_manifest": attr.label(
            default = Label("//tools:gen_manifest"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def generate_manifest_pb(
        name,
        display_name = None,
        package_name = None,
        version = "0.0.0",
        icon = None,
        allowed_hosts = None,
        allowed_paths = None,
        binaries = None,
        scopes = None,
        data = [],
        visibility = None,
        wasm_target = None):
    """
    Macro to generate manifest.pb if metadata is provided.
    """

    def is_file_like(arg):
        if not arg:
            return False
        if type(arg) == "list" or type(arg) == "dict":
            return False
        if type(arg) == "string":
            return arg.startswith("//") or arg.startswith(":") or arg.startswith("@")
        return True

    pkg_args = {}

    def map_arg(attr_name, val):
        if val == None:
            return
        if is_file_like(val):
            pkg_args[attr_name + "_file"] = val
        else:
            pkg_args[attr_name + "_val"] = val

    map_arg("package_name", package_name)
    map_arg("display_name", display_name)
    map_arg("version", version)
    map_arg("icon", icon)

    if allowed_hosts != None:
        if is_file_like(allowed_hosts):
            pkg_args["allowed_hosts_file"] = allowed_hosts
        else:
            pkg_args["hosts_json"] = json.encode(_normalize_hosts(allowed_hosts))

    if allowed_paths != None:
        if is_file_like(allowed_paths):
            pkg_args["allowed_paths_file"] = allowed_paths
        else:
            pkg_args["paths_json"] = json.encode(_normalize_paths(allowed_paths))

    if binaries != None:
        if is_file_like(binaries):
            pkg_args["binaries_file"] = binaries
        else:
            pkg_args["binaries_json"] = json.encode(_normalize_binaries(binaries))

    if scopes != None:
        if is_file_like(scopes):
            pkg_args["scopes_file"] = scopes
        else:
            pkg_args["scopes_json"] = json.encode(_normalize_scopes(scopes))

    if pkg_args or package_name or display_name:
        if not wasm_target:
            fail("wasm_target is required to generate manifest.pb")

        target_name = name + "_manifest_pb"
        moosync_extension_package(
            name = target_name,
            extension_entry = wasm_target,
            data = data,
            visibility = visibility,
            **pkg_args
        )
        return [":" + target_name]

    return []
