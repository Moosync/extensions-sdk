load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_test")

package(default_visibility = ["//visibility:public"])

exports_files([
    "generator.py",
    "defs.bzl",
])

filegroup(
    name = "all_templates",
    srcs = glob(["templates/**"]),
)

filegroup(
    name = "templates_marker",
    srcs = ["templates/marker.txt"],
)

py_binary(
    name = "generator",
    srcs = ["generator.py"],
    data = [":all_templates"],
    main = "generator.py",
    deps = [
        "@com_google_protobuf//:protobuf_python",
        "@pip_deps//jinja2:pkg",
    ],
)

py_test(
    name = "generator_test",
    srcs = ["generator_test.py"],
    data = [
        ":all_templates",
        ":generator",
        "//protos:extension_service_proto",
        "//protos:extensions_proto",
        "//protos:preferences_proto",
        "//protos:songs_proto",
        "//protos:ui_proto",
    ],
    main = "generator_test.py",
    deps = [
        ":generator",
        "@com_google_protobuf//:protobuf_python",
        "@pip_deps//jinja2:pkg",
    ],
)
