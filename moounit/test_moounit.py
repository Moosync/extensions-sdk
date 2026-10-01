# pylint: disable=unused-import,too-many-locals,protected-access,no-member,too-few-public-methods
import json
import pytest
from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    GetSecureRequest,
    GetSecureResponse,
    GetSongRequest,
    GetSongResponse,
    HttpRequest,
    HttpResponse,
    HttpResult,
    MainCommand,
    MainCommandResponse,
    PreferenceData,
)
from core.types.protos.songs_pb2 import GetSongOptions, Song
from moounit.defaults import (
    default_batch_http_response,
    default_hash,
    default_main_command_response,
    default_open_clientfd,
    default_read_sock,
    default_system_time,
    default_write_sock,
)
from moounit.expectations import ExpectationManager, current_scope
from moounit.matcher import partial_match
from moounit.models import Scope
from moounit.recorder import Recorder, _matches_filter


def test_defaults():
    cmd = MainCommand(get_song=GetSongRequest(options=GetSongOptions()))
    resp = default_main_command_response(cmd)
    assert resp.WhichOneof("response") == "get_song"

    sec_cmd = MainCommand(
        get_secure=GetSecureRequest(data=PreferenceData(key="my_token"))
    )
    sec_resp = default_main_command_response(sec_cmd)
    assert sec_resp.WhichOneof("response") == "get_secure"
    assert sec_resp.get_secure.data.key == "my_token"

    http_req = BatchHttpRequest(
        requests=[HttpRequest(url="https://example.com", method="GET")]
    )
    http_resp = default_batch_http_response(http_req)
    assert len(http_resp.responses) == 1
    assert http_resp.responses[0].response.status_code == 200


def test_matcher_with_ignored_fields():
    req1 = BatchHttpRequest(
        requests=[HttpRequest(url="https://example.com/v1?token=123", method="GET")]
    )
    req2 = BatchHttpRequest(
        requests=[HttpRequest(url="https://example.com/v1?token=456", method="GET")]
    )

    # Without ignore: mismatch with colored diff
    matched, err = partial_match(req1, req2, root_call="batch_http_request")
    assert not matched
    assert "requests[0].url" in err or "requests.url" in err
    assert "replay_ignore" in err
    assert "\033[" in err  # ANSI colored diff present

    # With ignore: match succeeds
    matched, err = partial_match(req1, req2, ignored_fields=["requests.url"])
    assert matched
    assert err is None


def test_matcher_with_regex_ignored_fields():
    # Value regex ignoring visitorData in request body while treating body as string
    body1 = b'{"client": {"visitorData": "VISITOR_111", "name": "web"}}'
    body2 = b'{"client": {"visitorData": "VISITOR_222", "name": "web"}}'
    body3 = b'{"client": {"visitorData": "VISITOR_222", "name": "mobile"}}'

    req1 = BatchHttpRequest(
        requests=[HttpRequest(url="https://example.com", method="POST", body=body1)]
    )
    req2 = BatchHttpRequest(
        requests=[HttpRequest(url="https://example.com", method="POST", body=body2)]
    )
    req3 = BatchHttpRequest(
        requests=[HttpRequest(url="https://example.com", method="POST", body=body3)]
    )

    regex_rule = r'"visitorData":\s*"[^"]*"'

    # Dict format ignore rule
    matched, err = partial_match(
        req1,
        req2,
        ignored_fields=[{"path": "requests.body", "regex": regex_rule}],
        root_call="batch_http_request",
    )
    assert matched
    assert err is None

    # String format ignore rule: requests.body[regex:...]
    matched, err = partial_match(
        req1,
        req2,
        ignored_fields=[f"requests.body[regex:{regex_rule}]"],
        root_call="batch_http_request",
    )
    assert matched
    assert err is None

    # String format ignore rule: requests.body["visitorData":\s*"[^"]*"]
    matched, err = partial_match(
        req1,
        req2,
        ignored_fields=[f"requests.body[{regex_rule}]"],
        root_call="batch_http_request",
    )
    assert matched
    assert err is None

    # Should still fail if other parts of body differ, and return colored diff
    matched, err = partial_match(
        req1,
        req3,
        ignored_fields=[{"path": "requests.body", "regex": regex_rule}],
        root_call="batch_http_request",
    )
    assert not matched
    assert "requests[0].body" in err
    assert "\033[31m" in err  # Red for deleted/expected
    assert "\033[32m" in err  # Green for added/actual


