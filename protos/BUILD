load("@com_google_protobuf//bazel:py_proto_library.bzl", "py_proto_library")
load("@rules_go//proto:def.bzl", "go_proto_library")
load("@rules_proto//proto:defs.bzl", "proto_library")
load("@rules_python//python:defs.bzl", "py_library")
load("@rules_rust_prost//:defs.bzl", "rust_prost_library")

exports_files(
    ["extension_service.proto"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "moosync_python_root",
    imports = [
        ".",
        "..",
        "../../moosync+",
        "../moosync+",
    ],
    visibility = ["//visibility:public"],
)

# -------------------------------------------------------------
# Protobuf definitions directly from Moosync
# -------------------------------------------------------------

alias(
    name = "preferences_proto",
    actual = "@moosync//core/types/protos:preferences_proto",
    visibility = ["//visibility:public"],
)

alias(
    name = "ui_proto",
    actual = "@moosync//core/types/protos:ui_proto",
    visibility = ["//visibility:public"],
)

alias(
    name = "songs_proto",
    actual = "@moosync//core/types/protos:songs_proto",
    visibility = ["//visibility:public"],
)

alias(
    name = "themes_proto",
    actual = "@moosync//core/types/protos:themes_proto",
    visibility = ["//visibility:public"],
)

alias(
    name = "extensions_proto",
    actual = "@moosync//core/types/protos:extensions_proto",
    visibility = ["//visibility:public"],
)

proto_library(
    name = "extension_service_proto",
    srcs = ["extension_service.proto"],
    import_prefix = "core/types/protos",
    strip_import_prefix = "/protos",
    visibility = ["//visibility:public"],
    deps = [
        "@com_google_protobuf//:descriptor_proto",
        "@com_google_protobuf//:duration_proto",
        "@com_google_protobuf//:timestamp_proto",
        "@moosync//core/types/protos:extensions_proto",
    ],
)

# -------------------------------------------------------------
# Language-specific targets
# -------------------------------------------------------------

alias(
    name = "ui_rs",
    actual = "@moosync//core/types/protos:ui_rs",
    visibility = ["//visibility:public"],
)

alias(
    name = "extensions_rs",
    actual = "@moosync//core/types/protos:extensions_rs",
    visibility = ["//visibility:public"],
)

rust_prost_library(
    name = "extension_service_rs",
    proto = ":extension_service_proto",
    visibility = ["//visibility:public"],
)

alias(
    name = "songs_rs",
    actual = "@moosync//core/types/protos:songs_rs",
    visibility = ["//visibility:public"],
)

rust_prost_library(
    name = "duration_rs",
    proto = "@com_google_protobuf//:duration_proto",
    visibility = ["//visibility:public"],
)

alias(
    name = "themes_rs",
    actual = "@moosync//core/types/protos:themes_rs",
    visibility = ["//visibility:public"],
)

alias(
    name = "preferences_rs",
    actual = "@moosync//core/types/protos:preferences_rs",
    visibility = ["//visibility:public"],
)

go_proto_library(
    name = "preferences_go_proto",
    importpath = "github.com/moosync/moosync/types/preferences",
    protos = [":preferences_proto"],
    visibility = ["//visibility:public"],
)

go_proto_library(
    name = "ui_go_proto",
    importpath = "github.com/moosync/moosync/types/ui",
    protos = [":ui_proto"],
    visibility = ["//visibility:public"],
    deps = [":preferences_go_proto"],
)

go_proto_library(
    name = "songs_go_proto",
    importpath = "github.com/moosync/moosync/types/songs",
    protos = [":songs_proto"],
    visibility = ["//visibility:public"],
)

go_proto_library(
    name = "extensions_go_proto",
    importpath = "github.com/moosync/moosync/types/extensions",
    protos = [":extensions_proto"],
    visibility = ["//visibility:public"],
    deps = [
        ":preferences_go_proto",
        ":songs_go_proto",
        ":ui_go_proto",
    ],
)

go_proto_library(
    name = "extension_service_go_proto",
    importpath = "github.com/moosync/moosync/types/extension_service",
    protos = [":extension_service_proto"],
    visibility = ["//visibility:public"],
    deps = [
        ":extensions_go_proto",
        ":preferences_go_proto",
        ":songs_go_proto",
    ],
)

go_proto_library(
    name = "themes_go_proto",
    importpath = "github.com/moosync/moosync/types/themes",
    protos = [":themes_proto"],
    visibility = ["//visibility:public"],
    deps = [":songs_go_proto"],
)

py_proto_library(
    name = "preferences_py_proto",
    visibility = ["//visibility:public"],
    deps = [":preferences_proto"],
)

py_proto_library(
    name = "extensions_py_proto",
    visibility = ["//visibility:public"],
    deps = [":extensions_proto"],
)

py_proto_library(
    name = "extension_service_py_proto",
    visibility = ["//visibility:public"],
    deps = [":extension_service_proto"],
)

py_proto_library(
    name = "songs_py_proto",
    visibility = ["//visibility:public"],
    deps = [":songs_proto"],
)

py_proto_library(
    name = "ui_py_proto",
    visibility = ["//visibility:public"],
    deps = [":ui_proto"],
)

py_proto_library(
    name = "themes_py_proto",
    visibility = ["//visibility:public"],
    deps = [":themes_proto"],
)
