load("//:defs.bzl", "py_extension")

package(default_visibility = ["//visibility:public"])

py_extension(
    name = "sample_extension",
    srcs = ["main.py"],
    main = "//wasm-extension-py:moosync_edk/__init__.py",
)
