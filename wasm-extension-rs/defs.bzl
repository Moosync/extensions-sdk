"""
Wasm extension rules for Rust.
"""

load("@rules_rust//rust:defs.bzl", "rust_shared_library")

def _wasi_transition_impl(_settings, _attr):
    return {
        "//command_line_option:platforms": "@rules_rust//rust/platform:wasi",
    }

wasi_transition = transition(
    implementation = _wasi_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

def _wasm_transition_rule_impl(ctx):
    # transition is 1:1, so actual_target is a list containing a single Target
    target = ctx.attr.actual_target[0]

    wasm_file = None
    for f in target.files.to_list():
        if f.extension == "wasm":
            wasm_file = f
            break

    if not wasm_file:
        files = [f.path for f in target.files.to_list()]
        fail("No .wasm file found in output of rust_shared_library. Found: {}".format(files))

    out = ctx.actions.declare_file(ctx.label.name + ".wasm")
    ctx.actions.run_shell(
        inputs = [wasm_file],
        outputs = [out],
        command = "cp '{}' '{}'".format(wasm_file.path, out.path),
        mnemonic = "CopyWasm",
    )

    return [DefaultInfo(files = depset([out]))]

_wasm_platform_transition_rule = rule(
    implementation = _wasm_transition_rule_impl,
    attrs = {
        "actual_target": attr.label(cfg = wasi_transition),
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
    },
)

def rust_extension(name, srcs, deps = [], edition = "2021", visibility = None, **kwargs):
    """
    Builds a Wasm extension from Rust sources.

    Args:
        name: The name of the target.
        srcs: Source files.
        deps: Dependencies.
        edition: Rust edition. Defaults to "2021".
        visibility: Target visibility.
        **kwargs: Additional arguments to pass to rust_shared_library.
    """
    internal_name = name + "_internal"

    rust_shared_library(
        name = internal_name,
        srcs = srcs,
        deps = deps + [Label("//wasm-extension-rs:wasm_extension_rs")],
        target_compatible_with = ["@platforms//os:wasi"],
        edition = edition,
        # Hide the internal target and prevent wildcard expansion from building it on host
        visibility = ["//visibility:private"],
        tags = ["manual"],
        **kwargs
    )

    _wasm_platform_transition_rule(
        name = name,
        actual_target = internal_name,
        visibility = visibility,
    )
