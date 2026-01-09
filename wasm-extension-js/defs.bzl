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
            "//wasm-extension-js:node_modules/@extism/js-pdk",
            "//wasm-extension-js:wasm_extension_js_lib",
        ],
        visibility = visibility,
    )

    # Bundling
    rollup(
        name = bundle_name,
        entry_point = out_dir + "/src/index.js",
        format = "cjs",
        node_modules = "//wasm-extension-js:node_modules",
        sourcemap = "false",
        config_file = rollup_config,
        deps = [
            ":" + ts_lib_name,
            "//wasm-extension-js:node_modules/@rollup/plugin-alias",
            "//wasm-extension-js:node_modules/@rollup/plugin-commonjs",
            "//wasm-extension-js:node_modules/@rollup/plugin-node-resolve",
            "//wasm-extension-js:wasm_extension_js_lib",
        ] + deps,
        visibility = visibility,
    )

    # Wasm generation
    native.genrule(
        name = name,
        srcs = [
            bundle_name + ".js",
            "//wasm-extension-js:src/plugin.d.ts",
        ],
        outs = [name + ".wasm"],
        cmd = """
            $(location //wasm-extension-js:extism_js_cli) $(location {bundle}.js) -i $(location //wasm-extension-js:src/plugin.d.ts) -o $@
        """.format(bundle = bundle_name),
        tools = ["//wasm-extension-js:extism_js_cli"],
        visibility = visibility,
    )
