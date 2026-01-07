load("//wasm-extension-py:defs.bzl", "py_wasm_extension")

package(default_visibility = ["//visibility:public"])

py_wasm_extension(
    name = "sample_extension",
    srcs = ["main.py"],
    main = "//wasm-extension-py:moosync_edk/__init__.py",
    deps = [
        "//wasm-extension-py:moosync_edk",
    ],
)