def test_recorder_flow(tmp_path):
    expectations_path = str(tmp_path / "expectations.json")
    recorder = Recorder(record_mode=True, expectations_file=expectations_path)

    cmd_session = MainCommand(get_song=GetSongRequest(options=GetSongOptions()))
    resp_session = MainCommandResponse(get_song=GetSongResponse(songs=[Song()]))

    # Record in session scope
    recorder.record_call("send_main_command", cmd_session, resp_session, Scope.SESSION)

    # Record in test scope
    recorder.set_current_test("test_custom_method")
    cmd_test = MainCommand(
        get_secure=GetSecureRequest(data=PreferenceData(key="secret"))
    )
    resp_test = MainCommandResponse(
        get_secure=GetSecureResponse(data=PreferenceData(key="secret"))
    )
    recorder.record_call("send_main_command", cmd_test, resp_test, Scope.LOCAL)
    recorder.clear_current_test()

    recorder.save_recorded_expectations()

    # Verify JSON structure
    with open(expectations_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "session" not in data
        assert "tests" in data
        assert "test_custom_method" in data["tests"]
        assert len(data["tests"]["test_custom_method"]) == 2

    # Replay
    replay_recorder = Recorder(record_mode=False, expectations_file=expectations_path)
    replay_recorder.set_current_test("test_custom_method")

    # Replay first call (which was recorded in session scope)
    res, err = replay_recorder.match_and_consume_replay(
        "send_main_command", cmd_session, Scope.LOCAL
    )
    assert err is None
    assert isinstance(res, MainCommandResponse)
    assert res.WhichOneof("response") == "get_song"

    # Replay second call (which was recorded in test scope)
    res_local, err_local = replay_recorder.match_and_consume_replay(
        "send_main_command", cmd_test, Scope.LOCAL
    )
    assert err_local is None
    assert isinstance(res_local, MainCommandResponse)
    assert res_local.WhichOneof("response") == "get_secure"


def test_replay_ignore_batch_http_request_header(tmp_path):
    expectations_path = str(tmp_path / "expectations.json")
    recorder = Recorder(record_mode=True, expectations_file=expectations_path)

    recorder.set_current_test("test_search")
    recorded_req = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/search?q=rust",
                method="GET",
                headers={"user-agent": "Agent-v1.0", "accept": "text/html"},
            )
        ]
    )
    resp = BatchHttpResponse(
        responses=[HttpResult(response=HttpResponse(status_code=200, status_text="OK"))]
    )
    recorder.record_call("batch_http_request", recorded_req, resp, Scope.LOCAL)
    recorder.clear_current_test()
    recorder.save_recorded_expectations()

    # Replay with mismatched user-agent
    incoming_req = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/search?q=rust",
                method="GET",
                headers={"user-agent": "Agent-v2.0", "accept": "text/html"},
            )
        ]
    )

    # Without ignore rule: fails
    replay = Recorder(record_mode=False, expectations_file=expectations_path)
    replay.set_current_test("test_search")
    res, err = replay.match_and_consume_replay(
        "batch_http_request", incoming_req, Scope.LOCAL
    )
    assert res is None
    assert err is not None

    # With replay_ignore: succeeds
    replay = Recorder(record_mode=False, expectations_file=expectations_path)
    replay.set_current_test("test_search")
    replay.replay_ignore(
        request=BatchHttpRequest(requests=[HttpRequest(url="www.google.com")]),
        ignore_field=["headers.user-agent"],
    )
    res, err = replay.match_and_consume_replay(
        "batch_http_request", incoming_req, Scope.LOCAL
    )
    assert err is None
    assert isinstance(res, BatchHttpResponse)
    assert res.responses[0].response.status_code == 200


