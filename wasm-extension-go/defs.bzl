"""
Wasm extension rules for Go.
"""

load("@rules_go//go:def.bzl", "go_binary")
load("//:package_json.bzl", "generate_package_json")

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
        **kwargs: Additional arguments to pass to go_binary.
    """

    pkg_json_targets = generate_package_json(
        name = name,
        display_name = display_name,
        package_name = package_name,
        version = version,
        icon = icon,
        allowed_hosts = allowed_hosts,
        allowed_paths = allowed_paths,
        data = data,
        visibility = visibility,
        wasm_target = ":" + name + "_wasm_file",
    )

    go_binary(
        name = name + "_wasm",
        srcs = srcs,
        deps = deps + [
            Label("//wasm-extension-go/pkg/api"),
            "@com_github_extism_go_pdk//:go_default_library",
            "//protos:extensions_go_proto",
            "//protos:songs_go_proto",
            "//protos:ui_go_proto",
        ],
        data = data,
        goos = "wasip1",
        goarch = "wasm",
        out = name + ".wasm",
        linkmode = "c-shared",
        cgo = True,
        pure = "on",
        **kwargs
    )

    native.genrule(
        name = name + "_wasm_file",
        srcs = [":" + name + "_wasm"],
        outs = [name + ".wasm"],
        cmd = "cp $< $@",
        visibility = visibility,
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_wasm_file"] + pkg_json_targets,
        visibility = visibility,
        **kwargs
    )
