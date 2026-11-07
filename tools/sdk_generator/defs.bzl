"""
Starlark rule for generating Moosync Extension SDK code from Protobuf RPC services.
"""

load("@rules_proto//proto:defs.bzl", "ProtoInfo")

def _generate_extension_sdk_impl(ctx):
    proto_info = ctx.attr.proto[ProtoInfo]
    transitive_descriptor_sets = proto_info.transitive_descriptor_sets.to_list()

    out_api = ctx.actions.declare_file(ctx.attr.out_api)
    out_dispatcher = ctx.actions.declare_file(ctx.attr.out_dispatcher)

    args = ctx.actions.args()
    args.add("--descriptor-sets")
    args.add_all([f.path for f in transitive_descriptor_sets])
    args.add("--templates-dir", ctx.file._templates_marker.dirname)
    args.add("--lang", ctx.attr.lang)
    args.add("--out-api", out_api.path)
    args.add("--out-dispatcher", out_dispatcher.path)

    ctx.actions.run(
        inputs = transitive_descriptor_sets + ctx.files.templates,
        outputs = [out_api, out_dispatcher],
        executable = ctx.executable._generator,
        arguments = [args],
        mnemonic = "GenExtensionSdk",
    )

    return [
        DefaultInfo(files = depset([out_api, out_dispatcher])),
        OutputGroupInfo(
            api = depset([out_api]),
            dispatcher = depset([out_dispatcher]),
        ),
    ]

generate_extension_sdk = rule(
    implementation = _generate_extension_sdk_impl,
    attrs = {
        "proto": attr.label(
            providers = [ProtoInfo],
            mandatory = True,
        ),
        "lang": attr.string(
            mandatory = True,
            values = ["rust", "ts", "go", "python"],
        ),
        "out_api": attr.string(mandatory = True),
        "out_dispatcher": attr.string(mandatory = True),
        "templates": attr.label_list(
            default = ["//tools/sdk_generator:all_templates"],
            allow_files = True,
        ),
        "_templates_marker": attr.label(
            default = "//tools/sdk_generator:templates_marker",
            allow_single_file = True,
        ),
        "_generator": attr.label(
            default = Label("//tools/sdk_generator:generator"),
            executable = True,
            cfg = "exec",
        ),
    },
)
