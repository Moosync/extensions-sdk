load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library", "py_test")
load("@rules_python//python/entry_points:py_console_script_binary.bzl", "py_console_script_binary")

exports_files(
    [
        "pytest_wrapper.py",
        ".pylintrc",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "elf_align_lib",
    srcs = ["elf_align.py"],
    imports = [".."],
    visibility = ["//visibility:public"],
)

py_binary(
    name = "elf_align",
    srcs = ["elf_align.py"],
    main = "elf_align.py",
    visibility = ["//visibility:public"],
)

py_test(
    name = "elf_align_test",
    srcs = ["test_elf_align.py"],
    main = "test_elf_align.py",
    deps = [":elf_align_lib"],
)

py_binary(
    name = "hash_binary",
    srcs = ["hash_binary.py"],
    main = "hash_binary.py",
    visibility = ["//visibility:public"],
)

py_binary(
    name = "check_git_override",
    srcs = ["check_git_override.py"],
    main = "check_git_override.py",
    visibility = ["//visibility:public"],
)

py_binary(
    name = "scaffold",
    srcs = ["scaffold.py"],
    data = glob(["templates/**"]),
    main = "scaffold.py",
    visibility = ["//visibility:public"],
)

py_binary(
    name = "gen_manifest",
    srcs = ["gen_manifest.py"],
    main = "gen_manifest.py",
    visibility = ["//visibility:public"],
    deps = [
        "//protos:extensions_py_proto",
        "//protos:moosync_python_root",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_console_script_binary(
    name = "pdoc",
    pkg = "@pip_deps//pdoc:pkg",
    deps = [
        "@pip_deps//extism:pkg",
        "@pip_deps//protobuf:pkg",
    ],
    visibility = ["//wasm-extension-py:__pkg__"],
)

py_binary(
    name = "serve",
    srcs = ["serve.py"],
    main = "serve.py",
    visibility = ["//docs:__pkg__"],
)

alias(
    name = "mdbook_admonish",
    actual = "@mdbook_admonish_tool//:mdbook-admonish",
    visibility = ["//docs:__pkg__"],
)

alias(
    name = "mdbook_tabs",
    actual = "@host_crates//:mdbook-tabs__mdbook-tabs",
    visibility = ["//docs:__pkg__"],
)
