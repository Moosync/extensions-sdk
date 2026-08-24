# ANCHOR: build_rule
load("@extensions_sdk//:defs.bzl", "rust_extension")

package(default_visibility = ["//visibility:public"])

rust_extension(
    name = "rust_sample",
    srcs = ["src/lib.rs"],
    package_name = "moosync.sample.rust",
    display_name = "Sample Extension (Rust)",
    version = "0.0.1",
)
# ANCHOR_END: build_rule

exports_files(["BUILD"])
