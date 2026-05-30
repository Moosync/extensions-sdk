load("@aspect_rules_py//py:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "moosync_edk",
    srcs = glob(["moosync_edk/**/*.py"]),
    imports = ["."],
    deps = [
        "@com_google_protobuf//:protobuf_python",
        "//protos:extensions_py_proto",
        "//protos:songs_py_proto",
        "//protos:themes_py_proto",
        "//protos:ui_py_proto",
    ],
)
