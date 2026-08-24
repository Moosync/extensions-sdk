load("@rules_rust//rust:defs.bzl", "rust_doc", "rust_library")

package(default_visibility = ["//visibility:public"])

rust_doc(
    name = "doc",
    crate = ":wasm_extension_rs",
)

rust_library(
    name = "wasm_extension_rs",
    srcs = glob(["src/**/*.rs"]),
    crate_name = "moosync_edk",
    edition = "2024",
    target_compatible_with = [
        "@platforms//os:wasi",
    ],
    deps = [
        "//protos:extensions_rs",
        "//protos:songs_rs",
        "//protos:themes_rs",
        "//protos:ui_rs",
        "//protos:duration_rs",
        "@sdk_wasm_crates//:extism-convert",
        "@sdk_wasm_crates//:extism-pdk",
        "@sdk_wasm_crates//:lazy_static",
        "@sdk_wasm_crates//:prost-types",
        "@sdk_wasm_crates//:serde",
        "@sdk_wasm_crates//:serde_json",
        "@sdk_wasm_crates//:tokio",
        "@sdk_wasm_crates//:tracing",
    ],
)
