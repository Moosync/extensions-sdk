load("@aspect_rules_py//py:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "moosync_edk",
    srcs = glob(["moosync_edk/**/*.py"]),
    imports = ["."],
    deps = [
        "@com_google_protobuf//:protobuf_python",
        "@moosync//core/types/protos:extensions_py_proto",
        "@moosync//core/types/protos:songs_py_proto",
        "@moosync//core/types/protos:themes_py_proto",
        "@moosync//core/types/protos:ui_py_proto",
    ],
)
