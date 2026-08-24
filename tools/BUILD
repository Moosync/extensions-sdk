load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@rules_python//python/entry_points:py_console_script_binary.bzl", "py_console_script_binary")

package(default_visibility = ["//visibility:public"])

exports_files([
    "pytest_wrapper.py",
    ".pylintrc",
    "requirements.txt",
])

py_binary(
    name = "scaffold",
    srcs = ["scaffold.py"],
    data = glob(["templates/**"]),
    main = "scaffold.py",
    visibility = ["//visibility:public"],
)

py_console_script_binary(
    name = "pdoc",
    pkg = "@pip_deps//pdoc:pkg",
    deps = [
        "@pip_deps//extism:pkg",
        "@pip_deps//protobuf:pkg",
    ],
    visibility = ["//visibility:public"],
)

py_binary(
    name = "serve",
    srcs = ["serve.py"],
    main = "serve.py",
    visibility = ["//visibility:public"],
)

alias(
    name = "mdbook",
    actual = "@mdbook_tool//:mdbook",
    visibility = ["//visibility:public"],
)

alias(
    name = "mdbook_admonish",
    actual = "@mdbook_admonish_tool//:mdbook-admonish",
    visibility = ["//visibility:public"],
)

alias(
    name = "mdbook_tabs",
    actual = "@host_crates//:mdbook-tabs__mdbook-tabs",
    visibility = ["//visibility:public"],
)
