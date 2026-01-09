load("//:defs.bzl", "rust_extension")

package(default_visibility = ["//visibility:public"])

rust_extension(
    name = "sample_extension_custom",
    srcs = ["src/lib.rs"],
    deps = [
        "@sdk_wasm_crates//:serde_json",
    ],
)
