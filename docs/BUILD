load("@rules_rust_mdbook//:defs.bzl", "mdbook", "mdbook_server")
load("//docs:defs.bzl", "docs_site")

package(default_visibility = ["//visibility:public"])

exports_files([
    "book.toml",
    "mdbook-admonish.css",
    "tabs.css",
    "tabs.js",
])

mdbook(
    name = "book",
    book = "book.toml",
    plugins = [
        "//tools:mdbook_admonish",
        "//tools:mdbook_tabs",
    ],
    srcs = glob([
        "src/**/*.md",
        "*.css",
        "*.js",
    ]) + [
        "//wasm-extension-go/examples:main.go",
        "//wasm-extension-go/examples:BUILD",
        "//wasm-extension-rs/examples:src/lib.rs",
        "//wasm-extension-rs/examples:BUILD",
        "//wasm-extension-py/examples:main.py",
        "//wasm-extension-py/examples:BUILD",
        "//wasm-extension-js/examples:src/index.ts",
        "//wasm-extension-js/examples:BUILD",
    ],
)

mdbook_server(
    name = "book_server",
    book = ":book",
)

docs_site(
    name = "site",
    book = ":book",
    go_doc = "//wasm-extension-go:doc",
    index_html = "//:index.html",
    js_doc = "//wasm-extension-js:doc",
    py_doc = "//wasm-extension-py:doc",
    rust_doc = "//wasm-extension-rs:doc",
)

alias(
    name = "serve",
    actual = "//tools:serve",
)
