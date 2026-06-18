"""
Wasm extension rules for TypeScript/JavaScript.
"""

load("@aspect_rules_rollup//rollup:defs.bzl", "rollup")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("//:package_json.bzl", "generate_package_json")
load("//:package_extension.bzl", "package_extension")

def js_wasm_extension(
        name,
        srcs,
        deps = [],
        data = [],
        tsconfig = Label("//wasm-extension-js:tsconfig.json"),
        rollup_config = Label("//wasm-extension-js:rollup.config.mjs"),
        visibility = None,
        display_name = None,
        package_name = None,
        version = None,
        icon = None,
        allowed_hosts = None,
        allowed_paths = None):
    """
    Builds a Wasm extension from TypeScript sources.

    Args:
        name: The name of the target. The output will be name.wasm.
        srcs: Source files (.ts).
        deps: Dependencies.
        data: Data dependencies.
        tsconfig: Path to tsconfig.json. Defaults to "tsconfig.json".
        rollup_config: Path to rollup config. Defaults to "rollup.config.mjs".
        visibility: Target visibility.
        display_name: Display name of the extension.
        package_name: Package name of the extension (mapped to name in json).
        version: Version of the extension.
        icon: Icon of the extension. Can be file path or label.
        allowed_hosts: List of allowed hosts.
        allowed_paths: Dict of allowed paths.
    """

    pkg_json_targets = generate_package_json(
        name = name,
        display_name = display_name,
        package_name = package_name,
        version = version,
        icon = icon,
        allowed_hosts = allowed_hosts,
        allowed_paths = allowed_paths,
        data = data,
        visibility = visibility,
        wasm_target = ":" + name + "_wasm",
    )

    ts_lib_name = name + "_ts"
    bundle_name = name + "_bundle"
    out_dir = name + "_lib"

    # Copy config files to the local package output tree to avoid copy_to_bin external repository issues
    tsconfig_local = name + "_tsconfig.json"
    native.genrule(
        name = name + "_copy_tsconfig",
        srcs = [tsconfig],
        outs = [tsconfig_local],
        cmd = 'sed \'s#"outDir": "./lib"#"outDir": "./{out_dir}"#g\' $< > $@'.format(out_dir = out_dir),
    )

    rollup_config_local = name + "_rollup.config.mjs"
    native.genrule(
        name = name + "_copy_rollup_config",
        srcs = [rollup_config],
        outs = [rollup_config_local],
        cmd = "cp $< $@",
    )

    # Compilation
    ts_project(
        name = ts_lib_name,
        srcs = srcs,
        declaration = True,
        declaration_map = True,
        out_dir = out_dir,
        tsconfig = ":" + tsconfig_local,
        deps = deps + [
            Label("//wasm-extension-js:node_modules/@extism/js-pdk"),
            Label("//wasm-extension-js:wasm_extension_js_lib"),
        ],
        data = data,
        visibility = visibility,
    )
    # Bundling
    rollup(
        name = bundle_name,
        entry_point = out_dir + "/src/index.js",
        format = "cjs",
        node_modules = Label("//wasm-extension-js:node_modules"),
        sourcemap = "false",
        config_file = ":" + rollup_config_local,
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
        name = name + "_wasm",
        srcs = [
            bundle_name + ".js",
            Label("//wasm-extension-js:src/plugin.d.ts"),
            Label("@binaryen_tool//:bin_files"),
        ],
        outs = [name + ".wasm"],
        cmd = """
            BINS="$(locations {})"
            FIRST_BIN=$${{BINS%% *}}
            BIN_DIR=$$(dirname $$FIRST_BIN)
            export PATH=$$PATH:$$BIN_DIR
            $(location {}) $(location {bundle}.js) -i $(location {}) -o $@
        """.format(
            Label("@binaryen_tool//:bin_files"),
            Label("//wasm-extension-js:extism_js_cli"),
            Label("//wasm-extension-js:src/plugin.d.ts"),
            bundle = bundle_name
        ),
        tools = [Label("//wasm-extension-js:extism_js_cli")],
        visibility = visibility,
    )

    native.filegroup(
        name = name + "_unpacked",
        srcs = [":" + name + "_wasm"] + pkg_json_targets,
        visibility = visibility,
    )

    package_extension(
        name = name,
        extension_target = ":" + name + "_unpacked",
        visibility = visibility,
    )

    native.filegroup(
        name = name,
        srcs = [
            ":" + name + "_unpacked",
            ":" + name + "_msxt",
        ],
        visibility = visibility,
    )
