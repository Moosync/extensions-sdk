# https://stackoverflow.com/a/67389568

load("@aspect_rules_py//py:defs.bzl", "py_test")
load("@pypi_moounit//:requirements.bzl", "requirement")

def pytest_test(name, srcs, deps = [], args = [], data = [], **kwargs):
    """
        Call pytest
    """
    pylint_rc = Label("//tools:.pylintrc")
    py_test(
        name = name,
        srcs = [
            Label("//tools:pytest_wrapper.py"),
        ] + srcs,
        main = Label("//tools:pytest_wrapper.py"),
        args = [
            "--black",
            "--pylint",
            "--pylint-rcfile=$(location %s)" % pylint_rc,
            "-p",
            "moounit.lib",
        ] + args + ["$(location :%s)" % x for x in srcs],
        deps = deps + [
            requirement("pytest"),
            requirement("pytest-black"),
            requirement("pytest-pylint"),
        ],
        data = [Label("//tools:.pylintrc")] + data,
        **kwargs
    )
