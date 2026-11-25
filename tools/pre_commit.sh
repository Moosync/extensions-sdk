#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(git rev-parse --show-toplevel 2>/dev/null || jj root 2>/dev/null || pwd)"
cd "$WORKSPACE_DIR"

echo "=== Checking MODULE.bazel Git Overrides ==="
ANDROID_HOME="" ANDROID_SDK_ROOT="" bazel run //tools:check_git_override

echo "=== Updating Moosync SDKs from Protobuf RPC definitions ==="
ANDROID_HOME="" ANDROID_SDK_ROOT="" bazel run //tools/sdk_generator:update

# If git repo and index has changes, stage them
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git add \
    wasm-extension-rs/src/generated_api.rs \
    wasm-extension-rs/src/generated_dispatcher.rs \
    wasm-extension-go/pkg/api/generated_api.go \
    wasm-extension-go/pkg/api/generated_exports.go \
    wasm-extension-py/moosync_edk/generated_api.py \
    wasm-extension-py/moosync_edk/generated_dispatcher.py \
    wasm-extension-js/src/generated_api.ts \
    wasm-extension-js/src/generated_events.ts \
    moounit/generated.py 2>/dev/null || true
fi
