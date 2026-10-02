#!/usr/bin/env python3
"""
Boilerplate extension generator for Moosync Extensions SDK.
Reads templates from template files and generates extension workspaces.
"""

import argparse
import glob
import os
import subprocess
import sys
from string import Template

# Language-specific definitions to place into bazel/<lang>.MODULE.bazel
LANGUAGE_MODULE_DEFINITIONS: dict[str, str] = {
    "rust": """bazel_dep(name = "rules_rust", version = "0.73.0")
single_version_override(
    module_name = "rules_rust",
    patch_strip = 1,
    patches = ["//patches:rules_rust_gnu_windows.patch"],
    version = "0.73.0",
)

bazel_dep(name = "rules_rust_prost", version = "0.73.0")

rust = use_extension("@rules_rust//rust:extensions.bzl", "rust")
rust.toolchain(
    edition = "2024",
    extra_target_triples = [
        "x86_64-unknown-linux-gnu",
        "aarch64-unknown-linux-gnu",
        "x86_64-apple-darwin",
        "aarch64-apple-darwin",
        "wasm32-wasip1",
        "x86_64-pc-windows-gnu",
    ],
    versions = [
        "1.95.0",
        "nightly/2025-12-16",
    ],
)
use_repo(rust, "rust_toolchains")

register_toolchains("@rust_toolchains//:all")
""",
    "js": """bazel_dep(name = "aspect_rules_js", version = "3.4.1")
single_version_override(
    module_name = "aspect_rules_js",
    patch_strip = 1,
    patches = ["//patches:aspect_rules_js_virtual_store_prefix.patch"],
)

bazel_dep(name = "aspect_rules_ts", version = "3.10.1")
bazel_dep(name = "rules_nodejs", version = "6.7.5")

pnpm = use_extension("@aspect_rules_js//npm:extensions.bzl", "pnpm")
pnpm.pnpm(pnpm_version = "9.15.0")
use_repo(pnpm, "pnpm")

node = use_extension("@rules_nodejs//nodejs:extensions.bzl", "node")
use_repo(node, "nodejs_toolchains")
register_toolchains("@nodejs_toolchains//:all")

rules_ts_ext = use_extension("@aspect_rules_ts//ts:extensions.bzl", "typescript")
rules_ts_ext.deps(
    name = "sdk_npm_typescript",
    ts_version_from = "@extensions_sdk//wasm-extension-js:package.json",
)
use_repo(rules_ts_ext, npm_typescript = "sdk_npm_typescript")
register_toolchains("@npm_typescript//:all")
""",
    "py": """bazel_dep(name = "rules_python", version = "2.3.2")
bazel_dep(name = "aspect_rules_py", version = "1.12.0")

python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(
    is_default = True,
    python_version = "3.11",
)
""",
    "go": """bazel_dep(name = "rules_go", version = "0.63.0")
bazel_dep(name = "gazelle", version = "0.53.0")
""",
}

DEFAULT_DEPENDENCIES_MODULE_CONTENT = """# Automatically included workspace-wide module dependencies
# Extension sub-modules are linked below
"""


def to_pascal_case(text: str) -> str:
    cleaned = text.replace("-", " ").replace("_", " ").replace(".", " ")
    return "".join(word.capitalize() for word in cleaned.split()) or "MyExtension"


def find_templates_root(custom_dir: str | None = None) -> str:
    if custom_dir and os.path.isdir(custom_dir):
        return os.path.abspath(custom_dir)

    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
        os.path.join(
            os.environ.get("BUILD_WORKSPACE_DIRECTORY", ""), "tools", "templates"
        ),
        os.path.join(os.environ.get("RUNFILES_DIR", ""), "_main", "tools", "templates"),
        os.path.join(
            os.environ.get("RUNFILES_DIR", ""), "extensions_sdk", "tools", "templates"
        ),
        os.path.join(
            os.environ.get("JAVA_RUNFILES", ""), "_main", "tools", "templates"
        ),
    ]

    for candidate in candidates:
        if candidate and os.path.isdir(candidate):
            return os.path.abspath(candidate)

    raise FileNotFoundError("Could not locate tools/templates directory")


