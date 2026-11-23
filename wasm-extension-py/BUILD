load("@aspect_rules_py//py:defs.bzl", "py_library", "py_test")
load("//tools/sdk_generator:defs.bzl", "generate_extension_sdk")

generate_extension_sdk(
    name = "gen_py_sdk",
    lang = "python",
    out_api = "moosync_edk/generated_api.py",
    out_dispatcher = "moosync_edk/generated_dispatcher.py",
    proto = "//protos:extension_service_proto",
)

py_library(
    name = "moosync_edk",
    srcs = glob(["moosync_edk/**/*.py"]) + [
        "extism.py",
    ],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = [
        "@com_google_protobuf//:protobuf_python",
        "//protos:extension_service_py_proto",
        "//protos:extensions_py_proto",
        "//protos:moosync_python_root",
        "//protos:preferences_py_proto",
        "//protos:songs_py_proto",
        "//protos:themes_py_proto",
        "//protos:ui_py_proto",
    ],
)

py_test(
    name = "parse_lrc_test",
    srcs = ["tests/test_parse_lrc.py"],
    main = "tests/test_parse_lrc.py",
    deps = [
        ":moosync_edk",
    ],
)

py_test(
    name = "websocket_test",
    srcs = ["tests/test_websocket.py"],
    main = "tests/test_websocket.py",
    deps = [
        ":moosync_edk",
    ],
)

py_test(
    name = "process_test",
    srcs = ["tests/test_process.py"],
    main = "tests/test_process.py",
    deps = [
        ":moosync_edk",
    ],
)

genrule(
    name = "doc",
    srcs = glob(["moosync_edk/**/*.py"]) + [
        "extism.py",
        "//protos:extensions_py_proto",
        "//protos:preferences_py_proto",
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
    visibility = ["//docs:__pkg__"],
)
