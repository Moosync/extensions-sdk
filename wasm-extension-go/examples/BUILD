# ANCHOR: build_rule
load("@extensions_sdk//:defs.bzl", "go_extension")

package(default_visibility = ["//visibility:public"])

go_extension(
    name = "go_sample",
    srcs = ["main.go"],
    package_name = "moosync.sample.go",
    display_name = "Sample Extension (Go)",
    version = "0.0.1",
)
# ANCHOR_END: build_rule

exports_files(["BUILD"])
