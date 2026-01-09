"""
Wasm extension rules for TypeScript/JavaScript.
"""

load("@aspect_rules_rollup//rollup:defs.bzl", "rollup")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

def js_wasm_extension(name, srcs, deps = [], tsconfig = "tsconfig.json", rollup_config = "rollup.config.mjs", visibility = None):
    """
    Builds a Wasm extension from TypeScript sources.

    Args:
        name: The name of the target. The output will be name.wasm.
        srcs: Source files (.ts).
        deps: Dependencies.
        tsconfig: Path to tsconfig.json. Defaults to "tsconfig.json".
        rollup_config: Path to rollup config. Defaults to "rollup.config.mjs".
        visibility: Target visibility.
    """

    ts_lib_name = name + "_ts"
    bundle_name = name + "_bundle"
    out_dir = name + "_lib"

    # Compilation
    ts_project(
        name = ts_lib_name,
        srcs = srcs,
        declaration = True,
        out_dir = out_dir,
        tsconfig = tsconfig,
        deps = deps + [
            Label("//wasm-extension-js:node_modules/@extism/js-pdk"),
            Label("//wasm-extension-js:wasm_extension_js_lib"),
        ],
        visibility = visibility,
    )

    # Bundling
    rollup(
        name = bundle_name,
        entry_point = out_dir + "/src/index.js",
        format = "cjs",
        node_modules = Label("//wasm-extension-js:node_modules"),
        sourcemap = "false",
        config_file = rollup_config,
        deps = [
            ":" + ts_lib_name,
            Label("//wasm-extension-js:node_modules/@rollup/plugin-alias"),
            Label("//wasm-extension-js:node_modules/@rollup/plugin-commonjs"),
            Label("//wasm-extension-js:node_modules/@rollup/plugin-node-resolve"),
            Label("//wasm-extension-js:wasm_extension_js_lib"),
        ] + deps,
        visibility = visibility,
    )

    # Wasm generation
    native.genrule(
        name = name,
        srcs = [
            bundle_name + ".js",
            Label("//wasm-extension-js:src/plugin.d.ts"),
        ],
        outs = [name + ".wasm"],
        cmd = """
            $(location {}) $(location {bundle}.js) -i $(location {}) -o $@
        """.format(Label("//wasm-extension-js:extism_js_cli"), Label("//wasm-extension-js:src/plugin.d.ts"), bundle = bundle_name),
        tools = [Label("//wasm-extension-js:extism_js_cli")],
        visibility = visibility,
    )
