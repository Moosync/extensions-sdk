"""
Wasm extension rules for Go.
"""

load("@rules_go//go:def.bzl", "go_binary")
load("//:manifest_pb.bzl", "generate_manifest_pb")
load("//:package_extension.bzl", "package_extension")

def go_extension(
        name,
        srcs,
        deps = [],
        data = [],
        visibility = None,
        display_name = None,
        package_name = None,
        version = None,
        icon = None,
        allowed_hosts = None,
        allowed_paths = None,
        scopes = None,
        **kwargs):
    """
    Builds a Wasm extension from Go sources.

        srcs: Source files.
        deps: Dependencies.
        data: Data dependencies.
        visibility: Target visibility.
        display_name: Display name of the extension.
        package_name: Package name of the extension (mapped to name in json).
        version: Version of the extension.
        icon: Icon of the extension. Can be file path or label.
        allowed_hosts: List of allowed hosts.
        allowed_paths: Dict of allowed paths.
        scopes: List of provider scopes.
        **kwargs: Additional arguments to pass to go_binary.
    """

    manifest_pb_targets = generate_manifest_pb(
        name = name,
        display_name = display_name,
        package_name = package_name,
        version = version,
        icon = icon,
        allowed_hosts = allowed_hosts,
        allowed_paths = allowed_paths,
        scopes = scopes,
        data = data,
        visibility = visibility,
        wasm_target = ":" + name + "_wasm",
    )

    go_binary(
        name = name + "_wasm_bin",
        srcs = srcs,
        deps = deps + [
            Label("//wasm-extension-go/pkg/api"),
            Label("@com_github_extism_go_pdk//:go_default_library"),
            Label("//protos:extensions_go_proto"),
            Label("//protos:preferences_go_proto"),
            Label("//protos:songs_go_proto"),
            Label("//protos:ui_go_proto"),
        ],
        data = data,
        goos = "wasip1",
        goarch = "wasm",
        out = name + ".wasm",
        linkmode = "c-shared",
        cgo = True,
        pure = "on",
        visibility = ["//visibility:private"],
        **kwargs
    )

    native.genrule(
        name = name + "_wasm",
        srcs = [":" + name + "_wasm_bin"],
        outs = [name + ".wasm"],
        cmd = "cp $< $@",
        visibility = ["//visibility:private"],
    )

    native.filegroup(
        name = name + "_unpacked",
        srcs = [":" + name + "_wasm"] + manifest_pb_targets,
        visibility = visibility,
    )

    package_extension(
        name = name,
        extension_target = ":" + name + "_unpacked",
        visibility = visibility,
    )

    native.filegroup(
        name = name,
        srcs = [
            ":" + name + "_unpacked",
            ":" + name + "_msxt",
        ],
        visibility = visibility,
    )
