# Using the API

The extension development kit provides APIs to fetch data from the main app.

For this example lets consider the `getCurrentSong` API.
`getCurrentSong` returns the actively playling song.

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
