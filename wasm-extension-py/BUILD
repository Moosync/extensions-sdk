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

genrule(
    name = "doc",
    srcs = glob(["moosync_edk/**/*.py"]) + [
        "extism.py",
        "//protos:extensions_py_proto",
        "//protos:songs_py_proto",
        "//protos:themes_py_proto",
        "//protos:ui_py_proto",
    ],
    outs = ["index.html"],
    cmd = """
BUILD_DIR="$$(mktemp -d)"
trap 'rm -rf "$$BUILD_DIR"' EXIT

mkdir -p "$$BUILD_DIR/proto_root/core/types/protos"
cp -rL wasm-extension-py/moosync_edk "$$BUILD_DIR/"
cp -f wasm-extension-py/extism.py "$$BUILD_DIR/extism.py"

for f in $$(find -L . -name "*_pb2.py"); do
    cp -f --no-preserve=mode "$$f" "$$BUILD_DIR/proto_root/core/types/protos/" 2>/dev/null || true
done
chmod -R u+w "$$BUILD_DIR"

export PYTHONPATH="$$BUILD_DIR:$$BUILD_DIR/proto_root:$${PYTHONPATH:-}"
$(location //tools:pdoc) --output-dir "$$BUILD_DIR/out" moosync_edk

if [ -f "$$BUILD_DIR/out/moosync_edk.html" ]; then
    cp "$$BUILD_DIR/out/moosync_edk.html" "$@"
elif [ -f "$$BUILD_DIR/out/moosync_edk/index.html" ]; then
    cp "$$BUILD_DIR/out/moosync_edk/index.html" "$@"
else
    cp "$$BUILD_DIR/out/index.html" "$@"
fi
""",
    tools = ["//tools:pdoc"],
    visibility = ["//visibility:public"],
)
