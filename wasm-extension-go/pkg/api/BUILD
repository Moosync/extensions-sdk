load("@rules_go//go:def.bzl", "go_library", "go_test")
load("//tools/sdk_generator:defs.bzl", "generate_extension_sdk")

generate_extension_sdk(
    name = "gen_go_sdk",
    lang = "go",
    out_api = "generated_api.go",
    out_dispatcher = "generated_exports.go",
    proto = "//protos:extension_service_proto",
)

exports_files([
    "api.go",
    "cache.go",
    "generated_api.go",
    "generated_exports.go",
    "platform.go",
    "socket.go",
    "websocket.go",
])

go_library(
    name = "api",
    srcs = [
        "api.go",
        "cache.go",
        "generated_api.go",
        "generated_exports.go",
        "platform.go",
        "socket.go",
        "websocket.go",
    ],
    importpath = "github.com/Moosync/extensions-sdk/wasm-extension-go/pkg/api",
    visibility = ["//visibility:public"],
    deps = [
        "//protos:extension_service_go_proto",
        "//protos:extensions_go_proto",
        "//protos:preferences_go_proto",
        "//protos:songs_go_proto",
        "//protos:themes_go_proto",
        "//protos:ui_go_proto",
        "@com_github_extism_go_pdk//:go_default_library",
        "@com_github_extism_go_pdk//http:go_default_library",
        "@org_golang_google_protobuf//proto:go_default_library",
        "@org_golang_google_protobuf//types/known/durationpb:go_default_library",
    ],
)

go_test(
    name = "api_test",
    srcs = ["api_test.go"],
    embed = [":api"],
)
