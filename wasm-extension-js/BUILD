load("@aspect_rules_js//js:defs.bzl", "js_library")
load("@aspect_rules_js//npm:defs.bzl", "npm_package")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@sdk_npm//:defs.bzl", "npm_link_all_packages")

package(default_visibility = ["//visibility:public"])

exports_files([
    "src/plugin.d.ts",
    "defs.bzl",
])

npm_package(
    name = "wasm_extension_js_pkg",
    srcs = [
        "package.json",
        ":protos_js_lib",
        ":wasm_extension_js",
    ],
    visibility = ["//visibility:public"],
)

npm_link_all_packages(name = "node_modules")

ts_project(
    name = "wasm_extension_js",
    srcs = glob(["src/**/*.ts"]) + [
        ":src/protos/extensions_pb.d.ts",
        ":src/protos/extensions_pb.js",
        ":src/protos/songs_pb.d.ts",
        ":src/protos/songs_pb.js",
        ":src/protos/themes_pb.d.ts",
        ":src/protos/themes_pb.js",
        ":src/protos/ui_pb.d.ts",
        ":src/protos/ui_pb.js",
    ],
    declaration = True,
    declaration_map = True,
    emit_declaration_only = False,
    out_dir = "lib",
    tsconfig = "tsconfig.json",
    deps = [
        ":node_modules/@bufbuild/protobuf",
        ":node_modules/@extism/js-pdk",
        ":node_modules/ts-proto",
    ],
)

filegroup(
    name = "proto_types",
    srcs = [
        "@moosync//core/types/protos:extensions_ts_proto",
        "@moosync//core/types/protos:songs_ts_proto",
        "@moosync//core/types/protos:themes_ts_proto",
        "@moosync//core/types/protos:ui_ts_proto",
    ],
    output_group = "types",
)

genrule(
    name = "copy_protos",
    srcs = [
        "@moosync//core/types/protos:extensions_ts_proto",
        "@moosync//core/types/protos:songs_ts_proto",
        "@moosync//core/types/protos:ui_ts_proto",
        "@moosync//core/types/protos:themes_ts_proto",
        ":proto_types",
    ],
    outs = [
        "src/protos/extensions_pb.d.ts",
        "src/protos/extensions_pb.js",
        "src/protos/songs_pb.d.ts",
        "src/protos/songs_pb.js",
        "src/protos/ui_pb.d.ts",
        "src/protos/ui_pb.js",
        "src/protos/themes_pb.d.ts",
        "src/protos/themes_pb.js",
    ],
    cmd = "mkdir -p $(@D)/src/protos && cp -f $(SRCS) $(@D)/src/protos/",
)

genrule(
    name = "copy_protos_to_lib",
    srcs = [
        "@moosync//core/types/protos:extensions_ts_proto",
        "@moosync//core/types/protos:songs_ts_proto",
        "@moosync//core/types/protos:ui_ts_proto",
        "@moosync//core/types/protos:themes_ts_proto",
        ":proto_types",
    ],
    outs = [
        "lib/src/protos/extensions_pb.d.ts",
        "lib/src/protos/extensions_pb.js",
        "lib/src/protos/songs_pb.d.ts",
        "lib/src/protos/songs_pb.js",
        "lib/src/protos/ui_pb.d.ts",
        "lib/src/protos/ui_pb.js",
        "lib/src/protos/themes_pb.d.ts",
        "lib/src/protos/themes_pb.js",
    ],
    cmd = "mkdir -p $(@D)/lib/src/protos && cp $(SRCS) $(@D)/lib/src/protos/",
    visibility = ["//visibility:public"],
)

filegroup(
    name = "proto_dts_lib",
    srcs = [":copy_protos_to_lib"],
    visibility = ["//visibility:public"],
)

js_library(
    name = "protos_js_lib",
    srcs = [":proto_dts_lib"],
    types = [":proto_dts_lib"],
    visibility = ["//visibility:public"],
)

js_library(
    name = "wasm_extension_js_lib",
    srcs = ["package.json"],
    visibility = ["//visibility:public"],
    deps = [
        ":protos_js_lib",
        ":wasm_extension_js",
    ],
)

genrule(
    name = "extism_js_cli",
    srcs = ["@extism_js_binary_download//file"],
    outs = ["extism-js"],
    cmd = "gunzip -c $< > $@ && chmod +x $@",
    executable = True,
    visibility = ["//visibility:public"],
)

genrule(
    name = "extism_js_help",
    outs = ["help.txt"],
    cmd = """
        BINS="$(locations @binaryen_tool//:bin_files)"
        FIRST_BIN=$${BINS%% *}
        BIN_DIR=$$(dirname $$FIRST_BIN)
        export PATH=$$PATH:$$BIN_DIR
        $(location :extism_js_cli) --help > $@ || true
    """,
    tools = [
        ":extism_js_cli",
        "@binaryen_tool//:bin_files",
    ],
    visibility = ["//visibility:public"],
)