def test_replay_ignore_times_limit(tmp_path):
    expectations_path = str(tmp_path / "expectations.json")
    recorder = Recorder(record_mode=True, expectations_file=expectations_path)

    recorder.set_current_test("test_search")
    req1 = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/api/v1",
                method="GET",
                headers={"user-agent": "v1"},
            )
        ]
    )
    req2 = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/api/v2",
                method="GET",
                headers={"user-agent": "v1"},
            )
        ]
    )
    resp = BatchHttpResponse(
        responses=[HttpResult(response=HttpResponse(status_code=200))]
    )
    recorder.record_call("batch_http_request", req1, resp, Scope.LOCAL)
    recorder.record_call("batch_http_request", req2, resp, Scope.LOCAL)
    recorder.clear_current_test()
    recorder.save_recorded_expectations()

    # Replay: rule only configured for times(1)
    replay = Recorder(record_mode=False, expectations_file=expectations_path)
    replay.set_current_test("test_search")
    replay.replay_ignore(
        request=HttpRequest(url="www.google.com"),
        ignore_field=["headers.user-agent"],
    ).times(1)

    # First call: mismatched user-agent is ignored
    incoming1 = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/api/v1",
                method="GET",
                headers={"user-agent": "v2"},
            )
        ]
    )
    res1, err1 = replay.match_and_consume_replay(
        "batch_http_request", incoming1, Scope.LOCAL
    )
    assert err1 is None
    assert res1 is not None

    # Second call: times(1) exhausted, so mismatched user-agent causes failure
    incoming2 = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/api/v2",
                method="GET",
                headers={"user-agent": "v2"},
            )
        ]
    )
    res2, err2 = replay.match_and_consume_replay(
        "batch_http_request", incoming2, Scope.LOCAL
    )
    assert res2 is None
    assert err2 is not None


def test_replay_ignore_regex_body(tmp_path):
    expectations_path = str(tmp_path / "expectations.json")
    recorder = Recorder(record_mode=True, expectations_file=expectations_path)

    recorder.set_current_test("test_search")
    body_recorded = b'{"system_time": 1000000000, "client": "web", "version": "1.0"}'
    recorded_req = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/search",
                method="POST",
                body=body_recorded,
            )
        ]
    )
    resp = BatchHttpResponse(
        responses=[HttpResult(response=HttpResponse(status_code=200))]
    )
    recorder.record_call("batch_http_request", recorded_req, resp, Scope.LOCAL)
    recorder.clear_current_test()
    recorder.save_recorded_expectations()

    # Replay with different system_time in body
    body_incoming = b'{"system_time": 9999999999, "client": "web", "version": "1.0"}'
    incoming_req = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/search",
                method="POST",
                body=body_incoming,
            )
        ]
    )

    replay = Recorder(record_mode=False, expectations_file=expectations_path)
    replay.set_current_test("test_search")
    replay.replay_ignore(
        request=BatchHttpRequest(requests=[HttpRequest(url="www.google.com")]),
        ignore_field=["body"],
        regex=r'"system_time":\s*\d+',
    )

    res, err = replay.match_and_consume_replay(
        "batch_http_request", incoming_req, Scope.LOCAL
    )
    assert err is None
    assert res is not None

    # Should still fail if client differs
    body_bad = b'{"system_time": 9999999999, "client": "mobile", "version": "1.0"}'
    incoming_bad = BatchHttpRequest(
        requests=[
            HttpRequest(
                url="https://www.google.com/search",
                method="POST",
                body=body_bad,
            )
        ]
    )
    replay2 = Recorder(record_mode=False, expectations_file=expectations_path)
    replay2.set_current_test("test_search")
    replay2.replay_ignore(
        request=BatchHttpRequest(requests=[HttpRequest(url="www.google.com")]),
        ignore_field=["body"],
        regex=r'"system_time":\s*\d+',
    )
    res_bad, err_bad = replay2.match_and_consume_replay(
        "batch_http_request", incoming_bad, Scope.LOCAL
    )
    assert res_bad is None
    assert err_bad is not None


