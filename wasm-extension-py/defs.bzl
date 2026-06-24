"""
Wasm extension rules for Python.
"""

load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@rules_python//python:defs.bzl", "PyInfo")
load("//:package_extension.bzl", "package_extension")
load("//:package_json.bzl", "generate_package_json")

def _py_wasm_extension_impl(ctx):
    extism_py = ctx.executable._extism_py
    share_dir = ctx.files._share_dir
    binaryen_files = ctx.files._binaryen

    relevant_files = [f.path for f in share_dir if "wasi-sysroot" not in f.path]

    # Locate EXTISM_PYTHON_WASI_DEPS_DIR (root of share/extism-py)
    share_path = ""
    for f in share_dir:
        # Check for libpython to determine root
        if "libpython3.11.a" in f.path:
            share_path = f.path.rsplit("/lib/wasm32-wasi/libpython3.11.a", 1)[0]
            break

    if not share_path:
        fail("Could not find libpython3.11.a in share directory. Files found: " + str(relevant_files))

    # Locate wasm-opt for PATH
    wasm_opt_path = ""
    for f in binaryen_files:
        if f.basename == "wasm-opt":
            wasm_opt_path = f.dirname
            break

    # Collect sources and deps
    transitive_srcs = depset(
        ctx.files.srcs + ctx.files.data,
        transitive = [dep[PyInfo].transitive_sources for dep in ctx.attr.deps],
    )

    # Remove "." to avoid copying the entire workspace
    custom_paths = ["wasm-extension-py"]

    # Add directories of srcs to allow importing them (e.g. main.py)
    src_dirs = []
    for f in ctx.files.srcs:
        path = f.short_path
        if path.startswith("../"):
            path = path[3:]

        if "/" in path:
            d = path.rsplit("/", 1)[0]
        else:
            d = ""

        if d and d not in src_dirs:
            src_dirs.append(d)

    runfiles_root_name = ctx.label.name + ".runfiles"
    symlinked_inputs = []
    runfiles_root_path = None

    # Map mapping sources to a merged directory structure
    for f in transitive_srcs.to_list():
        path = f.short_path
        if path.startswith("../"):
            path = path[3:]

        if f == ctx.file.main:
            # Rename main file to sdk_main.py cause thats how we load our sdk
            path = "sdk_main.py"

        out_link = ctx.actions.declare_file(runfiles_root_name + "/" + path)
        ctx.actions.symlink(output = out_link, target_file = f)
        symlinked_inputs.append(out_link)

        if runfiles_root_path == None:
            # Calculate the concrete path to runfiles root relative to execroot
            runfiles_root_path = out_link.path[:-len(path) - 1]

    # Reconstruct PYTHONPATH relative to the merged directory
    python_path_entries = [runfiles_root_path]

    dep_imports = depset(transitive = [dep[PyInfo].imports for dep in ctx.attr.deps]).to_list()
    for imp in dep_imports:
        python_path_entries.append(runfiles_root_path + "/" + imp)

    # Scan for specific known roots if they aren't covered by imports
    merged_roots = []
    for f in transitive_srcs.to_list():
        path = f.short_path
        if path.startswith("../"):
            path = path[3:]

        # Calculate root within the merged tree
        root = None
        if "core/types/protos/" in path and path.endswith("_pb2.py"):
            root = path.rsplit("core/types/protos/", 1)[0].rstrip("/")
        elif "google/protobuf" in path:
            root = path.split("google/protobuf", 1)[0].rstrip("/")

        if root and root not in merged_roots:
            merged_roots.append(root)

    for r in merged_roots:
        python_path_entries.append(runfiles_root_path + "/" + r)

    # Add custom paths and src dirs
    for d in custom_paths:
        python_path_entries.append(runfiles_root_path + "/" + d)

    for d in src_dirs:
        python_path_entries.append(runfiles_root_path + "/" + d)

    python_path = ":".join(python_path_entries)
    materialized_dir = ctx.actions.declare_directory(ctx.label.name + "_materialized_runfiles")

    ctx.actions.run_shell(
        inputs = depset(symlinked_inputs, transitive = [transitive_srcs]),
        outputs = [materialized_dir],
        command = "cp --reflink=auto -rL {src}/. {dst}/".format(src = runfiles_root_path, dst = materialized_dir.path),
        mnemonic = "MaterializeRunfiles",
    )

    # Update PYTHONPATH to use the materialized directory
    python_path = python_path.replace(runfiles_root_path, materialized_dir.path)

    # Find moosync_edk/__init__.py in transitive sources
    sdk_entry = None
    sdk_entry_path = None

    for f in transitive_srcs.to_list():
        if f.path.endswith("moosync_edk/__init__.py"):
            sdk_entry = f

            # Calculate where it ended up in the runfiles/materialized dir
            # Logic must match the loop above
            path = f.short_path
            if path.startswith("../"):
                path = path[3:]

            if f == ctx.file.main:
                path = "sdk_main.py"

            sdk_entry_path = materialized_dir.path + "/" + path
            break

    if not sdk_entry:
        fail("Could not find moosync_edk/__init__.py in dependencies. Ensure wasm-extension-py:moosync_edk is a dependency.")

    main_file = ctx.file.main
    inputs = depset([materialized_dir, main_file], transitive = [depset(share_dir), depset(binaryen_files)])

    out = ctx.actions.declare_file(ctx.label.name + ".wasm")
    ctx.actions.run(
        executable = extism_py,
        inputs = inputs,
        outputs = [out],
        env = {
            "EXTISM_PYTHON_WASI_DEPS_DIR": share_path,
            "PATH": wasm_opt_path,
            "PYTHONPATH": python_path,
            "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": "python",
            "EXTISM_ENABLE_WASI_OUTPUT": "1",
        },
        execution_requirements = {"no-sandbox": "1"},
        arguments = [
            sdk_entry_path,
            "-o",
            out.path,
        ],
    )

    return [DefaultInfo(files = depset([out]))]

