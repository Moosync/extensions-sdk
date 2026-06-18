load("@aspect_rules_ts//ts:proto.bzl", "ts_proto_library")
load("@com_google_protobuf//bazel:py_proto_library.bzl", "py_proto_library")
load("@proto_npm//:defs.bzl", "npm_link_all_packages")
load("@rules_go//proto:def.bzl", "go_proto_library")
load("@rules_proto//proto:defs.bzl", "proto_library")
load("@rules_python//python:defs.bzl", "py_library")
load("@rules_rust_prost//:defs.bzl", "rust_prost_library")

package(default_visibility = ["//visibility:public"])

npm_link_all_packages(name = "node_modules")

py_library(
    name = "moosync_python_root",
    imports = ["."],
    visibility = ["//visibility:public"],
)

# -------------------------------------------------------------
# Genrules to copy .proto source files from external workspace @moosync
# -------------------------------------------------------------

genrule(
    name = "copy_ui_proto",
    srcs = ["@moosync//core/types/protos:ui.proto"],
    outs = ["ui.proto"],
    cmd = "cp $< $@",
)

genrule(
    name = "copy_songs_proto",
    srcs = ["@moosync//core/types/protos:songs.proto"],
    outs = ["songs.proto"],
    cmd = "cp $< $@",
)

genrule(
    name = "copy_themes_proto",
    srcs = ["@moosync//core/types/protos:themes.proto"],
    outs = ["themes.proto"],
    cmd = "cp $< $@",
)

genrule(
    name = "copy_extensions_proto",
    srcs = ["@moosync//core/types/protos:extensions.proto"],
    outs = ["extensions.proto"],
    cmd = "cp $< $@",
)

# -------------------------------------------------------------
# Local proto_library targets
# -------------------------------------------------------------

proto_library(
    name = "ui_proto",
    srcs = ["ui.proto"],
    import_prefix = "core/types/protos",
    strip_import_prefix = "/protos",
    visibility = ["//visibility:public"],
    deps = [
        "@com_google_protobuf//:struct_proto",
    ],
)

proto_library(
    name = "songs_proto",
    srcs = ["songs.proto"],
    import_prefix = "core/types/protos",
    strip_import_prefix = "/protos",
    visibility = ["//visibility:public"],
    deps = [
        "@com_google_protobuf//:duration_proto",
    ],
)

proto_library(
    name = "themes_proto",
    srcs = ["themes.proto"],
    import_prefix = "core/types/protos",
    strip_import_prefix = "/protos",
    visibility = ["//visibility:public"],
    deps = [":songs_proto"],
)

proto_library(
    name = "extensions_proto",
    srcs = ["extensions.proto"],
    import_prefix = "core/types/protos",
    strip_import_prefix = "/protos",
    visibility = ["//visibility:public"],
    deps = [
        ":songs_proto",
        ":ui_proto",
        "@com_google_protobuf//:duration_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:struct_proto",
    ],
)

# -------------------------------------------------------------
# Language-specific targets
# -------------------------------------------------------------

rust_prost_library(
    name = "ui_rs",
    proto = ":ui_proto",
    visibility = ["//visibility:public"],
)

rust_prost_library(
    name = "extensions_rs",
    proto = ":extensions_proto",
    visibility = ["//visibility:public"],
)

rust_prost_library(
    name = "songs_rs",
    proto = ":songs_proto",
    visibility = ["//visibility:public"],
)

rust_prost_library(
    name = "duration_rs",
    proto = "@com_google_protobuf//:duration_proto",
    visibility = ["//visibility:public"],
)

rust_prost_library(
    name = "themes_rs",
    proto = ":themes_proto",
    visibility = ["//visibility:public"],
)

go_proto_library(
    name = "ui_go_proto",
    importpath = "github.com/moosync/moosync/types/ui",
    protos = [":ui_proto"],
    visibility = ["//visibility:public"],
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
        ":songs_go_proto",
        ":ui_go_proto",
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
    name = "extensions_py_proto",
    visibility = ["//visibility:public"],
    deps = [":extensions_proto"],
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

ts_proto_library(
    name = "extensions_ts_proto",
    copy_files = False,
    node_modules = ":node_modules",
    proto = ":extensions_proto",
    proto_srcs = ["extensions.proto"],
    protoc_gen_options = {"import_extension": "js"},
    visibility = ["//visibility:public"],
)

ts_proto_library(
    name = "songs_ts_proto",
    copy_files = False,
    node_modules = ":node_modules",
    proto = ":songs_proto",
    proto_srcs = ["songs.proto"],
    visibility = ["//visibility:public"],
)

ts_proto_library(
    name = "ui_ts_proto",
    copy_files = False,
    node_modules = ":node_modules",
    proto = ":ui_proto",
    proto_srcs = ["ui.proto"],
    visibility = ["//visibility:public"],
)

ts_proto_library(
    name = "themes_ts_proto",
    copy_files = False,
    node_modules = ":node_modules",
    proto = ":themes_proto",
    proto_srcs = ["themes.proto"],
    visibility = ["//visibility:public"],
)
