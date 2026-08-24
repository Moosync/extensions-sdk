#!/usr/bin/env python3
"""
Simple HTTP server to serve the generated documentation site locally.
"""

import argparse
import functools
import http.server
import os
import socketserver
import sys


def main():
    parser = argparse.ArgumentParser(description="Serve Moosync Extensions SDK documentation")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port to serve on (default: 8000)")
    parser.add_argument("--dir", "-d", help="Directory to serve (default: docs/site)")
    args = parser.parse_args()

    serve_dir = args.dir
    if not serve_dir:
        # Check standard bazel-bin locations
        candidates = [
            "bazel-bin/docs/site",
            "docs/site",
        ]
        for c in candidates:
            if os.path.isdir(c):
                serve_dir = c
                break
        if not serve_dir:
            serve_dir = "bazel-bin/docs/site"

    serve_dir = os.path.abspath(serve_dir)
    if not os.path.isdir(serve_dir):
        print(f"Error: Directory '{serve_dir}' does not exist.")
        print("Please build the documentation first with `bazel build //docs:site`.")
        sys.exit(1)

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=serve_dir)

    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", args.port), handler) as httpd:
        print("=" * 60)
        print(f" Moosync Extensions SDK Documentation Server")
        print(f" Serving from: {serve_dir}")
        print(f" Open in browser: http://localhost:{args.port}/")
        print("=" * 60)
        print("Press Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    main()