def test_replay_ignore_test_name_scoping(tmp_path):
    expectations_path = str(tmp_path / "expectations.json")
    recorder = Recorder(record_mode=True, expectations_file=expectations_path)

    # Record test_search
    recorder.set_current_test("test_search")
    req = BatchHttpRequest(
        requests=[HttpRequest(url="https://www.google.com", headers={"token": "t1"})]
    )
    resp = BatchHttpResponse(
        responses=[HttpResult(response=HttpResponse(status_code=200))]
    )
    recorder.record_call("batch_http_request", req, resp, Scope.LOCAL)
    recorder.clear_current_test()

    # Record test_other
    recorder.set_current_test("test_other")
    recorder.record_call("batch_http_request", req, resp, Scope.LOCAL)
    recorder.clear_current_test()

    recorder.save_recorded_expectations()

    # Replay test_search with rule registered specifically for test_search
    replay = Recorder(record_mode=False, expectations_file=expectations_path)
    replay.set_current_test("test_search")
    replay.replay_ignore(
        request=HttpRequest(url="www.google.com"),
        ignore_field=["headers.token"],
        test_name="test_search",
    )

    incoming = BatchHttpRequest(
        requests=[HttpRequest(url="https://www.google.com", headers={"token": "t2"})]
    )
    res_search, err_search = replay.match_and_consume_replay(
        "batch_http_request", incoming, Scope.LOCAL
    )
    assert err_search is None
    assert res_search is not None

    # In test_other: the rule for test_search does NOT apply, so it fails
    replay.clear_local_replay_ignore_rules()
    replay.set_current_test("test_other")
    res_other, err_other = replay.match_and_consume_replay(
        "batch_http_request", incoming, Scope.LOCAL
    )
    assert res_other is None
    assert err_other is not None


def test_replay_ignore_main_command(tmp_path):
    expectations_path = str(tmp_path / "expectations.json")
    recorder = Recorder(record_mode=True, expectations_file=expectations_path)

    recorder.set_current_test("test_secure")
    recorded_cmd = MainCommand(
        get_secure=GetSecureRequest(data=PreferenceData(key="api_key_v1"))
    )
    resp = MainCommandResponse(
        get_secure=GetSecureResponse(data=PreferenceData(key="api_key_v1"))
    )
    recorder.record_call("send_main_command", recorded_cmd, resp, Scope.LOCAL)
    recorder.clear_current_test()
    recorder.save_recorded_expectations()

    # Replay with different key
    incoming_cmd = MainCommand(
        get_secure=GetSecureRequest(data=PreferenceData(key="api_key_v2"))
    )

    replay = Recorder(record_mode=False, expectations_file=expectations_path)
    replay.set_current_test("test_secure")
    replay.replay_ignore(
        request=MainCommand(get_secure=GetSecureRequest()),
        ignore_field=["get_secure.data.key"],
    )

    res, err = replay.match_and_consume_replay(
        "send_main_command", incoming_cmd, Scope.LOCAL
    )
    assert err is None
    assert isinstance(res, MainCommandResponse)
    assert res.get_secure.data.key == "api_key_v1"


