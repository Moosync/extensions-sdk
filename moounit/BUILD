load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pypi_moounit//:requirements.bzl", "requirement")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("//tools:defs.bzl", "pytest_test")
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
        "core.py",
        "defaults.py",
        "expectations.py",
        "matcher.py",
        "models.py",
        "passthrough.py",
        "pytest_plugin.py",
        "recorder.py",
    ],
    imports = ["moounit"],
    deps = [
        requirement("extism"),
        requirement("pytest"),
        "//protos:extensions_py_proto",
        "//protos:moosync_python_root",
        "//protos:songs_py_proto",
        "//protos:ui_py_proto",
        "@com_google_protobuf//:protobuf_python",
    ],
)

expose_pyi(
    name = "moounit_pyi",
    deps = [
        "//protos:extensions_py_proto",
        "//protos:songs_py_proto",
        "//protos:themes_py_proto",
        "//protos:ui_py_proto",
    ],
)

pytest_test(
    name = "moounit_unit_test",
    srcs = ["test_moounit.py"],
    deps = [
        ":moounit",
    ],
)
