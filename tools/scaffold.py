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
            target_file = os.path.join(target_dir, target_filename)

            with open(src_file, "r", encoding="utf-8") as f:
                content = f.read()

            rendered = Template(content).substitute(template_vars)

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(rendered)

            created_files.append(target_file)

    return created_files


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

    print(f"Successfully generated extension in: {dest}")
    print("Created files:")
    for cf in created_files:
        print(f"  - {os.path.relpath(cf, working_dir)}")
    print(f"\nBuild target: {name}")
    print(f"Run `bazel build //{os.path.relpath(dest, working_dir)}:{name}` to build your extension.")


if __name__ == "__main__":
    main()
