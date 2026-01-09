"""
Wasm extension rules for Go.
"""

load("@rules_go//go:def.bzl", "go_binary", "go_library")

def go_extension(name, srcs, deps = [], visibility = None, **kwargs):
    """
    Builds a Wasm extension from Go sources.

    Args:
        name: The name of the target.
        srcs: Source files.
        deps: Dependencies.
        visibility: Target visibility.
        **kwargs: Additional arguments to pass to go_binary.
    """
    go_library(
        name = name + "_lib",
        srcs = srcs,
        deps = deps + [
            Label("//wasm-extension-go/pkg/api"),
            "@com_github_extism_go_pdk//:go_default_library",
            "@moosync//core/types/protos:extensions_go_proto",
            "@moosync//core/types/protos:songs_go_proto",
            "@moosync//core/types/protos:ui_go_proto",
        ],
        importpath = "moosync/" + name,
        tags = ["manual"],
        visibility = visibility,
    )

    go_binary(
        name = name,
        srcs = srcs,
        deps = deps + [
            Label("//wasm-extension-go/pkg/api"),
            "@com_github_extism_go_pdk//:go_default_library",
            "@moosync//core/types/protos:extensions_go_proto",
            "@moosync//core/types/protos:songs_go_proto",
            "@moosync//core/types/protos:ui_go_proto",
        ],
        goos = "wasip1",
        goarch = "wasm",
        linkmode = "c-shared",
        cgo = True,
        pure = "on",
        visibility = visibility,
        **kwargs
    )
