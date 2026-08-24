# ANCHOR: build_rule
load("@extensions_sdk//:defs.bzl", "py_extension")

package(default_visibility = ["//visibility:public"])

py_extension(
    name = "py_sample",
    srcs = ["main.py"],
    main = "main.py",
    package_name = "moosync.sample.python",
    display_name = "Sample Extension (Python)",
    version = "0.0.1",
)
# ANCHOR_END: build_rule

exports_files(["BUILD"])
