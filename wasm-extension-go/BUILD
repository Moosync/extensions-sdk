load("@gazelle//:def.bzl", "gazelle")

package(default_visibility = ["//visibility:public"])

# gazelle:prefix github.com/Moosync/extensions-sdk/wasm-extension-go
gazelle(name = "gazelle")

genrule(
    name = "doc",
    srcs = [
        "//wasm-extension-go/pkg/api:api.go",
        "//wasm-extension-go/pkg/api:exports.go",
    ],
    outs = ["index.html"],
    cmd = "$(location //tools/gen_godoc) -src_dir wasm-extension-go/pkg/api -out_dir $(@D) -import_path github.com/Moosync/extensions-sdk/wasm-extension-go/pkg/api",
    tools = ["//tools/gen_godoc"],
    visibility = ["//visibility:public"],
)
