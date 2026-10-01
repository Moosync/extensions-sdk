load("//tools:defs.bzl", "pytest_test")
load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@pypi_moounit//:requirements.bzl", "requirement")

def moounit_test(
        name,
        deps = [],
        data = [],
        args = [],
        extension = None,
        debug = False,
        expectations_file = "expectations.json",
        **kwargs):
    """
    Wrapper around pytest_test that automatically adds moounit dependencies
    and supports record/replay mode.
    """

    test_args = list(args)
    test_data = list(data)

    if debug:
        test_args = test_args + ["-s"]

    if extension:
        test_args = test_args + ["--extension-path='$(locations %s)'" % extension]
        test_data = test_data + [extension]

    file_matches = native.glob([expectations_file], allow_empty = True) if expectations_file else []
    if file_matches:
        test_args = test_args + ["--expectations-file=$(location %s)" % expectations_file]
        test_data = test_data + [expectations_file]

    pytest_test(
        name = name,
        deps = deps + [
            Label("//moounit:moounit"),
        ],
        data = test_data + [
            Label("//moounit:moounit_pyi"),
            Label("//moounit:moounit"),
        ],
        args = test_args,
        **kwargs
    )

    # Generate a runnable record binary target: <name>_record
    srcs = kwargs.get("srcs", [])
    record_args = [
        "--record",
        "-p",
        "moounit.pytest_plugin",
    ]
    if expectations_file:
        package_prefix = native.package_name()
        file_path = package_prefix + "/" + expectations_file if package_prefix else expectations_file
        record_args = record_args + ["--expectations-file=" + file_path]

    if extension:
        record_args = record_args + ["--extension-path='$(locations %s)'" % extension]

    record_args = record_args + ["$(location :%s)" % x for x in srcs]

    py_binary(
        name = name + "_record",
        srcs = [
            Label("//tools:pytest_wrapper.py"),
        ] + srcs,
        main = Label("//tools:pytest_wrapper.py"),
        args = record_args,
        deps = deps + [
            Label("//moounit:moounit"),
            requirement("pytest"),
            requirement("pytest-black"),
            requirement("pytest-pylint"),
        ],
        data = test_data + [
            Label("//moounit:moounit_pyi"),
            Label("//moounit:moounit"),
            Label("//tools:.pylintrc"),
        ],
    )
