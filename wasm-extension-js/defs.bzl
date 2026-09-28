"""
Wasm extension rules for TypeScript/JavaScript.
"""

load("@aspect_rules_rollup//rollup:defs.bzl", "rollup")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@rules_shell//shell:sh_binary.bzl", "sh_binary")
load("//:package_extension.bzl", "package_extension")
load("//:package_json.bzl", "generate_package_json")

def js_wasm_extension(
        name,
        srcs,
        package_json,
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
        allowed_paths = None):
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

# 1. Grab the relative path to pnpm passed via args
PNPM_PATH="$$1"
shift

# 2. Resolve absolute path to the binary
if [[ -x "$$PNPM_PATH" ]]; then
  PNPM_BIN="$$(readlink -f "$$PNPM_PATH")"
elif [[ -x "$$0.runfiles/$$PNPM_PATH" ]]; then
  PNPM_BIN="$$(readlink -f "$$0.runfiles/$$PNPM_PATH")"
else
  PNPM_BIN="$$(which pnpm 2>/dev/null || true)"
fi

if [[ -z "$${PNPM_BIN:-}" || ! -x "$$PNPM_BIN" ]]; then
  echo >&2 "ERROR: Could not locate executable pnpm binary ($$PNPM_PATH)"
  exit 1
fi

# 3. Satisfy aspect_rules_js js_binary launcher requirement
export BAZEL_BINDIR="."

# 4. CD into the extension source directory
cd "$${BUILD_WORKSPACE_DIRECTORY}/""" + pkg_dir + """"

# 5. Run pnpm with the user-supplied arguments
exec "$$PNPM_BIN" "$$@"
EOF
""",
        visibility = ["//visibility:private"],
    )

    sh_binary(
        name = name + "_pnpm",
        srcs = [":" + pnpm_runner_script],
        # rootpath produces the clean relative path inside runfiles:
        args = ["$(rootpath {})".format(pnpm_target)],
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
            node_modules,
            Label("//wasm-extension-js:node_modules/@extism/js-pdk"),
            Label("//wasm-extension-js:wasm_extension_js_lib"),
        ],
        data = data,
        visibility = visibility,
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
            bundle = bundle_name,
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
