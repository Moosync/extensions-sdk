import contextvars
from collections.abc import Callable
from typing import Any

from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    MainCommand,
    MainCommandResponse,
)
from moounit.defaults import (
    default_batch_http_response,
    default_hash,
    default_main_command_response,
    default_open_clientfd,
    default_read_sock,
    default_system_time,
    default_write_sock,
)
from moounit.matcher import ReplayIgnoreBuilder, partial_match
from moounit.models import (
    BatchHttpRequestExpectation,
    Expectation,
    HashExpectation,
    OpenClientFdExpectation,
    ReadSockExpectation,
    Scope,
    SystemTimeExpectation,
    WriteSockExpectation,
)
from moounit.passthrough import (
    RealSocketManager,
    execute_real_batch_http_request,
    get_real_hash,
    get_real_system_time,
)
from moounit.recorder import Recorder

current_scope = contextvars.ContextVar("current_scope", default=Scope.SESSION)

ATTR_MAP: dict[str, tuple[str, str]] = {
    "command": ("local_expectations", "session_expectations"),
    "system_time": (
        "local_system_time_expectations",
        "session_system_time_expectations",
    ),
    "hash": ("local_hash_expectations", "session_hash_expectations"),
    "open_clientfd": (
        "local_open_clientfd_expectations",
        "session_open_clientfd_expectations",
    ),
    "write_sock": (
        "local_write_sock_expectations",
        "session_write_sock_expectations",
    ),
    "read_sock": (
        "local_read_sock_expectations",
        "session_read_sock_expectations",
    ),
    "batch_http_request": (
        "local_batch_http_request_expectations",
        "session_batch_http_request_expectations",
    ),
}


