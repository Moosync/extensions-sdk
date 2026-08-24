"""
Rule for generating package.json for Moosync extensions natively in Starlark.
"""

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

    out_json = ctx.actions.declare_file("package.json")
    out_files.append(out_json)

    data = {
        "name": expand(ctx.attr.package_name_val) if ctx.attr.package_name_val else "",
        "displayName": expand(ctx.attr.display_name_val) if ctx.attr.display_name_val else "",
        "version": expand(ctx.attr.version_val) if ctx.attr.version_val else "0.0.0",
        "extensionEntry": ctx.file.extension_entry.basename,
        "moosyncExtension": True,
    }

    if icon_val:
        data["icon"] = icon_val

    perms = {}
    if ctx.attr.allowed_hosts_val:
        perms["hosts"] = [expand(v) for v in ctx.attr.allowed_hosts_val]
    if ctx.attr.allowed_paths_val:
        perms["paths"] = {expand(k): expand(v) for k, v in ctx.attr.allowed_paths_val.items()}

    if perms:
        data["permissions"] = perms

    ctx.actions.write(
        output = out_json,
        content = json.encode_indent(data, indent = "    ") + "\n",
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
    },
)

def generate_package_json(
        name,
        display_name = None,
        package_name = None,
        version = "0.0.0",
        icon = None,
        allowed_hosts = None,
        allowed_paths = None,
        data = [],
        visibility = None,
        wasm_target = None):
    """
    Macro to generate package.json if metadata is provided.

    Args:
        name: Name of the extension.
        display_name: Display name.
        package_name: Package name.
        version: Version string.
        icon: Icon file or label.
        allowed_hosts: List of allowed hosts.
        allowed_paths: Dict of allowed paths.
        data: Data dependencies.
        visibility: Visibility of the target.
        wasm_target: Label of the WASM target rule.

    Returns:
        List of targets generated (e.g. [":name_pkg_json"]), or empty list.
    """

    def is_file_like(arg):
        if not arg:
            return False
        if type(arg) != "string":
            return True
        return arg.startswith("//") or arg.startswith(":") or arg.startswith("@")

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

    if allowed_hosts:
        if type(allowed_hosts) == "list":
            pkg_args["allowed_hosts_val"] = allowed_hosts
        else:
            pkg_args["allowed_hosts_file"] = allowed_hosts

    if allowed_paths:
        if type(allowed_paths) == "dict":
            pkg_args["allowed_paths_val"] = allowed_paths
        else:
            pkg_args["allowed_paths_file"] = allowed_paths

    if pkg_args or package_name or display_name:
        if not wasm_target:
            fail("wasm_target is required to generate package.json")

        target_name = name + "_pkg_json"
        moosync_extension_package(
            name = target_name,
            extension_entry = wasm_target,
            data = data,
            visibility = visibility,
            **pkg_args
        )
        return [":" + target_name]

    return []
