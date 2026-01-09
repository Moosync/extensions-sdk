load("@rules_rust//rust:defs.bzl", "rust_library")

package(default_visibility = ["//visibility:public"])

rust_library(
    name = "wasm_extension_rs",
    srcs = glob(["src/**/*.rs"]),
    crate_name = "moosync_edk",
    edition = "2024",
    target_compatible_with = [
        "@platforms//os:wasi",
    ],
    deps = [
        "@moosync//core/types/protos:extensions_rs",
        "@moosync//core/types/protos:songs_rs",
        "@moosync//core/types/protos:themes_rs",
        "@moosync//core/types/protos:ui_rs",
        "@sdk_wasm_crates//:extism-convert",
        "@sdk_wasm_crates//:extism-pdk",
        "@sdk_wasm_crates//:lazy_static",
        "@sdk_wasm_crates//:prost-types",
        "@sdk_wasm_crates//:tokio",
        "@sdk_wasm_crates//:tracing",
    ],
)
