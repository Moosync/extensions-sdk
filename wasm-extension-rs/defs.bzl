"""
Wasm extension rules for Rust.
"""

load("@rules_rust//rust:defs.bzl", "rust_binary")
load("//:package_json.bzl", "generate_package_json")

def rust_extension(
        name,
        srcs,
        deps = [],
        data = [],
        edition = "2024",
        display_name = None,
        package_name = None,
        version = None,
        icon = None,
        allowed_hosts = None,
        allowed_paths = None,
        **kwargs):
    """
    Builds a Wasm extension from Rust sources.

        srcs: Source files.
        deps: Dependencies.
        data: Data dependencies.
        edition: Rust edition. Defaults to "2024".
        display_name: Display name of the extension.
        package_name: Package name of the extension (mapped to name in json).
        version: Version of the extension.
        icon: Icon of the extension. Can be file path or label.
        allowed_hosts: List of allowed hosts.
        allowed_paths: Dict of allowed paths.
        **kwargs: Additional arguments to pass to rust_binary.
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
        visibility = kwargs.get("visibility"),
        wasm_target = ":" + name + "_wasm_file",
    )

    rust_binary(
        name = name + "_wasm",
        srcs = srcs,
        deps = deps + [Label("//wasm-extension-rs:wasm_extension_rs")],
        data = data,
        platform = "@rules_rust//rust/platform:wasi",
        edition = edition,
        tags = ["manual"],
        **kwargs
    )

    native.genrule(
        name = name + "_wasm_file",
        srcs = [":" + name + "_wasm"],
        outs = [name + ".wasm"],
        cmd = "cp $< $@",
        visibility = kwargs.get("visibility"),
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_wasm_file"] + pkg_json_targets,
        **kwargs
    )