def test_replay_ignore_other_calls(tmp_path):
    expectations_path = str(tmp_path / "expectations.json")
    recorder = Recorder(record_mode=True, expectations_file=expectations_path)
    recorder.set_current_test("test_primitives")

    recorder.record_call("open_clientfd", "/var/run/moosync.sock", 10, Scope.LOCAL)
    recorder.record_call("write_sock", {"sock_id": 10, "buf": b"data"}, 4, Scope.LOCAL)
    recorder.record_call(
        "read_sock", {"sock_id": 10, "read_len": 4}, b"resp", Scope.LOCAL
    )
    recorder.record_call(
        "hash", {"hash_type": "sha256", "data": b"secret"}, b"hashval", Scope.LOCAL
    )
    recorder.record_call("system_time", {}, 12345, Scope.LOCAL)

    recorder.clear_current_test()
    recorder.save_recorded_expectations()

    replay = Recorder(record_mode=False, expectations_file=expectations_path)
    replay.set_current_test("test_primitives")

    # open_clientfd
    res, err = replay.match_and_consume_replay(
        "open_clientfd", "/var/run/moosync.sock", Scope.LOCAL
    )
    assert err is None and res == 10

    # write_sock
    res, err = replay.match_and_consume_replay(
        "write_sock", {"sock_id": 10, "buf": b"data"}, Scope.LOCAL
    )
    assert err is None and res == 4

    # read_sock
    res, err = replay.match_and_consume_replay(
        "read_sock", {"sock_id": 10, "read_len": 4}, Scope.LOCAL
    )
    assert err is None and res == b"resp"

    # hash
    res, err = replay.match_and_consume_replay(
        "hash", {"hash_type": "sha256", "data": b"secret"}, Scope.LOCAL
    )
    assert err is None and res == b"hashval"

    # system_time
    res, err = replay.match_and_consume_replay("system_time", {}, Scope.LOCAL)
    assert err is None and res == 12345


class FakeMoounit:
    def __init__(self, mapped_paths=None):
        self.passthrough = False
        self._mapped_paths = mapped_paths or {}
        self.socket_manager = None

    def send_command(self, _command):
        return None


def test_expect_command_and_handle_main_command():
    manager = ExpectationManager(recorder=Recorder(record_mode=False))
    cmd = MainCommand(get_song=GetSongRequest(options=GetSongOptions()))
    expected_resp = MainCommandResponse(get_song=GetSongResponse(songs=[Song()]))
    manager.expect_command(cmd, expected_resp)

    # Matching command returns expected response
    res_bytes = manager.handle_main_command(cmd.SerializeToString())
    res = MainCommandResponse.FromString(res_bytes)
    assert res.WhichOneof("response") == "get_song"
    assert len(res.get_song.songs) == 1

    # Unmatched command in replay mode raises AssertionError
    wrong_cmd = MainCommand(
        get_secure=GetSecureRequest(data=PreferenceData(key="secret"))
    )
    with pytest.raises(AssertionError, match="Unexpected command"):
        manager.handle_main_command(wrong_cmd.SerializeToString())

    # In record mode, unmatched command falls back to default response
    rec_manager = ExpectationManager(recorder=Recorder(record_mode=True))
    rec_res_bytes = rec_manager.handle_main_command(wrong_cmd.SerializeToString())
    rec_res = MainCommandResponse.FromString(rec_res_bytes)
    assert rec_res.WhichOneof("response") == "get_secure"


def test_default_response_fallback():
    fake = FakeMoounit()
    manager = ExpectationManager(recorder=Recorder(record_mode=True), moounit=fake)
    assert not manager.passthrough_enabled

    # system_time fallback to default_system_time
    assert manager._check_system_time() == default_system_time()

    # hash fallback to default_hash
    assert manager._check_hash("sha256", b"data") == default_hash("sha256", b"data")

    # open_clientfd fallback to default_open_clientfd
    assert manager._check_open_clientfd("test.sock") == default_open_clientfd(
        "test.sock"
    )

    # write_sock fallback to default_write_sock
    assert manager._check_write_sock(1, b"hello") == default_write_sock(1, b"hello")

    # read_sock fallback to default_read_sock
    assert manager._check_read_sock(1, 10) == default_read_sock(1, 10)

    # batch_http_request fallback to default_batch_http_response
    http_req = BatchHttpRequest(
        requests=[HttpRequest(url="https://fallback.example.com", method="GET")]
    )
    resp_bytes = manager._check_batch_http_request(http_req.SerializeToString())
    resp = BatchHttpResponse.FromString(resp_bytes)
    assert (
        resp.SerializeToString()
        == default_batch_http_response(http_req).SerializeToString()
    )


