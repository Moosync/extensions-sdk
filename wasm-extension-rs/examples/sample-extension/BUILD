load("@rules_rust//rust:defs.bzl", "rust_shared_library")

package(default_visibility = ["//visibility:public"])

rust_shared_library(
    name = "sample_extension",
    srcs = ["src/lib.rs"],
    edition = "2021",
    target_compatible_with = [
        "@platforms//os:wasi",
    ],
    deps = [
        "//wasm-extension-rs:wasm_extension_rs",
        "@sdk_wasm_crates//:serde_json",
    ],
)
