"""
Rules for building mdBook and aggregated documentation site.
"""

def _mdbook_impl(ctx):
    out_dir = ctx.actions.declare_directory(ctx.label.name)
    book_toml = ctx.file.book_toml
    srcs = ctx.files.srcs
    tools = [ctx.executable._mdbook, ctx.executable._mdbook_tabs, ctx.executable._mdbook_admonish]

    script = """#!/usr/bin/env bash
set -e

EXEC_ROOT="$(pwd)"
MDBOOK_BIN="$EXEC_ROOT/{mdbook}"
MDBOOK_TABS_BIN="$EXEC_ROOT/{mdbook_tabs}"
MDBOOK_ADMONISH_BIN="$EXEC_ROOT/{mdbook_admonish}"
OUT_DIR="$EXEC_ROOT/{out_dir}"

BIN_DIR="$(mktemp -d)"
BUILD_ROOT="$(mktemp -d)"
trap 'rm -rf "$BIN_DIR" "$BUILD_ROOT"' EXIT

ln -sf "$MDBOOK_TABS_BIN" "$BIN_DIR/mdbook-tabs"
ln -sf "$MDBOOK_ADMONISH_BIN" "$BIN_DIR/mdbook-admonish"

export PATH="$BIN_DIR:$PATH"

mkdir -p "$BUILD_ROOT/docs"
cp -rL docs/. "$BUILD_ROOT/docs/"

for lang_dir in wasm-extension-*; do
    if [ -d "$lang_dir/examples" ]; then
        mkdir -p "$BUILD_ROOT/$lang_dir/examples"
        cp -rL "$lang_dir/examples/." "$BUILD_ROOT/$lang_dir/examples/"
    fi
done

cd "$BUILD_ROOT/docs"
"$MDBOOK_BIN" build -d "$BUILD_ROOT/docs/book_out"

mkdir -p "$OUT_DIR"
if [ -d "$BUILD_ROOT/docs/book_out/html" ]; then
    cp -rL "$BUILD_ROOT/docs/book_out/html/." "$OUT_DIR/"
else
    cp -rL "$BUILD_ROOT/docs/book_out/." "$OUT_DIR/"
fi
""".format(
        mdbook = ctx.executable._mdbook.path,
        mdbook_tabs = ctx.executable._mdbook_tabs.path,
        mdbook_admonish = ctx.executable._mdbook_admonish.path,
        out_dir = out_dir.path,
    )

    ctx.actions.run_shell(
        inputs = depset(srcs + [book_toml]),
        outputs = [out_dir],
        tools = tools,
        command = script,
        mnemonic = "MdBookBuild",
    )

    return [DefaultInfo(files = depset([out_dir]))]

mdbook = rule(
    implementation = _mdbook_impl,
    attrs = {
        "book_toml": attr.label(allow_single_file = True, default = "//docs:book.toml"),
        "srcs": attr.label_list(allow_files = True),
        "_mdbook": attr.label(
            default = Label("@mdbook_tool//:mdbook"),
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
        "_mdbook_tabs": attr.label(
            default = Label("@host_crates//:mdbook-tabs__mdbook-tabs"),
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
        "_mdbook_admonish": attr.label(
            default = Label("@mdbook_admonish_tool//:mdbook-admonish"),
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
    },
)

def _wasi_platform_transition_impl(settings, attr):
    return {"//command_line_option:platforms": "@rules_rust//rust/platform:wasi"}

_wasi_platform_transition = transition(
    implementation = _wasi_platform_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

def _docs_site_impl(ctx):
    out_dir = ctx.actions.declare_directory(ctx.label.name)

    book = ctx.file.book
    rust_doc = ctx.files.rust_doc[0]
    go_doc = ctx.file.go_doc
    js_doc = ctx.file.js_doc
    py_doc = ctx.file.py_doc
    index_html = ctx.file.index_html

    script = """#!/usr/bin/env bash
set -e

mkdir -p "{out_dir}/book"
mkdir -p "{out_dir}/rust"
mkdir -p "{out_dir}/go"
mkdir -p "{out_dir}/js"
mkdir -p "{out_dir}/py"

cp -rL "{book}/." "{out_dir}/book/"
cp -rL "{rust_doc}/." "{out_dir}/rust/"
cp -rL "{go_doc}" "{out_dir}/go/index.html"
cp -rL "{js_doc}/." "{out_dir}/js/"
cp -rL "{py_doc}" "{out_dir}/py/index.html"
cp -L "{index_html}" "{out_dir}/index.html"
""".format(
        out_dir = out_dir.path,
        book = book.path,
        rust_doc = rust_doc.path,
        go_doc = go_doc.path,
        js_doc = js_doc.path,
        py_doc = py_doc.path,
        index_html = index_html.path,
    )

    ctx.actions.run_shell(
        inputs = [book, rust_doc, go_doc, js_doc, py_doc, index_html],
        outputs = [out_dir],
        command = script,
        mnemonic = "DocsSite",
    )

    return [DefaultInfo(files = depset([out_dir]))]

docs_site = rule(
    implementation = _docs_site_impl,
    attrs = {
        "book": attr.label(allow_single_file = True, mandatory = True),
        "rust_doc": attr.label(
            allow_files = True,
            mandatory = True,
            cfg = _wasi_platform_transition,
        ),
        "go_doc": attr.label(allow_single_file = True, mandatory = True),
        "js_doc": attr.label(allow_single_file = True, mandatory = True),
        "py_doc": attr.label(allow_single_file = True, mandatory = True),
        "index_html": attr.label(allow_single_file = True, default = "//:index.html"),
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
    },
)
