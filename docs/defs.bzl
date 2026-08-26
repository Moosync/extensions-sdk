"""
Rules for building aggregated documentation site.
"""

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
