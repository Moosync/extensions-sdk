load("@aspect_rules_js//js:defs.bzl", "js_library", "js_test")
load("@aspect_rules_js//npm:defs.bzl", "npm_package")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@sdk_npm//:defs.bzl", "npm_link_all_packages")
load("@sdk_npm//wasm-extension-js:typedoc/package_json.bzl", typedoc_bin = "bin")

typedoc_bin.typedoc(
    name = "doc",
    srcs = glob(["src/**/*.ts"]) + [
        "tsconfig.json",
        ":generate_ts_protos",
        ":node_modules/@bufbuild/protobuf",
        ":node_modules/@extism/js-pdk",
        ":node_modules/@types/node",
        ":node_modules/@whatwg-node/fetch",
        ":node_modules/fast-text-encoding",
        ":node_modules/ts-proto",
        ":node_modules/typescript",
    ],
    args = [
        "--entryPoints",
        "wasm-extension-js/src/index.ts",
        "--out",
        "wasm-extension-js/doc",
        "--tsconfig",
        "wasm-extension-js/tsconfig.json",
    ],
    out_dirs = ["doc"],
    visibility = ["//docs:__pkg__"],
)

exports_files([
    "src/plugin.d.ts",
    "defs.bzl",
    "rollup.config.mjs",
    "tsconfig.json",
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

genrule(
    name = "generate_ts_protos",
    srcs = [
        "@moosync//core/types/protos:preferences.proto",
        "@moosync//core/types/protos:ui.proto",
        "@moosync//core/types/protos:songs.proto",
        "@moosync//core/types/protos:themes.proto",
        "@moosync//core/types/protos:extensions.proto",
        "//protos:extension_service.proto",
        "@com_google_protobuf//:descriptor_proto_srcs",
        "@com_google_protobuf//:well_known_type_protos",
        ":node_modules/@bufbuild/protoc-gen-es/dir",
    ],
    outs = [
        "src/protos/extension_service_pb.d.ts",
        "src/protos/extension_service_pb.js",
        "src/protos/extensions_pb.d.ts",
        "src/protos/extensions_pb.js",
        "src/protos/preferences_pb.d.ts",
        "src/protos/preferences_pb.js",
        "src/protos/songs_pb.d.ts",
        "src/protos/songs_pb.js",
        "src/protos/ui_pb.d.ts",
        "src/protos/ui_pb.js",
        "src/protos/themes_pb.d.ts",
        "src/protos/themes_pb.js",
    ],
    cmd = """
        OUT_DIR=$(@D)/src/protos
        mkdir -p $$OUT_DIR

        PREF="$(location @moosync//core/types/protos:preferences.proto)"
        MOOSYNC_ROOT="$${PREF%/core/types/protos/preferences.proto}"

        WKTS="$(locations @com_google_protobuf//:well_known_type_protos)"
        FIRST_WKT="$${WKTS%% *}"
        PROTO_ROOT="$${FIRST_WKT%/google/protobuf/*}"

        EXT_SRV="$(location //protos:extension_service.proto)"
        EXT_DIR="$${EXT_SRV%/extension_service.proto}"
        EXT_ROOT="$${EXT_DIR%/protos}"
        if [ -z "$$EXT_ROOT" ]; then
            EXT_ROOT="."
        fi

        $(location @com_google_protobuf//:protoc) \
            --plugin=protoc-gen-es=$(location :node_modules/@bufbuild/protoc-gen-es/dir)/bin/protoc-gen-es \
            --es_out=$$OUT_DIR \
            --es_opt=import_extension=js \
            -I"$$EXT_ROOT" \
            -I"$$MOOSYNC_ROOT" \
            -I"$$PROTO_ROOT" \
            $(location @moosync//core/types/protos:preferences.proto) \
            $(location @moosync//core/types/protos:ui.proto) \
            $(location @moosync//core/types/protos:songs.proto) \
            $(location @moosync//core/types/protos:themes.proto) \
            $(location @moosync//core/types/protos:extensions.proto) \
            "$$EXT_SRV"

        find "$$OUT_DIR" -mindepth 2 -type f -exec mv -f {} "$$OUT_DIR/" \\;
        find "$$OUT_DIR" -mindepth 1 -type d -exec rm -rf {} +
    """,
    tools = ["@com_google_protobuf//:protoc"],
)

genrule(
    name = "protos_to_lib",
    srcs = [":generate_ts_protos"],
    outs = [
        "lib/src/protos/extension_service_pb.d.ts",
        "lib/src/protos/extension_service_pb.js",
        "lib/src/protos/extension_service_pbjs",
        "lib/src/protos/extensions_pb.d.ts",
        "lib/src/protos/extensions_pb.js",
        "lib/src/protos/extensions_pbjs",
        "lib/src/protos/preferences_pb.d.ts",
        "lib/src/protos/preferences_pb.js",
        "lib/src/protos/preferences_pbjs",
        "lib/src/protos/songs_pb.d.ts",
        "lib/src/protos/songs_pb.js",
        "lib/src/protos/songs_pbjs",
        "lib/src/protos/ui_pb.d.ts",
        "lib/src/protos/ui_pb.js",
        "lib/src/protos/ui_pbjs",
        "lib/src/protos/themes_pb.d.ts",
        "lib/src/protos/themes_pb.js",
        "lib/src/protos/themes_pbjs",
    ],
    cmd = """
        mkdir -p $(@D)/lib/src/protos
        cp -f $(SRCS) $(@D)/lib/src/protos/
        for f in $(@D)/lib/src/protos/*_pb.js; do
            cp -f "$$f" "$${f%.js}js"
        done
    """,
    visibility = ["//visibility:public"],
)

filegroup(
    name = "proto_dts_lib",
    srcs = [":protos_to_lib"],
    visibility = ["//visibility:public"],
)

js_library(
    name = "protos_js_lib",
    srcs = [":proto_dts_lib"],
    types = [":proto_dts_lib"],
    visibility = ["//visibility:public"],
)

ts_project(
    name = "wasm_extension_js",
    srcs = glob(["src/**/*.ts"]) + [
        ":src/protos/extension_service_pb.d.ts",
        ":src/protos/extension_service_pb.js",
        ":src/protos/extensions_pb.d.ts",
        ":src/protos/extensions_pb.js",
        ":src/protos/preferences_pb.d.ts",
        ":src/protos/preferences_pb.js",
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
        ":node_modules/@types/node",
        ":node_modules/@whatwg-node/fetch",
        ":node_modules/fast-text-encoding",
        ":node_modules/ts-proto",
    ],
)

js_library(
    name = "wasm_extension_js_lib",
    srcs = [
        "package.json",
        "rollup.config.mjs",
        "tsconfig.json",
    ],
    visibility = ["//visibility:public"],
    deps = [
        ":node_modules",
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
    visibility = ["//visibility:private"],
)


js_test(
    name = "parse_lrc_test",
    data = [
        ":protos_to_lib",
        ":wasm_extension_js",
        ":node_modules/@bufbuild/protobuf",
        ":node_modules/@extism/js-pdk",
        ":node_modules/fast-text-encoding",
        ":node_modules/@whatwg-node/fetch",
        ":node_modules/ts-proto",
    ],
    entry_point = "tests/parse_lrc_test.mjs",
)
