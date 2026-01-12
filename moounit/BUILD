load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pypi_moounit//:requirements.bzl", "requirement")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("//wasm-extension-py:defs.bzl", "expose_pyi")

package(default_visibility = ["//visibility:public"])

compile_pip_requirements(
    name = "requirements",
    src = "requirements.txt",
    generate_hashes = False,
    requirements_txt = "requirements_lock.txt",
)

py_library(
    name = "moounit",
    srcs = [
        "__init__.py",
        "lib.py",
    ],
    imports = ["moounit"],
    deps = [
        requirement("extism"),
        requirement("pytest"),
        "@com_google_protobuf//:protobuf_python",
        "@moosync//:moosync_python_root",
        "@moosync//core/types/protos:extensions_py_proto",
        "@moosync//core/types/protos:songs_py_proto",
        "@moosync//core/types/protos:ui_py_proto",
    ],
)

expose_pyi(
    name = "moounit_pyi",
    deps = [
        "@moosync//core/types/protos:extensions_py_proto",
        "@moosync//core/types/protos:songs_py_proto",
        "@moosync//core/types/protos:themes_py_proto",
        "@moosync//core/types/protos:ui_py_proto",
    ],
)

py_binary(
    name = "dummy",
    srcs = [
        "lib.py",
    ],
    args = ["$(location sample/package.json)"],
    data = [
        ":moounit_pyi",
    ],
    main = "lib.py",
    tags = ["manual"],
    visibility = ["//visibility:private"],
    deps = [
        requirement("extism"),
        ":moounit_pyi",
        "//wasm-extension-py:moosync_edk",
        "@moosync//:moosync_python_root",
    ],
)
