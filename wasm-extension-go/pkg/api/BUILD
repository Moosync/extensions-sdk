load("@rules_go//go:def.bzl", "go_library")

exports_files(["api.go", "exports.go"])

go_library(
    name = "api",
    srcs = [
        "api.go",
        "exports.go",
    ],
    importpath = "github.com/Moosync/extensions-sdk/wasm-extension-go/pkg/api",
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_extism_go_pdk//:go_default_library",
        "@com_github_extism_go_pdk//http:go_default_library",
        "//protos:extensions_go_proto",
        "//protos:songs_go_proto",
        "//protos:themes_go_proto",
        "//protos:ui_go_proto",
        "@org_golang_google_protobuf//proto:go_default_library",
        "@org_golang_google_protobuf//types/known/durationpb:go_default_library",
    ],
)