_py_wasm_extension = rule(
    implementation = _py_wasm_extension_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = [".py"]),
        "deps": attr.label_list(providers = [PyInfo]),
        "main": attr.label(allow_single_file = [".py"], mandatory = True),
        "_extism_py": attr.label(
            default = Label("@extism_py_tool//:bin/extism-py"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_share_dir": attr.label(
            default = Label("@extism_py_tool//:share_files"),
        ),
        "_binaryen": attr.label(
            default = Label("@binaryen_tool//:bin_files"),
        ),
        "data": attr.label_list(allow_files = True),
    },
)

def _expose_pyi_impl(ctx):
    pyi_files = []
    for dep in ctx.attr.deps:
        if PyInfo in dep:
            pyi_files.append(dep[PyInfo].transitive_pyi_files)

    all_pyi = depset(transitive = pyi_files)

    return [
        DefaultInfo(files = all_pyi),
        PyInfo(
            transitive_sources = all_pyi,
        ),
    ]

expose_pyi = rule(
    implementation = _expose_pyi_impl,
    attrs = {"deps": attr.label_list(providers = [PyInfo])},
)

def py_extension(
        name,
        srcs,
        deps = [],
        data = [],
        display_name = None,
        package_name = None,
        version = None,
        icon = None,
        allowed_hosts = None,
        allowed_paths = None,
        main = None,
        **kwargs):
    """
    Builds a Wasm extension from Python sources.

    Args:
        name: The name of the target.
        srcs: Source files.
        deps: Dependencies.
        data: Data dependencies.
        display_name: Display name of the extension.
        package_name: Package name of the extension (mapped to name in json).
        version: Version of the extension.
        icon: Icon of the extension. Can be file path or label.
        allowed_hosts: List of allowed hosts.
        allowed_paths: Dict of allowed paths.
        main: Entry point file. Defaults to name + ".py".
        **kwargs: Additional arguments to pass to the rule.
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
        visibility = kwargs.get("visibility"),
        wasm_target = ":" + name + "_wasm",
    )

    expose_pyi(
        name = name + "_pyi",
        deps = [
            Label("//protos:extensions_py_proto"),
            Label("//protos:songs_py_proto"),
            Label("//protos:themes_py_proto"),
            Label("//protos:ui_py_proto"),
        ],
    )

    py_binary(
        name = name + "_bin",
        srcs = srcs,
        main = main,
        deps = deps + [
            Label("//wasm-extension-py:moosync_edk"),
            Label("//protos:moosync_python_root"),
            ":" + name + "_pyi",
        ],
        data = [
            ":" + name + "_pyi",
        ] + data,
        **kwargs
    )

    _py_wasm_extension(
        name = name + "_wasm",
        srcs = srcs,
        main = main,
        deps = deps + [Label("//wasm-extension-py:moosync_edk")],
        data = data,
        **kwargs
    )

    native.filegroup(
        name = name + "_unpacked",
        srcs = [":" + name + "_wasm"] + pkg_json_targets,
        visibility = kwargs.get("visibility"),
    )

    package_extension(
        name = name,
        extension_target = ":" + name + "_unpacked",
        visibility = kwargs.get("visibility"),
    )

    native.filegroup(
        name = name,
        srcs = [
            ":" + name + "_unpacked",
            ":" + name + "_msxt",
        ],
        **kwargs
    )
