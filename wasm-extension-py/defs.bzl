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
        ctx.files.srcs,
        transitive = [dep[PyInfo].transitive_sources for dep in ctx.attr.deps],
    )

    # Remove "." to avoid copying the entire workspace
    custom_paths = ["wasm-extension-py"]

    # Add directories of srcs to allow importing them (e.g. main.py)
    src_dirs = []
    for f in ctx.files.srcs:
        # Use short_path to match runfiles structure
        path = f.short_path
        if path.startswith("../"):
            path = path[3:]

        # Get directory
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

        out_link = ctx.actions.declare_file(runfiles_root_name + "/" + path)
        ctx.actions.symlink(output = out_link, target_file = f)
        symlinked_inputs.append(out_link)

        if runfiles_root_path == None:
            # Calculate the concrete path to runfiles root relative to execroot
            # out_link.path is bazel-out/.../pkg/name.runfiles/path/to/file
            # we want bazel-out/.../pkg/name.runfiles
            runfiles_root_path = out_link.path[:-len(path) - 1]

    # Reconstruct PYTHONPATH relative to the merged directory
    # We start with the root of the runfiles
    python_path_entries = [runfiles_root_path]

    # Add dep imports, adjusted for runfiles structure
    # Most deps provide imports as simple paths. We prepend the runfiles root.
    # Note: simple string concatenation assumes paths are relative.
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
        if path.endswith("core/types/protos/extensions_pb2.py"):
            root = path.rsplit("core/types/protos/extensions_pb2.py", 1)[0].rstrip("/")
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

    # Materialize the runfiles tree to a directory to allow WASI access (dereference symlinks)
    # WASI sandbox often cannot follow symlinks pointing outside the mapped directories.
    materialized_dir = ctx.actions.declare_directory(ctx.label.name + "_materialized_runfiles")

    # Copy runfiles tree to materialized dir.
    # We attempt Copy-on-Write (--reflink=auto) to save space, but fall back to copy (-rL)
    # because:
    # 1. Hardlinks (-l) fail due to cross-device link errors in Bazel sandbox.
    # 2. Symlinks fail because WASI sandbox cannot follow them outside mapped dirs.
    ctx.actions.run_shell(
        inputs = depset(symlinked_inputs, transitive = [transitive_srcs]),
        outputs = [materialized_dir],
        command = "cp --reflink=auto -rL {src}/. {dst}/".format(src = runfiles_root_path, dst = materialized_dir.path),
        mnemonic = "MaterializeRunfiles",
    )

    # Update PYTHONPATH to use the materialized directory
    python_path = python_path.replace(runfiles_root_path, materialized_dir.path)

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
            main_file.path,
            "-o",
            out.path,
        ],
    )

    return [DefaultInfo(files = depset([out]))]

py_wasm_extension = rule(
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
    },
)