def test_callable_return_values():
    manager = ExpectationManager(recorder=Recorder(record_mode=False))

    # _get_value handles both callables and plain values
    assert manager._get_value(lambda: 42) == 42
    assert manager._get_value("static") == "static"

    # Local scope with callable
    token = current_scope.set(Scope.LOCAL)
    try:
        manager.expect_system_time(lambda: 99999)
        assert manager._check_system_time() == 99999
    finally:
        current_scope.reset(token)

    # Session scope with callable
    token = current_scope.set(Scope.SESSION)
    try:
        manager.expect_hash("sha256", b"call_test", lambda: b"dyn_hash")
        assert manager._check_hash("sha256", b"call_test") == b"dyn_hash"
    finally:
        current_scope.reset(token)


def test_recorder_filter():
    recorder = Recorder(record_mode=True, filter="target")

    # Call under non-matching test name should not be recorded
    recorder.set_current_test("other_test")
    recorder.record_call("system_time", {}, 100, Scope.LOCAL)
    assert "other_test" not in recorder.recorded_test_calls

    # Call under matching test name should be recorded
    recorder.set_current_test("my_target_test")
    recorder.record_call("system_time", {}, 200, Scope.LOCAL)
    assert len(recorder.recorded_test_calls["my_target_test"]) == 1
    assert recorder.recorded_test_calls["my_target_test"][0]["response"] == 200
    recorder.clear_current_test()

    # Direct testing of _matches_filter
    assert _matches_filter(None, "anything")
    assert _matches_filter("foo", "foobar")
    assert not _matches_filter("baz", "foobar")
    assert _matches_filter(b"part", b"full_part_byte")
    assert not _matches_filter(b"missing", b"full_part_byte")


def test_session_expectations_lifecycle():
    token = current_scope.set(Scope.SESSION)
    try:
        manager = ExpectationManager(recorder=Recorder(record_mode=False))
        manager.expect_system_time(100)

        # Unconsumed expectation raises AssertionError on verification
        with pytest.raises(
            AssertionError, match="Unused session system_time expectations"
        ):
            manager.verify_and_clear_session_expectations()

        # Re-add and consume
        manager.expect_system_time(100)
        assert manager._check_system_time() == 100
        # Verification passes when consumed
        manager.verify_and_clear_session_expectations()

        # clear_session_expectations empties unconsumed expectations
        manager.expect_system_time(200)
        manager.clear_session_expectations()
        manager.verify_and_clear_session_expectations()
    finally:
        current_scope.reset(token)


def test_get_mapped_paths():
    fake = FakeMoounit(mapped_paths={"/ext/data": "/tmp/moosync_test"})
    manager = ExpectationManager(moounit=fake)
    assert manager.get_mapped_paths() == {"/ext/data": "/tmp/moosync_test"}

    # Without moounit, returns empty dict
    manager_standalone = ExpectationManager(moounit=None)
    assert manager_standalone.get_mapped_paths() == {}


def test_verify_and_clear_local_expectations():
    token = current_scope.set(Scope.LOCAL)
    try:
        manager = ExpectationManager(recorder=Recorder(record_mode=False))
        manager.expect_system_time(500)

        # Unconsumed expectation raises AssertionError on verification
        with pytest.raises(AssertionError, match="Unused system_time expectations"):
            manager.verify_and_clear_local_expectations()

        # Re-add and consume
        manager.expect_system_time(500)
        assert manager._check_system_time() == 500
        # Verification passes when consumed
        manager.verify_and_clear_local_expectations()

        # In record mode, unconsumed expectations are cleared without error
        rec_manager = ExpectationManager(recorder=Recorder(record_mode=True))
        rec_manager.expect_system_time(600)
        rec_manager.verify_and_clear_local_expectations()
        assert len(rec_manager.local_system_time_expectations) == 0
    finally:
        current_scope.reset(token)
