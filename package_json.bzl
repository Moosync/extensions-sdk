"""
Rule for generating package.json for Moosync extensions.
"""

def _moosync_extension_package_impl(ctx):
    out_files = []

    def expand(val):
        if not val:
            return val
        return ctx.expand_location(val, targets = ctx.attr.data)

    icon_basename = None
    if ctx.file.icon_file:
        icon_out = ctx.actions.declare_file(ctx.file.icon_file.basename)
        ctx.actions.run_shell(
            inputs = [ctx.file.icon_file],
            outputs = [icon_out],
            command = "cp '{}' '{}'".format(ctx.file.icon_file.path, icon_out.path),
            mnemonic = "CopyIcon",
        )
        out_files.append(icon_out)
        icon_basename = ctx.file.icon_file.basename

    out_json = ctx.actions.declare_file("package.json")
    out_files.append(out_json)

    args = ctx.actions.args()
    args.add("--output", out_json)

    args.add("--extension_entry", ctx.file.extension_entry.basename)

    inputs = []

    def add_arg(name):
        val = getattr(ctx.attr, name + "_val")
        f = getattr(ctx.file, name + "_file")
        if val:
            if name == "allowed_hosts":
                expanded_list = [expand(v) for v in val]
                args.add("--" + name, json.encode(expanded_list))
            elif name == "allowed_paths":
                expanded_dict = {expand(k): expand(v) for k, v in val.items()}
                args.add("--" + name, json.encode(expanded_dict))
            else:
                args.add("--" + name, expand(val))
        elif f:
            inputs.append(f)
            args.add("--" + name + "_file", f)

    add_arg("package_name")
    add_arg("display_name")
    add_arg("version")

    if ctx.attr.icon_val:
        args.add("--icon", expand(ctx.attr.icon_val))
    elif icon_basename:
        args.add("--icon", icon_basename)

    add_arg("allowed_hosts")
    add_arg("allowed_paths")

    script = ctx.file._gen_script
    inputs.append(script)

    ctx.actions.run(
        executable = "python3",
        arguments = [script.path, args],
        inputs = inputs,
        outputs = [out_json],
        mnemonic = "GenPackageJson",
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
        "_gen_script": attr.label(
            default = Label("//:gen_package_json.py"),
            allow_single_file = True,
        ),
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

    # Helper to determine if arg is a Label or file-like string
    def is_file_like(arg):
        if not arg:
            return False
        if type(arg) != "string":
            return True  # Assume Label
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