def find_workspace_root(start_dir: str) -> str | None:
    ws = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    if ws and os.path.isdir(ws):
        return os.path.abspath(ws)

    current = os.path.abspath(start_dir)
    while True:
        if (
            os.path.isfile(os.path.join(current, "MODULE.bazel"))
            or os.path.isfile(os.path.join(current, "dependencies.MODULE.bazel"))
            or os.path.isfile(os.path.join(current, "REPO.bazel"))
            or os.path.isfile(os.path.join(current, "WORKSPACE"))
            or os.path.isfile(os.path.join(current, "WORKSPACE.bazel"))
        ):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def ensure_include_statement(target_file: str, include_label: str) -> bool:
    """Ensures an include("...") statement exists in target_file. Returns True if updated."""
    content = ""
    if os.path.isfile(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

    include_stmt = f'include("{include_label}")'
    if include_stmt in content:
        return False

    prefix = "" if not content or content.endswith("\n") else "\n"
    new_content = content + prefix + include_stmt + "\n"

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def ensure_dependencies_module(workspace_root: str) -> tuple[str, bool, bool]:
    """
    Ensures dependencies.MODULE.bazel exists at workspace root and is included in MODULE.bazel.
    Returns (dep_file_path, created_file, included_in_root).
    """
    dep_file_path = os.path.join(workspace_root, "dependencies.MODULE.bazel")
    created_file = False

    if not os.path.isfile(dep_file_path):
        with open(dep_file_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_DEPENDENCIES_MODULE_CONTENT)
        created_file = True

    root_module = os.path.join(workspace_root, "MODULE.bazel")
    included_in_root = ensure_include_statement(
        root_module, "//:dependencies.MODULE.bazel"
    )

    return dep_file_path, created_file, included_in_root


def ensure_language_module(
    canonical_lang: str, workspace_root: str
) -> tuple[str, bool, bool]:
    """
    Creates bazel/<lang>.MODULE.bazel if missing, and includes it in root MODULE.bazel.
    Returns (lang_module_path, created_file, included_in_root).
    """
    lang_file_map = {
        "rust": "rust.MODULE.bazel",
        "js": "js.MODULE.bazel",
        "py": "python.MODULE.bazel",
        "go": "go.MODULE.bazel",
    }
    filename = lang_file_map.get(canonical_lang, f"{canonical_lang}.MODULE.bazel")
    bazel_dir = os.path.join(workspace_root)
    os.makedirs(bazel_dir, exist_ok=True)

    lang_module_path = os.path.join(bazel_dir, filename)
    created_file = False

    if not os.path.isfile(lang_module_path):
        content = LANGUAGE_MODULE_DEFINITIONS.get(
            canonical_lang, f"# Module dependencies for {canonical_lang}\n"
        )
        with open(lang_module_path, "w", encoding="utf-8") as f:
            f.write(content)
        created_file = True

    root_module = os.path.join(workspace_root, "MODULE.bazel")
    include_target = f"//:{filename}"
    included_in_root = ensure_include_statement(root_module, include_target)

    return lang_module_path, created_file, included_in_root


def scaffold_extension(
    lang: str,
    name: str,
    dest: str,
    display_name: str,
    package_name: str,
    templates_root: str,
    workspace_root: str,
):
    lang_map = {
        "rs": "rust",
        "rust": "rust",
        "go": "go",
        "golang": "go",
        "py": "py",
        "python": "py",
        "js": "js",
        "javascript": "js",
        "ts": "js",
        "typescript": "js",
    }
    canonical_lang = lang_map.get(lang)
    if not canonical_lang:
        sys.exit(f"Unknown language: {lang}. Choose from: rust, go, python, js")

    lang_tmpl_dir = os.path.join(templates_root, canonical_lang)
    if not os.path.isdir(lang_tmpl_dir):
        sys.exit(
            f"Template directory not found for '{canonical_lang}': {lang_tmpl_dir}"
        )

    try:
        rel_pkg = os.path.relpath(dest, workspace_root)
    except ValueError:
        sys.exit(
            f"Destination '{dest}' must be on the same drive/filesystem as workspace root '{workspace_root}'."
        )

    if rel_pkg.startswith(".."):
        sys.exit(
            f"Destination '{dest}' must be located inside the Bazel workspace '{workspace_root}'."
        )

    rel_to_root = os.path.relpath(workspace_root, dest)
    pkg_label = "" if rel_pkg == "." else f"//{rel_pkg}"

    struct_name = to_pascal_case(name)
    template_vars = {
        "name": name,
        "display_name": display_name,
        "package_name": package_name,
        "struct_name": struct_name,
        "rel_pkg": rel_pkg,
        "rel_to_root": rel_to_root,
        "pkg_label": pkg_label,
    }

    os.makedirs(dest, exist_ok=True)

    created_files = []
    # 1. Walk language-specific template directory
    for root, dirs, files in os.walk(lang_tmpl_dir):
        rel_dir = os.path.relpath(root, lang_tmpl_dir)
        target_dir = dest if rel_dir == "." else os.path.join(dest, rel_dir)
        os.makedirs(target_dir, exist_ok=True)

        for filename in files:
            src_file = os.path.join(root, filename)
            target_filename = filename[:-5] if filename.endswith(".tmpl") else filename
            target_filename = (
                Template(target_filename)
                .safe_substitute(template_vars)
                .replace("ext_name", name)
            )
            target_file = os.path.join(target_dir, target_filename)

            with open(src_file, "r", encoding="utf-8") as f:
                content = f.read()

            rendered = Template(content).substitute(template_vars)

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(rendered)

            created_files.append(target_file)

    # 2. Process root templates (e.g. test.py.tmpl) into extension root
    for entry in os.listdir(templates_root):
        src_file = os.path.join(templates_root, entry)
        if os.path.isfile(src_file) and entry.endswith(".tmpl"):
            target_filename = entry[:-5]
            target_filename = (
                Template(target_filename)
                .safe_substitute(template_vars)
                .replace("ext_name", name)
            )
            target_file = os.path.join(dest, target_filename)

            with open(src_file, "r", encoding="utf-8") as f:
                content = f.read()

            rendered = Template(content).substitute(template_vars)

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(rendered)

            created_files.append(target_file)

    if canonical_lang == "js":
        pnpm_lock = os.path.join(dest, "pnpm-lock.yaml")
        if not os.path.exists(pnpm_lock):
            with open(pnpm_lock, "w", encoding="utf-8") as f:
                f.write("lockfileVersion: '9.0'\n")
            created_files.append(pnpm_lock)

    # Extension-specific module dependencies
    module_bazel_file = os.path.join(dest, f"{name}.MODULE.bazel")
    if module_bazel_file not in created_files and not os.path.isfile(module_bazel_file):
        with open(module_bazel_file, "w", encoding="utf-8") as f:
            f.write(f"# Module dependencies for {name}\n")
        created_files.append(module_bazel_file)

    return created_files, canonical_lang, pkg_label


def include_in_module(
    dest: str, name: str, workspace_root: str
) -> tuple[str, bool] | None:
    try:
        rel_pkg = os.path.relpath(dest, workspace_root)
    except ValueError:
        return None

    if rel_pkg.startswith(".."):
        return None

    include_target = (
        f"//:{name}.MODULE.bazel"
        if rel_pkg == "."
        else f"//{rel_pkg}:{name}.MODULE.bazel"
    )

    dep_file = os.path.join(workspace_root, "dependencies.MODULE.bazel")
    mod_file = os.path.join(workspace_root, "MODULE.bazel")

    # Prioritize dependencies.MODULE.bazel, falling back to root MODULE.bazel
    target_file = (
        dep_file
        if os.path.isfile(dep_file)
        else mod_file
        if os.path.isfile(mod_file)
        else None
    )
    if not target_file:
        return None

    updated = ensure_include_statement(target_file, include_target)
    return target_file, updated


def create_python_venv(workspace_root: str, pkg_label: str, name: str, dest: str):
    venv_target = f"{pkg_label}:{name}_bin.venv" if pkg_label else f"//:{name}_bin.venv"
    print(f"\nCreating Python virtual environment using Bazel: {venv_target}...")
    cmd = ["bazel", "run", venv_target, "--", f"--dest={dest}", "--name=.venv"]
    res = subprocess.run(cmd, cwd=workspace_root)
    if res.returncode != 0:
        print(
            f"Warning: Failed to create venv via Bazel command: {' '.join(cmd)}",
            file=sys.stderr,
        )
    else:
        print(
            f"Successfully generated virtual environment in: {os.path.join(dest, '.venv')}"
        )


def ensure_moounit_venv(workspace_root: str):
    """
    Creates and configures a shared Python virtual environment (.venv) at workspace root
    containing moounit, pytest, and proto dependencies for all moounit tests.
    """
    bin_target = "@extensions_sdk//moounit:moounit_runner"
    print(f"\nEnsuring shared moounit virtual environment using Bazel: {bin_target}...")
    res = subprocess.run(["bazel", "build", bin_target], cwd=workspace_root)
    if res.returncode != 0:
        print(
            f"Warning: Failed to build moounit runner target {bin_target}",
            file=sys.stderr,
        )
        return

    bazel_bin = os.path.join(workspace_root, "bazel-bin")
    runner_runfiles = os.path.join(
        bazel_bin, "external", "extensions_sdk+", "moounit", "moounit_runner.runfiles"
    )
    if not os.path.isdir(runner_runfiles):
        matches = glob.glob(
            os.path.join(bazel_bin, "**", "moounit_runner.runfiles"), recursive=True
        )
        if matches:
            runner_runfiles = matches[0]

    runfiles_venv = None
    candidate_venvs = [
        os.path.join(
            bazel_bin, "external", "extensions_sdk+", "moounit", ".moounit_runner.venv"
        ),
        os.path.join(runner_runfiles, ".moounit_runner.venv"),
    ]
    for c in candidate_venvs:
        if os.path.isdir(c):
            runfiles_venv = c
            break

    if not runfiles_venv:
        matches = glob.glob(
            os.path.join(bazel_bin, "**", ".moounit_runner.venv"), recursive=True
        )
        if matches:
            runfiles_venv = matches[0]

    if not runfiles_venv or not os.path.isdir(runfiles_venv):
        print(
            f"Warning: Could not locate .moounit_runner.venv inside {bazel_bin}",
            file=sys.stderr,
        )
        return

    venv_link = os.path.join(workspace_root, ".venv")
    if os.path.islink(venv_link) or os.path.exists(venv_link):
        try:
            if os.path.islink(venv_link) or os.path.isfile(venv_link):
                os.unlink(venv_link)
            else:
                import shutil
                shutil.rmtree(venv_link)
        except Exception as e:
            print(f"Warning: Failed to clean up existing {venv_link}: {e}", file=sys.stderr)

    try:
        os.symlink(runfiles_venv, venv_link)
        print(
            f"Successfully generated shared moounit virtual environment in: {venv_link}"
        )
    except Exception as e:
        print(f"Warning: Failed to symlink {runfiles_venv} to {venv_link}: {e}", file=sys.stderr)
        return

    # Patch any *.pth files in site-packages to contain absolute paths to runfiles
    for sp in glob.glob(os.path.join(venv_link, "lib", "python*", "site-packages")):
        for pth in glob.glob(os.path.join(sp, "*.pth")):
            if os.path.basename(pth).startswith("_"):
                continue
            try:
                with open(pth, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                new_lines = []
                modified = False
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("../../../../"):
                        rel = stripped.removeprefix("../../../../")
                        abs_path = os.path.normpath(os.path.join(runner_runfiles, rel))
                        new_lines.append(abs_path + "\n")
                        modified = True
                    else:
                        new_lines.append(line)
                if modified:
                    with open(pth, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
            except Exception as e:
                print(f"Warning: Failed to patch {pth}: {e}", file=sys.stderr)


def run_pnpm_install(workspace_root: str, pkg_label: str):
    pnpm_target = f"{pkg_label}:pnpm" if pkg_label else "//:pnpm"
    print(f"\nRunning pnpm install using Bazel: {pnpm_target}...")
    cmd = ["bazel", "run", pnpm_target, "--", "install"]

    # Explicit check=False silences the warning while retaining custom error handling
    res = subprocess.run(
        cmd,
        cwd=workspace_root,
        capture_output=True,
        text=True,
        check=False,
    )

    # aspect_rules_js updates the lockfile during module extension evaluation and intentionally
    # fails the first run to invalidate Bazel's cache. If so, rerun the command.
    if (
        res.returncode != 0
        and "pnpm-lock.yaml file updated. Please run your build again." in res.stderr
    ):
        print(
            "Initial pnpm lockfile generated by Bazel. Re-running to link dependencies..."
        )
        res = subprocess.run(cmd, cwd=workspace_root, check=False)

    if res.returncode != 0:
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        print(
            f"Warning: Failed to run pnpm install via Bazel command: {' '.join(cmd)}",
            file=sys.stderr,
        )
    else:
        print("Successfully generated pnpm lockfile and node_modules.")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new Moosync extension from file templates"
    )
    parser.add_argument(
        "--lang",
        "-l",
        choices=[
            "rust",
            "rs",
            "go",
            "golang",
            "python",
            "py",
            "javascript",
            "js",
            "typescript",
            "ts",
        ],
        required=True,
        help="Language for the extension",
    )
    parser.add_argument(
        "--name", "-n", required=True, help="Extension target name (e.g., my_extension)"
    )
    parser.add_argument(
        "--dest",
        "-d",
        help="Destination directory (defaults to current working dir / name)",
    )
    parser.add_argument("--display-name", help="Display name shown in Moosync UI")
    parser.add_argument(
        "--package-name", help="Unique package name (e.g. moosync.my_extension)"
    )
    parser.add_argument(
        "--templates-dir", help="Optional path to custom templates directory"
    )

    args = parser.parse_args()

    name = args.name.strip()
    working_dir = os.environ.get("BUILD_WORKING_DIRECTORY", os.getcwd())
    dest = args.dest if args.dest else os.path.join(working_dir, name)
    dest = os.path.abspath(dest)

    workspace_root = find_workspace_root(dest)
    if not workspace_root:
        sys.exit(
            f"Error: Could not locate Bazel workspace root for destination '{dest}'. Scaffold must be run from inside a Bazel workspace."
        )

    display_name = args.display_name or name.replace("_", " ").replace("-", " ").title()
    package_name = args.package_name or f"moosync.{name.replace('_', '.')}"

    templates_root = find_templates_root(args.templates_dir)

    created_files, canonical_lang, pkg_label = scaffold_extension(
        lang=args.lang.lower(),
        name=name,
        dest=dest,
        display_name=display_name,
        package_name=package_name,
        templates_root=templates_root,
        workspace_root=workspace_root,
    )

    # 1. Mandatory dependencies.MODULE.bazel check and include
    dep_file, dep_created, dep_included = ensure_dependencies_module(workspace_root)
    if dep_created:
        print(
            f"Created workspace dependencies file: {os.path.relpath(dep_file, working_dir)}"
        )
    if dep_included:
        print("Included dependencies.MODULE.bazel in root MODULE.bazel")

    # 2. Language-specific module check and include
    lang_file, lang_created, lang_included = ensure_language_module(
        canonical_lang, workspace_root
    )
    if lang_created:
        print(f"Created language module: {os.path.relpath(lang_file, working_dir)}")
    if lang_included:
        print(f"Included {os.path.basename(lang_file)} in root MODULE.bazel")

    # 3. Extension-specific module check and include (into dependencies.MODULE.bazel)
    include_result = include_in_module(dest, name, workspace_root)

    print(f"\nSuccessfully generated extension in: {dest}")
    print("Created files:")
    for cf in created_files:
        print(f"  - {os.path.relpath(cf, working_dir)}")

    if include_result:
        target_file, updated = include_result
        rel_target = os.path.relpath(target_file, working_dir)
        if updated:
            print(f"\nIncluded {name}.MODULE.bazel in: {rel_target}")
        else:
            print(f"\n{name}.MODULE.bazel already included in: {rel_target}")

    # Post-scaffold language setup hooks
    if canonical_lang == "py":
        create_python_venv(workspace_root, pkg_label, name, dest)
    elif canonical_lang == "js":
        run_pnpm_install(workspace_root, pkg_label)

    # Ensure shared moounit test virtualenv at workspace root
    ensure_moounit_venv(workspace_root)

    build_label = f"{pkg_label}:{name}" if pkg_label else f"//:{name}"

    print(f"\nBuild target: {name}")
    print(f"Run `bazel build {build_label}` to build your extension.")


if __name__ == "__main__":
    main()
