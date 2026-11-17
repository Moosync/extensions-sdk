# pylint: disable=duplicate-code
import contextvars
import json
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

import extism
from google.protobuf.message import Message

from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    Error,
    ExtensionAccountDetail,
    HttpRequest,
    HttpResult,
    MainCommand,
    MainCommandResponse,
)

if TYPE_CHECKING:
    from moounit.core import Moounit

T = TypeVar("T")
E = TypeVar("E", bound=object)
from moounit.defaults import default_main_command_response
from moounit.generated import GeneratedMoounitExpectationClient
from moounit.matcher import ReplayIgnoreBuilder, partial_match
from moounit.models import (
    Expectation,
    Scope,
)
from moounit.passthrough import (
    RealSocketManager,
    execute_real_batch_http_request,
    get_real_system_time,
)
from moounit.recorder import Recorder
from moounit.sanitize import sanitize_main_command

current_scope = contextvars.ContextVar("current_scope", default=Scope.SESSION)


class ExpectationManager(GeneratedMoounitExpectationClient):
    def __init__(
        self,
        recorder: Recorder | None = None,
        moounit: "Moounit | None" = None,
    ):
        self.recorder = recorder or Recorder()
        self.moounit = moounit
        self._socket_manager: RealSocketManager | None = None
        self.accounts: dict[str, ExtensionAccountDetail] = {}
        self._last_http_result: HttpResult | None = None
        self.local_expectations: list[Expectation] = []
        self.session_expectations: list[Expectation] = []

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

    @property
    def package_name(self) -> str:
        if self.moounit is not None:
            return getattr(self.moounit, "package_name", "")
        return ""

    def expect_command(
        self,
        command: MainCommand,
        response: MainCommandResponse | Callable[[], MainCommandResponse],
        times: int = 1,
    ):
        pkg_name = getattr(self.moounit, "package_name", "") if self.moounit else ""
        sanitize_main_command(command, pkg_name)
        target = (
            self.local_expectations
            if current_scope.get() == Scope.LOCAL
            else self.session_expectations
        )
        target.append(Expectation(command=command, response=response, times=times))

    def replay_ignore(
        self,
        request: Message,
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
        self.accounts.clear()
        self._last_http_result = None
        self.local_expectations.clear()

    def verify_and_clear_local_expectations(self):
        if self.recorder.record_mode:
            self.clear_local_expectations()
            return

        unused = [e for e in self.local_expectations if e.times > 0]
        self.clear_local_expectations()
        if unused:
            raise AssertionError(f"Unused command expectations: {unused}")

    def clear_session_expectations(self):
        self._last_http_result = None
        self.session_expectations.clear()

    def verify_and_clear_session_expectations(self):
        if self.recorder.record_mode:
            self.clear_session_expectations()
            return

        unused = [e for e in self.session_expectations if e.times > 0]
        self.clear_session_expectations()
        if unused:
            raise AssertionError(f"Unused session command expectations: {unused}")

    def _get_value(self, val: T | Callable[[], T]) -> T:
        if callable(val):
            return val()
        return val

    def _consume_expectation(
        self,
        local_list: list[E],
        session_list: list[E],
        matcher: Callable[[E], bool],
    ) -> E | None:
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
        self, call_type: str, request_obj: Message, default_error_msg: str
    ) -> object:
        scope = current_scope.get()
        if self.recorder.has_replay_expectations(scope):
            resp, err = self.recorder.match_and_consume_replay(
                call_type, request_obj, scope, package_name=self.package_name
            )
            if resp is not None:
                return resp
            if err and not self.recorder.has_replay_expectations(Scope.SESSION):
                raise AssertionError(err)

        if scope == Scope.LOCAL and self.recorder.has_replay_expectations(
            Scope.SESSION
        ):
            resp, err = self.recorder.match_and_consume_replay(
                call_type, request_obj, Scope.SESSION, package_name=self.package_name
            )
            if resp is not None:
                return resp
            if err:
                raise AssertionError(err)

        raise AssertionError(default_error_msg)

    def _dispatch(
        self,
        kind: str,
        local_list: list[E],
        session_list: list[E],
        matcher: Callable[[E], bool],
        req_info: Message,
        passthrough_fn: Callable[[], T] | None,
        default_fn: Callable[[], T],
        record_name: str,
        error_msg: str | None = None,
    ) -> T:
        scope = current_scope.get()
        exp = self._consume_expectation(local_list, session_list, matcher)
        if exp is not None:
            ret = self._get_value(getattr(exp, "response", None))
            if not self.recorder.record_mode and self.recorder.has_replay_expectations(
                scope
            ):
                self.recorder.match_and_consume_replay(
                    kind, req_info, scope, package_name=self.package_name
                )
        elif self.recorder.record_mode:
            if self.passthrough_enabled and passthrough_fn is not None:
                try:
                    ret = passthrough_fn()
                except Exception:
                    ret = default_fn()
                if ret is None:
                    ret = default_fn()
            else:
                ret = default_fn()
        else:
            err = error_msg or f"Unexpected call to {kind}"
            ret = self._replay_or_fail(kind, req_info, err)

        self.recorder.record_call(record_name, req_info, ret, scope)
        return ret

    def _check_http_request(
        self, plugin: extism.CurrentPlugin, req_offs: int, body_offs: int
    ) -> int:
        req_mem = plugin.memory_at_offset(req_offs)
        req_json = bytes(plugin.memory(req_mem)).decode("utf-8")
        req_dict = json.loads(req_json)
        headers = {str(k): str(v) for k, v in req_dict.get("headers", {}).items()}
        if body_offs != 0:
            body_mem = plugin.memory_at_offset(body_offs)
            body = bytes(plugin.memory(body_mem))
        else:
            body = b""

        http_req = HttpRequest(
            url=req_dict.get("url", ""),
            method=req_dict.get("method", "GET").upper(),
            headers=headers,
            body=body,
        )
        batch_req = BatchHttpRequest(requests=[http_req])
        cmd = MainCommand(batch_http_request=batch_req)
        res_bytes = self.handle_main_command(cmd.SerializeToString())
        res = MainCommandResponse.FromString(res_bytes)
        batch_resp = res.batch_http_request
        result = batch_resp.responses[0] if batch_resp.responses else HttpResult()
        self._last_http_result = result

        if result.HasField("error"):
            err_bytes = result.error.encode("utf-8")
            mem = plugin.alloc(len(err_bytes))
            plugin.memory(mem)[:] = err_bytes
            return mem.offset

        resp_bytes = result.response.body if result.response.body else b""
        mem = plugin.alloc(len(resp_bytes))
        plugin.memory(mem)[:] = resp_bytes
        return mem.offset

    def _check_http_status_code(self) -> int:
        if self._last_http_result is None or self._last_http_result.HasField("error"):
            return 500
        return self._last_http_result.response.status_code

    def _check_http_headers(self, plugin: extism.CurrentPlugin) -> int:
        if self._last_http_result is None or self._last_http_result.HasField("error"):
            headers_dict = {}
        else:
            headers_dict = dict(self._last_http_result.response.headers)
        headers_json = json.dumps(headers_dict).encode("utf-8")
        mem = plugin.alloc(len(headers_json))
        plugin.memory(mem)[:] = headers_json
        return mem.offset

    def _get_main_command_passthrough(
        self, command: MainCommand, which: str | None
    ) -> Callable[[], MainCommandResponse] | None:
        if not which:
            return None
        if which == "system_time":
            return lambda: MainCommandResponse(
                system_time=get_real_system_time(command.system_time)
            )
        if which == "batch_http_request":
            return lambda: MainCommandResponse(
                batch_http_request=execute_real_batch_http_request(
                    command.batch_http_request
                )
            )
        if not self.moounit:
            return None
        for mgr_attr in ("ws_manager", "process_manager", "socket_manager"):
            mgr = getattr(self.moounit, mgr_attr, None)
            handler = getattr(mgr, which, None) if mgr else None
            if handler:
                def _invoke(h=handler, w=which, c=command):
                    try:
                        return MainCommandResponse(**{w: h(getattr(c, w))})
                    except Exception as e:
                        return MainCommandResponse(error=Error(message=str(e)))

                return _invoke
        return None

    def handle_main_command(self, data: bytes) -> bytes:
        command = MainCommand.FromString(data)
        pkg_name = getattr(self.moounit, "package_name", "") if self.moounit else ""
        try:
            sanitize_main_command(command, pkg_name)
        except Exception as e:
            return MainCommandResponse(error=Error(message=str(e))).SerializeToString()

        ignore_rules, _ = self.recorder._collect_ignore_rules_for_request(
            "send_main_command", command
        )

        which = command.WhichOneof("command")
        if which == "set_account":
            self.accounts[command.set_account.account.id] = command.set_account.account

        passthrough_fn = self._get_main_command_passthrough(command, which)

        resp = self._dispatch(
            "send_main_command",
            self.local_expectations,
            self.session_expectations,
            lambda e: partial_match(
                e.command,
                command,
                ignored_fields=ignore_rules,
                root_call="send_main_command",
            )[0],
            command,
            passthrough_fn,
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
