load("@rules_go//go:def.bzl", "go_binary", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "gen_godoc_lib",
    srcs = ["main.go"],
    importpath = "github.com/Moosync/extensions-sdk/tools/gen_godoc",
)

go_binary(
    name = "gen_godoc",
    embed = [":gen_godoc_lib"],
)
