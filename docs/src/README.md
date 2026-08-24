# Introduction

Moosync lets you create your own extensions to extent the functionality for the main app.
Extensions are web-assembly modules that can be loaded at runtime.

## Restrictions
Web assembly is platform independant and has a few restrictions:
- Limited access to the file system
- Limited access to the network
- No support for threads (tracking [wasi-threads](https://github.com/WebAssembly/wasi-threads))
- No support for native libraries


## Development
Moosync uses [extism](https://extism.org/) under the hood to load web assembly modules. Any host language supported by extism can be used to write extensions. Currently we only provide support for
- Rust
- Golang
- Javascript / Typescript
- Python