class ExpectationManager:
    def __init__(
        self,
        recorder: Recorder | None = None,
        moounit: Any | None = None,
    ):
        self.recorder = recorder or Recorder()
        self.moounit = moounit
        self._socket_manager: RealSocketManager | None = None

        for local_attr, session_attr in ATTR_MAP.values():
            setattr(self, local_attr, [])
            setattr(self, session_attr, [])

    @property
    def passthrough_enabled(self) -> bool:
        if self.moounit is None:
            return True
        return bool(getattr(self.moounit, "passthrough", False))

    @property
    def socket_manager(self) -> RealSocketManager | None:
        if self.moounit is not None:
            return getattr(self.moounit, "socket_manager", None)
        return self._socket_manager

    def _add_expectation(self, kind: str, exp: Any):
        local_attr, session_attr = ATTR_MAP[kind]
        target = getattr(
            self,
            local_attr if current_scope.get() == Scope.LOCAL else session_attr,
        )
        target.append(exp)

    def expect_command(
        self,
        command: MainCommand,
        response: MainCommandResponse | Callable[[], MainCommandResponse],
        times: int = 1,
    ):
        self._add_expectation(
            "command",
            Expectation(command=command, response=response, times=times),
        )

    def expect_system_time(
        self, return_value: int | Callable[[], int], times: int = 1
    ):
        self._add_expectation(
            "system_time",
            SystemTimeExpectation(return_value=return_value, times=times),
        )

    def expect_hash(
        self,
        hash_type: str,
        data: bytes,
        return_value: bytes | Callable[[], bytes],
        times: int = 1,
    ):
        self._add_expectation(
            "hash",
            HashExpectation(
                hash_type=hash_type,
                data=data,
                return_value=return_value,
                times=times,
            ),
        )

    def expect_open_clientfd(
        self, path: str, return_value: int | Callable[[], int], times: int = 1
    ):
        self._add_expectation(
            "open_clientfd",
            OpenClientFdExpectation(
                path=path, return_value=return_value, times=times
            ),
        )

    def expect_write_sock(
        self,
        sock_id: int,
        buf: bytes = b"",
        return_value: int | Callable[[], int] = 0,
        times: int = 1,
    ):
        self._add_expectation(
            "write_sock",
            WriteSockExpectation(
                sock_id=sock_id,
                buf=buf,
                return_value=return_value,
                times=times,
            ),
        )

    def expect_read_sock(
        self,
        sock_id: int,
        read_len: int = 0,
        return_value: bytes | Callable[[], bytes] = b"",
        times: int = 1,
    ):
        self._add_expectation(
            "read_sock",
            ReadSockExpectation(
                sock_id=sock_id,
                read_len=read_len,
                return_value=return_value,
                times=times,
            ),
        )

    def expect_batch_http_request(
        self,
        requests: BatchHttpRequest,
        response: BatchHttpResponse | Callable[[], BatchHttpResponse],
        times: int = 1,
    ):
        self._add_expectation(
            "batch_http_request",
            BatchHttpRequestExpectation(
                requests=requests, response=response, times=times
            ),
        )

    def replay_ignore(
        self,
        request: Any,
        ignore_fields: list[str] | str | None = None,
        ignore_field: list[str] | str | None = None,
        regex: str | None = None,
        test_name: str | None = None,
    ) -> ReplayIgnoreBuilder:
        if current_scope.get() == Scope.LOCAL:
            return self.recorder.replay_ignore(
                request=request,
                ignore_fields=ignore_fields,
                ignore_field=ignore_field,
                regex=regex,
                test_name=test_name,
            )
        return self.recorder.session_replay_ignore(
            request=request,
            ignore_fields=ignore_fields,
            ignore_field=ignore_field,
            regex=regex,
            test_name=test_name,
        )

    def clear_local_expectations(self):
        for local_attr, _ in ATTR_MAP.values():
            getattr(self, local_attr).clear()

    def verify_and_clear_local_expectations(self):
        if self.recorder.record_mode:
            self.clear_local_expectations()
            return

        errors = [
            f"Unused {kind} expectations: {[e for e in getattr(self, local_attr) if e.times > 0]}"
            for kind, (local_attr, _) in ATTR_MAP.items()
            if any(e.times > 0 for e in getattr(self, local_attr))
        ]
        self.clear_local_expectations()
        if errors:
            raise AssertionError("\n".join(errors))

    def clear_session_expectations(self):
        for _, session_attr in ATTR_MAP.values():
            getattr(self, session_attr).clear()

    def verify_and_clear_session_expectations(self):
        if self.recorder.record_mode:
            self.clear_session_expectations()
            return

        errors = [
            f"Unused session {kind} expectations: {[e for e in getattr(self, session_attr) if e.times > 0]}"
            for kind, (_, session_attr) in ATTR_MAP.items()
            if any(e.times > 0 for e in getattr(self, session_attr))
        ]
        self.clear_session_expectations()
        if errors:
            raise AssertionError("\n".join(errors))

    def _get_value(self, val: Any | Callable[[], Any]) -> Any:
        if callable(val):
            return val()
        return val

    def _consume_expectation(
        self,
        local_list: list[Any],
        session_list: list[Any],
        matcher: Callable[[Any], bool],
    ) -> Any | None:
        for exp in local_list + session_list:
            if matcher(exp):
                if exp.times >= 0:
                    exp.times -= 1
                    if exp.times <= 0:
                        if exp in local_list:
                            local_list.remove(exp)
                        else:
                            session_list.remove(exp)
                return exp
        return None

    def _replay_or_fail(
        self, call_type: str, request_obj: Any, default_error_msg: str
    ) -> Any:
        scope = current_scope.get()
        if self.recorder.has_replay_expectations(scope):
            resp, err = self.recorder.match_and_consume_replay(
                call_type, request_obj, scope
            )
            if resp is not None:
                return resp
            if err and not self.recorder.has_replay_expectations(Scope.SESSION):
                raise AssertionError(err)

        if scope == Scope.LOCAL and self.recorder.has_replay_expectations(
            Scope.SESSION
        ):
            resp, err = self.recorder.match_and_consume_replay(
                call_type, request_obj, Scope.SESSION
            )
            if resp is not None:
                return resp
            if err:
                raise AssertionError(err)

        raise AssertionError(default_error_msg)

    def _dispatch(
        self,
        kind: str,
        local_list: list[Any],
        session_list: list[Any],
        matcher: Callable[[Any], bool],
        req_info: Any,
        passthrough_fn: Callable[[], Any] | None,
        default_fn: Callable[[], Any],
        record_name: str,
        error_msg: str | None = None,
    ) -> Any:
        scope = current_scope.get()
        exp = self._consume_expectation(local_list, session_list, matcher)
        if exp is not None:
            ret = self._get_value(
                getattr(exp, "return_value", getattr(exp, "response", None))
            )
        elif self.recorder.record_mode:
            if self.passthrough_enabled and passthrough_fn is not None:
                try:
                    ret = passthrough_fn()
                except Exception:
                    ret = default_fn()
                if ret is None or (
                    isinstance(ret, int)
                    and ret == -1
                    and kind in ("open_clientfd", "write_sock")
                ):
                    ret = default_fn()
            else:
                ret = default_fn()
        else:
            err = error_msg or f"Unexpected call to {kind}"
            ret = self._replay_or_fail(kind, req_info, err)

        self.recorder.record_call(record_name, req_info, ret, scope)
        return ret

    def _check_system_time(self) -> int:
        return self._dispatch(
            "system_time",
            self.local_system_time_expectations,
            self.session_system_time_expectations,
            lambda _: True,
            {},
            get_real_system_time,
            default_system_time,
            "system_time",
            "Unexpected call to system_time. If this call is expected, please ensure you have set an expectation using expect_system_time.",
        )

    def _check_hash(self, hash_type: str, data: bytes) -> bytes:
        req_info = {"hash_type": hash_type, "data": data}
        return self._dispatch(
            "hash",
            self.local_hash_expectations,
            self.session_hash_expectations,
            lambda e: e.hash_type == hash_type and e.data == data,
            req_info,
            lambda: get_real_hash(hash_type, data),
            lambda: default_hash(hash_type, data),
            "hash",
            f"Unexpected call to hash with type: {hash_type}, data: {data}. If this call is expected, please ensure you have set an expectation using expect_hash.",
        )

    def _check_open_clientfd(self, path: str) -> int:
        return self._dispatch(
            "open_clientfd",
            self.local_open_clientfd_expectations,
            self.session_open_clientfd_expectations,
            lambda e: e.path == path,
            path,
            lambda: self.socket_manager.open_clientfd(path)
            if self.socket_manager
            else -1,
            lambda: default_open_clientfd(path),
            "open_clientfd",
            f"Unexpected call to open_clientfd with path: {path}. If this call is expected, please ensure you have set an expectation using expect_open_clientfd.",
        )

    def _check_write_sock(self, sock_id: int, buf: bytes) -> int:
        req_info = {"sock_id": sock_id, "buf": buf}
        return self._dispatch(
            "write_sock",
            self.local_write_sock_expectations,
            self.session_write_sock_expectations,
            lambda e: e.sock_id == sock_id,
            req_info,
            lambda: self.socket_manager.write_sock(sock_id, buf)
            if self.socket_manager
            else -1,
            lambda: default_write_sock(sock_id, buf),
            "write_sock",
            f"Unexpected call to write_sock with sock_id: {sock_id}. If this call is expected, please ensure you have set an expectation using expect_write_sock.",
        )

    def _check_read_sock(self, sock_id: int, read_len: int) -> bytes:
        req_info = {"sock_id": sock_id, "read_len": read_len}
        return self._dispatch(
            "read_sock",
            self.local_read_sock_expectations,
            self.session_read_sock_expectations,
            lambda e: e.sock_id == sock_id,
            req_info,
            lambda: self.socket_manager.read_sock(sock_id, read_len)
            if self.socket_manager
            else b"",
            lambda: default_read_sock(sock_id, read_len),
            "read_sock",
            f"Unexpected call to read_sock with sock_id: {sock_id}. If this call is expected, please ensure you have set an expectation using expect_read_sock.",
        )

    def _check_batch_http_request(self, data: bytes) -> bytes:
        req = BatchHttpRequest.FromString(data)
        resp = self._dispatch(
            "batch_http_request",
            self.local_batch_http_request_expectations,
            self.session_batch_http_request_expectations,
            lambda e: partial_match(e.requests, req)[0],
            req,
            lambda: execute_real_batch_http_request(req),
            lambda: default_batch_http_response(req),
            "batch_http_request",
            f"Unexpected batch_http_request: {req}. If this request is expected, please ensure you have set an expectation using expect_batch_http_request.",
        )
        return resp.SerializeToString()

    def handle_main_command(self, data: bytes) -> bytes:
        command = MainCommand.FromString(data)
        resp = self._dispatch(
            "send_main_command",
            self.local_expectations,
            self.session_expectations,
            lambda e: partial_match(e.command, command)[0],
            command,
            None,
            lambda: default_main_command_response(command),
            "send_main_command",
            f"Unexpected command: {command}. If this command is expected, please ensure you have set an expectation using expect_command.",
        )
        return resp.SerializeToString()

    def get_mapped_paths(self) -> dict[str, str]:
        if self.moounit is not None:
            if hasattr(self.moounit, "get_mapped_paths"):
                return self.moounit.get_mapped_paths()
            return getattr(self.moounit, "_mapped_paths", {})
        return {}
