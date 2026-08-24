# Using the API

The extension development kit provides APIs to interact with the main app and perform external network operations.

## Fetching App State

For this example lets consider the `getCurrentSong` API.
`getCurrentSong` returns the actively playing song.

{{#tabs }}
{{#tab name="Rust" }}
```rust
impl Provider for SampleExtension {
{{#include ../../wasm-extension-rs/examples/src/lib.rs:api_usage}}
}
```
{{#endtab }}
{{#tab name="Golang" }}
```go
{{#include ../../wasm-extension-go/examples/main.go:api_usage}}
```
{{#endtab }}
{{#tab name="Python" }}
```python
{{#include ../../wasm-extension-py/examples/main.py:api_usage}}
```
{{#endtab }}
{{#tab name="Javascript" }}
```typescript
{{#include ../../wasm-extension-js/examples/src/index.ts:api_usage}}
```
{{#endtab }}
{{#endtabs }}

---

## Making HTTP Requests

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

