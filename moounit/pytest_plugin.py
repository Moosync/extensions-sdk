import os

import pytest
from extism.extism import set_log_custom

from moounit.core import Moounit, current_scope
from moounit.models import Scope
from moounit.recorder import Recorder


def pytest_configure(config):
    """
    Configure pytest to fail on unraisable exceptions (e.g. from CFFI callbacks).
    """
    config.addinivalue_line(
        "filterwarnings", "error::pytest.PytestUnraisableExceptionWarning"
    )


def pytest_addoption(parser):
    """
    Add CLI options for extension path, record mode, and expectations file.
    """
    parser.addoption(
        "--extension-path",
        action="store",
        default=None,
        help="Path to the extension to test",
    )
    parser.addoption(
        "--record",
        action="store_true",
        default=False,
        help="Run in record mode to record host requests and responses",
    )
    parser.addoption(
        "--expectations-file",
        action="store",
        default=None,
        help="Path to expectations.json file",
    )


@pytest.fixture(scope="session")
def moounit_recorder(request):
    record_mode = request.config.getoption("--record", default=False)
    expectations_file = request.config.getoption("--expectations-file", default=None)

    if not expectations_file:
        test_dir = os.path.dirname(str(request.config.rootdir))
        default_file = os.path.join(test_dir, "expectations.json")
        if record_mode or os.path.exists(default_file):
            expectations_file = default_file

    recorder = Recorder(
        record_mode=record_mode,
        expectations_file=expectations_file,
    )
    yield recorder
    if record_mode:
        recorder.save_recorded_expectations()


@pytest.fixture(autouse=True)
def moounit_session(request, moounit_recorder):
    """
    Pytest fixture to manage Moounit expectation scopes and track test names.
    Sets the scope to LOCAL for each test function and clears local expectations afterwards.
    """
    test_name = request.node.name
    moounit_recorder.set_current_test(test_name)
    token = current_scope.set(Scope.LOCAL)
    yield
    current_scope.reset(token)
    moounit_recorder.clear_current_test()
    moounit_recorder.clear_local_replay_ignore_rules()
    for instance in Moounit._instances.values():
        instance._check_host_exception()
        instance.verify_and_clear_local_expectations()


logs_buf = []


def logs(s: str):
    global logs_buf
    if logs_buf is None:
        logs_buf = []
    logs_buf.append(s.strip())


log_buffer = set_log_custom(logs, "debug")


@pytest.fixture
def moounit(
    request, moounit_session, moounit_recorder
):  # pylint: disable=unused-argument
    """
    Pytest fixture to provide a Moounit instance configured via CLI.
    """
    path: str = request.config.getoption("--extension-path")
    if path:
        path = path.split(" ")[0]
    if not path:
        pytest.fail("--extension-path CLI option is required")

    if not os.path.exists(path):
        pytest.fail(f"Extension not found at {path}")

    if os.path.isfile(path):
        path = os.path.dirname(path)

    instance = Moounit(path, recorder=moounit_recorder)
    print(f"[moounit fixture] created instance {id(instance)} for {request.node.name}")

    try:
        yield instance
    finally:
        instance.close()
        log_buffer.drain()

        for line in logs_buf:
            print(line)
        logs_buf.clear()
