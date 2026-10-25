# Getting started

## Bazel setup

### Using the moosync-ext repo

The moosync-ext repo is already setup, you may skip to [the next step](#creating-a-new-extension).

### Starting in a new repository

In your workspace root, create or update `MODULE.bazel` to depend on `extensions_sdk`:

```starlark
module(
    name = "my_extensions", # Name for your workspace
    version = "1.0.0",
)

bazel_dep(name = "extensions_sdk", version = "1.0.0")
git_override(
    module_name = "extensions_sdk",
    branch = "main",
    remote = "https://github.com/Moosync/extensions-sdk",
) # Pull the extension sdk from git
```

## Creating a new extension

### Using Scaffold tool

The extension SDK repo provides a tool called `scaffold`. This tool can generate a new extension for you in one of the following languages:

- TypeScript (`ts`)
- Golang (`go`)
- Python (`py`)
- Rust (`rs`)

```sh
bazel run @extensions_sdk//tools:scaffold -- --lang py --name my_extension
```

Scaffold will generate your new extension in a new directory. It will also generate additional files like `lang.MODULE.bazel`, `dependencies.MODULE.bazel` and update your existing MODULE.bazel to setup language toolchains and other required deps.

#### Configuring the extension

Head over to the `BUILD` in your newly generated extension directory. You may see something like

````starlark
js_extension(
    name = "my_extension",
    srcs = ["src/index.ts"],
    package_name = "moosync.my_extension",
    display_name = "My extension",
    allowed_hosts = [],
    allowed_paths = {},
    version = "0.0.1",
)

- `name`: A unique identifier for your extension's build rule.
- `version`: The version of your extension in semver format.
- `icon`: The icon of your extension. The path is relative to `package.json`.
- `display_name`: The name of your extension that will be displayed in the UI.
- `allowed_hosts`: The hosts (URLs) that your extension needs to access.
- `allowed_paths`: The paths that your extension needs to access. You can use environment variables in the path. The environment variable must be wrapped in `{}`. For example, `{ENV_1}` will be replaced with the value of `ENV_1` environment variable.

    Keys in the `paths` object is the location in the user's filesystem.
    Values in the `paths` object is where the actual directory will be accessible in the extension.
    Eg.

    ```json
    "paths": {
      "/test": "/"
    }
    ```

    To access `/test/file.txt` in the extension, you can use the path `/file.txt`.
````
