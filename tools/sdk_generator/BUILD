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
    data = [
        ":all_templates",
        "//protos:extension_service.proto",
    ],
    main = "generator.py",
    deps = [
        "@com_google_protobuf//:protobuf_python",
        "@pip_deps//jinja2:pkg",
    ],
)

py_binary(
    name = "update",
    srcs = ["generator.py"],
    args = [
        "--all",
        "--templates-dir",
        "tools/sdk_generator/templates",
        "--descriptor-sets",
        "$(rootpath //protos:extension_service_proto)",
        "$(rootpath //protos:extensions_proto)",
        "$(rootpath //protos:preferences_proto)",
        "$(rootpath //protos:songs_proto)",
        "$(rootpath //protos:ui_proto)",
        "$(rootpath @com_google_protobuf//:timestamp_proto)",
    ],
    data = [
        ":all_templates",
        "//protos:extension_service.proto",
        "//protos:extension_service_proto",
        "//protos:extensions_proto",
        "//protos:preferences_proto",
        "//protos:songs_proto",
        "//protos:ui_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
    main = "generator.py",
    deps = [
        "@com_google_protobuf//:protobuf_python",
        "@pip_deps//jinja2:pkg",
    ],
)

py_test(
    name = "generator_unit_test",
    srcs = ["generator_test.py"],
    data = [
        ":all_templates",
        ":generator",
        "//protos:extension_service.proto",
        "//protos:extension_service_proto",
        "//protos:extensions_proto",
        "//protos:preferences_proto",
        "//protos:songs_proto",
        "//protos:ui_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
    main = "generator_test.py",
    deps = [
        ":generator",
        "@com_google_protobuf//:protobuf_python",
        "@pip_deps//jinja2:pkg",
    ],
)
