def package_extension(name, extension_target, visibility = None):
    native.genrule(
        name = name + "_msxt",
        srcs = [extension_target],
        outs = [name + ".msxt"],
        cmd = "zip -j $@ $(SRCS)",
        visibility = visibility or ["//visibility:public"],
    )
