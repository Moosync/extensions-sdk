load("//tools:defs.bzl", "pytest_test")

def moounit_test(name, deps = [], data = [], args = [], extension = None, debug = False, **kwargs):
    """
    Wrapper around pytest_test that automatically adds moounit dependencies.
    """

    if debug:
        args = args + ["-s"]

    if extension:
        args = args + ["--extension-path='$(locations %s)'" % extension]
        data = data + [extension]

    pytest_test(
        name = name,
        deps = deps + [
            Label("//moounit:moounit"),
        ],
        data = data + [
            Label("//moounit:moounit_pyi"),
            Label("//moounit:moounit"),
        ],
        args = args,
        **kwargs
    )
