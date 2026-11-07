load("@rules_rust//rust:defs.bzl", "rust_doc", "rust_library")
load("//tools/sdk_generator:defs.bzl", "generate_extension_sdk")

generate_extension_sdk(
    name = "gen_rust_sdk",
    proto = "//protos:extension_service_proto",
    lang = "rust",
    out_api = "src/generated_api.rs",
    out_dispatcher = "src/generated_dispatcher.rs",
)

rust_doc(
    name = "doc",
    crate = ":wasm_extension_rs",
    visibility = ["//docs:__pkg__"],
)

rust_library(
    name = "wasm_extension_rs",
    srcs = glob(["src/**/*.rs"]) + [":gen_rust_sdk"],
    crate_name = "moosync_edk",
    edition = "2024",
    target_compatible_with = [
        "@platforms//os:wasi",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//protos:extension_service_rs",
        "//protos:extensions_rs",
        "//protos:preferences_rs",
        "//protos:songs_rs",
        "//protos:themes_rs",
        "//protos:ui_rs",
        "//protos:duration_rs",
        "@sdk_wasm_crates//:extism-convert",
        "@sdk_wasm_crates//:extism-pdk",
        "@sdk_wasm_crates//:lazy_static",
        "@sdk_wasm_crates//:prost",
        "@sdk_wasm_crates//:prost-types",
        "@sdk_wasm_crates//:serde",
        "@sdk_wasm_crates//:serde_json",
        "@sdk_wasm_crates//:tokio",
        "@sdk_wasm_crates//:tracing",
    ],
)
