"""
Unified definition file for all Moosync Wasm extension rules.
"""

load("//wasm-extension-go:defs.bzl", _go_extension = "go_extension")
load("//wasm-extension-js:defs.bzl", _js_extension = "js_wasm_extension")
load("//wasm-extension-py:defs.bzl", _py_extension = "py_extension")
load("//wasm-extension-rs:defs.bzl", _rust_extension = "rust_extension")

go_extension = _go_extension
js_extension = _js_extension
py_extension = _py_extension
rust_extension = _rust_extension
