# Writing your first extension

## 1. Workspace Setup

In your workspace root, create or update `MODULE.bazel` to depend on `extensions_sdk`:

```starlark
module(
    name = "my_extensions",
    version = "1.0.0",
)

bazel_dep(name = "extensions_sdk", version = "1.0.0")
```

---

## 2. Generating Boilerplate

The easiest way to get started is by using the built-in scaffolding tool. This generates both the Bazel `BUILD` file and the starter code for your extension:

{{#tabs }}
{{#tab name="Rust" }}
```bash
bazel run @extensions_sdk//tools:scaffold -- --lang rust --name my_rust_ext
```
{{#endtab }}
{{#tab name="Golang" }}
```bash
bazel run @extensions_sdk//tools:scaffold -- --lang go --name my_go_ext
```
{{#endtab }}
{{#tab name="Python" }}
```bash
bazel run @extensions_sdk//tools:scaffold -- --lang python --name my_py_ext
```
{{#endtab }}
{{#tab name="Javascript" }}
```bash
bazel run @extensions_sdk//tools:scaffold -- --lang js --name my_js_ext
```
{{#endtab }}
{{#endtabs }}

---

## 3. Extension Rules & Implementation

{{#tabs }}
{{#tab name="Rust" }}
### Generated `BUILD` Rule

The scaffolding tool generates a `BUILD` file using `rust_extension`:

```starlark
{{#include ../../wasm-extension-rs/examples/BUILD:build_rule}}
```

### Implementation

Extensions are represented by the `Extension` trait. You need to register your extension through the `init` function:

```rust
{{#include ../../wasm-extension-rs/examples/src/lib.rs:first_extension}}
```

### Build

```bash
bazel build //my_rust_ext:my_rust_ext
```
{{#endtab }}
{{#tab name="Golang" }}
### Generated `BUILD` Rule

The scaffolding tool generates a `BUILD` file using `go_extension`:

```starlark
{{#include ../../wasm-extension-go/examples/BUILD:build_rule}}
```

### Implementation

Extensions are represented by embedding `api.DefaultExtension`. You need to register your extension through the `entry` function:

```go
{{#include ../../wasm-extension-go/examples/main.go:first_extension}}
```

### Build

```bash
bazel build //my_go_ext:my_go_ext
```
{{#endtab }}
{{#tab name="Python" }}
### Generated `BUILD` Rule

The scaffolding tool generates a `BUILD` file using `py_extension`:

```starlark
{{#include ../../wasm-extension-py/examples/BUILD:build_rule}}
```

### Implementation

All extensions must start in a module called `main`. Extensions are represented by the `Extension` class. You need to register your extension through the `entry` function:

```python
{{#include ../../wasm-extension-py/examples/main.py:first_extension}}
```

### Build

```bash
bazel build //my_py_ext:my_py_ext
```
{{#endtab }}
{{#tab name="Javascript" }}
### Generated `BUILD` Rule

The scaffolding tool generates a `BUILD` file using `js_extension`:

```starlark
{{#include ../../wasm-extension-js/examples/BUILD:build_rule}}
```

### Implementation

You need to re-export all methods provided by `wasm-extension-js` package. The entrypoint of your extension is a function called `entry`:

```typescript
{{#include ../../wasm-extension-js/examples/src/index.ts:first_extension}}
```

### Build

```bash
bazel build //my_js_ext:my_js_ext
```
{{#endtab }}
{{#endtabs }}

---

## 4. Making HTTP Requests

Extensions can make outgoing HTTP requests through the host runner using the SDK's HTTP APIs. Both single requests and batch/parallel requests are supported.

> **Permissions**: To communicate with external servers, specify allowed hosts in your extension manifest (`package.json`) under `"allowed_hosts"` (for example, `["api.spotify.com", "*.last.fm"]`).

{{#tabs }}
{{#tab name="Rust" }}
```rust
{{#include ../../wasm-extension-rs/examples/src/lib.rs:http_usage}}
```
{{#endtab }}
{{#tab name="Golang" }}
```go
{{#include ../../wasm-extension-go/examples/main.go:http_usage}}
```
{{#endtab }}
{{#tab name="Python" }}
```python
{{#include ../../wasm-extension-py/examples/main.py:http_usage}}
```
{{#endtab }}
{{#tab name="Javascript" }}
```typescript
{{#include ../../wasm-extension-js/examples/src/index.ts:http_usage}}
```
{{#endtab }}
{{#endtabs }}

