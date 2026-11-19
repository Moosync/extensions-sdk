#!/usr/bin/env python3
"""
CLI utility to compute SHA-256, SHA-512, and MD5 hashes for an executable binary
and print a ready-to-copy Bazel rule snippet for Moosync extensions.
"""

import argparse
import hashlib
import os
import sys


def compute_hashes(file_path):
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
            sha512.update(chunk)
            md5.update(chunk)

    return {
        "sha256": sha256.hexdigest(),
        "sha512": sha512.hexdigest(),
        "md5": md5.hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compute binary hashes and generate Bazel rule configuration for Moosync extension."
    )
    parser.add_argument("binary", help="Path to the binary file")
    parser.add_argument(
        "--name",
        help="Binary name (defaults to basename of binary file)",
        default=None,
    )
    parser.add_argument(
        "--path",
        help="Target execution path (defaults to '{CACHE_DIR}/bin/<name>')",
        default=None,
    )
    parser.add_argument(
        "--justification",
        help="Justification for executing this binary",
        default="<Describe why this binary is required by the extension>",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.binary):
        print(f"Error: File not found: {args.binary}", file=sys.stderr)
        sys.exit(1)

    binary_name = args.name or os.path.basename(args.binary)
    target_path = args.path or f"{{CACHE_DIR}}/bin/{binary_name}"
    hashes = compute_hashes(args.binary)

    snippet = f"""binaries = {{
    "{binary_name}": {{
        "path": "{target_path}",
        "sha256": "{hashes['sha256']}",
        "sha512": "{hashes['sha512']}",
        "md5": "{hashes['md5']}",
        "justification": "{args.justification}",
    }},
}}"""

    print("\nGenerated Bazel rule snippet for binaries:")
    print("------------------------------------------")
    print(snippet)
    print("------------------------------------------")
    print(
        f"Note: Ensure that the directory containing '{target_path}' is declared in 'allowed_paths'!\n"
    )


if __name__ == "__main__":
    main()
