load("@rules_go//go:def.bzl", "go_binary", "go_library")

go_binary(
    name = "sample_extension",
    cgo = True,
    embed = [":sample_extension_lib"],
    goarch = "wasm",
    goos = "wasip1",
    linkmode = "c-shared",
    pure = "on",
    visibility = ["//visibility:public"],
)

go_library(
    name = "sample_extension_lib",
    srcs = ["main.go"],
    importpath = "github.com/Moosync/extensions-sdk/wasm-extension-go/examples/sample-extension",
    visibility = ["//visibility:private"],
    deps = [
        "//wasm-extension-go/pkg/api",
        "@com_github_extism_go_pdk//:go_default_library",
        "@moosync//core/types/protos:extensions_go_proto",
        "@moosync//core/types/protos:songs_go_proto",
        "@moosync//core/types/protos:ui_go_proto",
    ],
)
