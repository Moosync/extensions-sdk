# ANCHOR: build_rule
load("@extensions_sdk//:defs.bzl", "js_extension")

package(default_visibility = ["//visibility:public"])

js_extension(
    name = "js_sample",
    srcs = ["src/index.ts"],
    package_name = "moosync.sample.js",
    display_name = "Sample Extension (JavaScript)",
    version = "0.0.1",
)
# ANCHOR_END: build_rule

exports_files(["BUILD"])
