# Required implementations

All extensions must return ProviderScopes. These scopes determine which events are sent to your extension.

Lets consider the `search` scope for this example. Adding the search scope would cause the main app to request search results from your extension.

{{#tabs }}
{{#tab name="Rust" }}
```rust
impl Provider for SampleExtension {
{{#include ../../wasm-extension-rs/examples/src/lib.rs:provider}}
}
```
{{#endtab }}
{{#tab name="Golang" }}
```go
{{#include ../../wasm-extension-go/examples/main.go:provider}}
```
{{#endtab }}
{{#tab name="Python" }}
```python
{{#include ../../wasm-extension-py/examples/main.py:provider}}
```
{{#endtab }}
{{#tab name="Javascript" }}
```typescript
{{#include ../../wasm-extension-js/examples/src/index.ts:provider}}
```
{{#endtab }}
{{#endtabs }}
