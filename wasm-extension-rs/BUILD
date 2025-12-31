load("@rules_rust//rust:defs.bzl", "rust_library")

rust_library(
    name = "app_lib",
    srcs = [
        "src/api.rs",
        "src/handler.rs",
        "src/lib.rs"
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//core/types",
        "@crates//:extism-pdk",
         "@crates//:lazy_static",
         "@crates//:serde",
          "@crates//:serde_json",
          "@crates//:tracing",
          "@crates//:extism-convert",
    ],
)