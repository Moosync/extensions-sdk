load("@rules_rust//rust:defs.bzl", "rust_library_group")
load("@rules_rust_prost//:defs.bzl", "rust_prost_toolchain")

package(default_visibility = ["//visibility:public"])

alias(
    name = "prost_wasm",
    actual = "@sdk_wasm_crates//:prost",
)

alias(
    name = "prost_types_wasm",
    actual = "@sdk_wasm_crates//:prost-types",
)

alias(
    name = "protoc_gen_prost_wasm",
    actual = "@sdk_wasm_crates//:protoc-gen-prost__protoc-gen-prost",
)

PROST_OPTS = []

rust_library_group(
    name = "prost_runtime_wasi",
    deps = [
        "@sdk_wasm_crates//:prost",
    ],
)

rust_prost_toolchain(
    name = "prost_toolchain_impl_wasi",
    prost_opts = PROST_OPTS,
    prost_plugin = "@sdk_wasm_crates//:protoc-gen-prost__protoc-gen-prost",
    prost_runtime = ":prost_runtime_wasi",
    prost_types = "@sdk_wasm_crates//:prost-types",
    tonic_plugin_flag = "",
    visibility = ["//visibility:public"],
)

toolchain(
    name = "prost_toolchain_wasi",
    target_compatible_with = ["@platforms//cpu:wasm32"],
    toolchain = ":prost_toolchain_impl_wasi",
    toolchain_type = "@rules_rust_prost//:toolchain_type",
)
