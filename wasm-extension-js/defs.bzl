"""
Wasm extension rules for TypeScript/JavaScript.
"""

load("@aspect_rules_rollup//rollup:defs.bzl", "rollup")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@rules_shell//shell:sh_binary.bzl", "sh_binary")
load("//:manifest_pb.bzl", "generate_manifest_pb")
load("//:package_extension.bzl", "package_extension")

def js_wasm_extension(
        name,
        srcs,
        deps = [],
        data = [],
        node_modules = None,
        pnpm_target = Label("@pnpm"),
        tsconfig = Label("//wasm-extension-js:tsconfig.json"),
        rollup_config = Label("//wasm-extension-js:rollup.config.mjs"),
        visibility = None,
        display_name = None,
        package_name = None,
        version = None,
        icon = None,
        allowed_hosts = None,
        allowed_paths = None,
        scopes = None):
    """
    Builds a Wasm extension from TypeScript sources.
    """

    if node_modules == None:
        node_modules = ":node_modules"

    pnpm_runner_script = name + "_run_pnpm.sh"

    # In wasm-extension-js/defs.bzl
    pkg_dir = native.package_name()

    native.genrule(
        name = name + "_gen_pnpm_runner",
        outs = [pnpm_runner_script],
        cmd = """cat << 'EOF' > $@
#!/usr/bin/env bash
set -euo pipefail

PNPM_PATH="$$1"
shift

export BAZEL_BINDIR="."
cd "$${BUILD_WORKSPACE_DIRECTORY}/""" + pkg_dir + """"
exec "$${RUNFILES_DIR:-$$0.runfiles}/$$PNPM_PATH" "$$@"
EOF
""",
        visibility = ["//visibility:private"],
    )

    sh_binary(
        name = name + "_pnpm",
        srcs = [":" + pnpm_runner_script],
        args = ["$(rlocationpath {})".format(pnpm_target)],
        data = [pnpm_target],
        visibility = visibility,
    )

    # Optional alias so callers can simply run `:pnpm`
    if not native.existing_rule("pnpm"):
        native.alias(
            name = "pnpm",
            actual = ":" + name + "_pnpm",
            visibility = visibility,
        )

    # =========================================================================
    # Extension Manifest & Config Generation
    # =========================================================================
    manifest_pb_targets = generate_manifest_pb(
        name = name,
        display_name = display_name,
        package_name = package_name,
        version = version,
        icon = icon,
        allowed_hosts = allowed_hosts,
        allowed_paths = allowed_paths,
        scopes = scopes,
        data = data,
        visibility = visibility,
        wasm_target = ":" + name + "_wasm",
    )

    ts_lib_name = name + "_ts"
    bundle_name = name + "_bundle"
    out_dir = name + "_lib"

    tsconfig_local = name + "_tsconfig.json"
    native.genrule(
        name = name + "_copy_tsconfig",
        srcs = [tsconfig],
        outs = [tsconfig_local],
        cmd = 'sed \'s#"outDir": "./lib"#"outDir": "./{out_dir}"#g\' $< > $@'.format(out_dir = out_dir),
        visibility = ["//visibility:private"],
    )

    rollup_config_local = name + "_rollup.config.mjs"
    native.genrule(
        name = name + "_copy_rollup_config",
        srcs = [rollup_config],
        outs = [rollup_config_local],
        cmd = "cp $< $@",
        visibility = ["//visibility:private"],
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
            node_modules,
            Label("//wasm-extension-js:node_modules/@extism/js-pdk"),
            Label("//wasm-extension-js:wasm_extension_js_lib"),
        ],
        data = data,
        visibility = ["//visibility:private"],
    )

    rollup(
        name = bundle_name,
        entry_point = out_dir + "/src/index.js",
        format = "cjs",
        node_modules = Label("//wasm-extension-js:node_modules"),
        sourcemap = "false",
        config_file = ":" + rollup_config_local,
        deps = [
            ":" + ts_lib_name,
            node_modules,
            Label("//wasm-extension-js:node_modules/@rollup/plugin-alias"),
            Label("//wasm-extension-js:node_modules/@rollup/plugin-commonjs"),
            Label("//wasm-extension-js:node_modules/@rollup/plugin-json"),
            Label("//wasm-extension-js:node_modules/@rollup/plugin-node-resolve"),
            Label("//wasm-extension-js:wasm_extension_js_lib"),
            Label("//wasm-extension-js:node_modules/@extism/js-pdk"),
        ] + deps,
        visibility = ["//visibility:private"],
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
            bundle = bundle_name,
        ),
        tools = [Label("//wasm-extension-js:extism_js_cli")],
        visibility = ["//visibility:private"],
    )

    native.filegroup(
        name = name + "_unpacked",
        srcs = [":" + name + "_wasm"] + manifest_pb_targets,
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
