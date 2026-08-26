#!/usr/bin/env python3
"""
Boilerplate extension generator for Moosync Extensions SDK.
Reads templates from template files and generates extension workspaces.
"""

import argparse
import os
import sys
from string import Template


def to_pascal_case(text: str) -> str:
    cleaned = text.replace("-", " ").replace("_", " ").replace(".", " ")
    return "".join(word.capitalize() for word in cleaned.split()) or "MyExtension"


def find_templates_root(custom_dir: str | None = None) -> str:
    if custom_dir and os.path.isdir(custom_dir):
        return os.path.abspath(custom_dir)

    candidates = [
        # Direct relative to script
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
        # Under BUILD_WORKSPACE_DIRECTORY
        os.path.join(os.environ.get("BUILD_WORKSPACE_DIRECTORY", ""), "tools", "templates"),
        # Bazel runfiles locations
        os.path.join(os.environ.get("RUNFILES_DIR", ""), "_main", "tools", "templates"),
        os.path.join(os.environ.get("RUNFILES_DIR", ""), "extensions_sdk", "tools", "templates"),
        os.path.join(os.environ.get("JAVA_RUNFILES", ""), "_main", "tools", "templates"),
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


def scaffold_extension(lang: str, name: str, dest: str, display_name: str, package_name: str, templates_root: str):
    lang_map = {
        "rs": "rust", "rust": "rust",
        "go": "go", "golang": "go",
        "py": "py", "python": "py",
        "js": "js", "javascript": "js", "ts": "js", "typescript": "js",
    }
    canonical_lang = lang_map.get(lang)
    if not canonical_lang:
        sys.exit(f"Unknown language: {lang}. Choose from: rust, go, python, js")

    lang_tmpl_dir = os.path.join(templates_root, canonical_lang)
    if not os.path.isdir(lang_tmpl_dir):
        sys.exit(f"Template directory not found for '{canonical_lang}': {lang_tmpl_dir}")

    struct_name = to_pascal_case(name)
    template_vars = {
        "name": name,
        "display_name": display_name,
        "package_name": package_name,
        "struct_name": struct_name,
    }

    os.makedirs(dest, exist_ok=True)

    created_files = []
    for root, dirs, files in os.walk(lang_tmpl_dir):
        rel_dir = os.path.relpath(root, lang_tmpl_dir)
        target_dir = dest if rel_dir == "." else os.path.join(dest, rel_dir)
        os.makedirs(target_dir, exist_ok=True)

        for filename in files:
            src_file = os.path.join(root, filename)
            target_filename = filename[:-5] if filename.endswith(".tmpl") else filename
            target_filename = Template(target_filename).safe_substitute(template_vars).replace("ext_name", name)
            target_file = os.path.join(target_dir, target_filename)

            with open(src_file, "r", encoding="utf-8") as f:
                content = f.read()

            rendered = Template(content).substitute(template_vars)

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(rendered)

            created_files.append(target_file)

    module_bazel_file = os.path.join(dest, f"{name}.MODULE.bazel")
    if module_bazel_file not in created_files and not os.path.isfile(module_bazel_file):
        with open(module_bazel_file, "w", encoding="utf-8") as f:
            f.write(f"# Module dependencies for {name}\n")
        created_files.append(module_bazel_file)

    return created_files


def include_in_module(dest: str, name: str) -> tuple[str, bool] | None:
    workspace_root = find_workspace_root(dest)
    if not workspace_root:
        return None

    try:
        rel_pkg = os.path.relpath(dest, workspace_root)
    except ValueError:
        return None

    if rel_pkg.startswith(".."):
        return None

    if rel_pkg == ".":
        include_target = f"//:{name}.MODULE.bazel"
    else:
        include_target = f"//{rel_pkg}:{name}.MODULE.bazel"

    dep_file = os.path.join(workspace_root, "dependencies.MODULE.bazel")
    mod_file = os.path.join(workspace_root, "MODULE.bazel")

    if os.path.isfile(dep_file):
        target_file = dep_file
    elif os.path.isfile(mod_file):
        target_file = mod_file
    else:
        return None

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    include_stmt = f'include("{include_target}")'
    if include_stmt in content:
        return target_file, False

    prefix = "" if not content or content.endswith("\n") else "\n"
    new_content = content + prefix + include_stmt + "\n"

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    return target_file, True


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new Moosync extension from file templates")
    parser.add_argument(
        "--lang",
        "-l",
        choices=["rust", "rs", "go", "golang", "python", "py", "javascript", "js", "typescript", "ts"],
        required=True,
        help="Language for the extension",
    )
    parser.add_argument("--name", "-n", required=True, help="Extension target name (e.g., my_extension)")
    parser.add_argument("--dest", "-d", help="Destination directory (defaults to current working dir / name)")
    parser.add_argument("--display-name", help="Display name shown in Moosync UI")
    parser.add_argument("--package-name", help="Unique package name (e.g. moosync.my_extension)")
    parser.add_argument("--templates-dir", help="Optional path to custom templates directory")

    args = parser.parse_args()

    name = args.name.strip()
    working_dir = os.environ.get("BUILD_WORKING_DIRECTORY", os.getcwd())
    dest = args.dest if args.dest else os.path.join(working_dir, name)
    dest = os.path.abspath(dest)

    display_name = args.display_name or name.replace("_", " ").replace("-", " ").title()
    package_name = args.package_name or f"moosync.{name.replace('_', '.')}"

    templates_root = find_templates_root(args.templates_dir)

    created_files = scaffold_extension(
        lang=args.lang.lower(),
        name=name,
        dest=dest,
        display_name=display_name,
        package_name=package_name,
        templates_root=templates_root,
    )

    include_result = include_in_module(dest, name)

    print(f"Successfully generated extension in: {dest}")
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

    workspace_root = find_workspace_root(dest)
    if workspace_root:
        rel_to_ws = os.path.relpath(dest, workspace_root)
        pkg = "" if rel_to_ws == "." else rel_to_ws
        build_label = f"//{pkg}:{name}" if pkg else f"//:{name}"
    else:
        build_label = f"//{os.path.relpath(dest, working_dir)}:{name}"

    print(f"\nBuild target: {name}")
    print(f"Run `bazel build {build_label}` to build your extension.")


if __name__ == "__main__":
    main()
