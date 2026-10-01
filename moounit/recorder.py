import base64
import json
import os
from typing import Any
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import Message
from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    HttpRequest,
    MainCommand,
    MainCommandResponse,
)
from moounit.matcher import (
    IgnoreRule,
    ReplayIgnoreBuilder,
    format_colored_diff,
    partial_match,
)
from moounit.models import ReplayIgnoreRule, Scope


def bytes_to_b64(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")


def b64_to_bytes(s: str) -> bytes:
    return base64.b64decode(s.encode("utf-8"))


def _matches_filter(filter_val: Any, target_val: Any) -> bool:
    if filter_val is None:
        return True

    if isinstance(filter_val, Message) and isinstance(target_val, Message):
        # Special case: BatchHttpRequest vs BatchHttpRequest
        if isinstance(filter_val, BatchHttpRequest) and isinstance(
            target_val, BatchHttpRequest
        ):
            if not filter_val.requests:
                return True
            for req_filter in filter_val.requests:
                if not any(
                    _matches_filter(req_filter, req_target)
                    for req_target in target_val.requests
                ):
                    return False
            return True

        # Special case: HttpRequest filter against BatchHttpRequest target
        if filter_val.DESCRIPTOR.name == "HttpRequest" and isinstance(
            target_val, BatchHttpRequest
        ):
            return any(
                _matches_filter(filter_val, req_target)
                for req_target in target_val.requests
            )

        # Special case: MainCommand vs MainCommand
        if isinstance(filter_val, MainCommand) and isinstance(target_val, MainCommand):
            cmd_filter = filter_val.WhichOneof("command")
            if not cmd_filter:
                return True
            cmd_target = target_val.WhichOneof("command")
            if cmd_filter != cmd_target:
                return False
            return _matches_filter(
                getattr(filter_val, cmd_filter), getattr(target_val, cmd_target)
            )

        # Special case: Inner command (e.g. GetSongRequest) against MainCommand target
        if isinstance(target_val, MainCommand) and not isinstance(
            filter_val, MainCommand
        ):
            cmd_target = target_val.WhichOneof("command")
            if cmd_target:
                inner = getattr(target_val, cmd_target)
                if inner.DESCRIPTOR == filter_val.DESCRIPTOR:
                    return _matches_filter(filter_val, inner)
            return False

        if filter_val.DESCRIPTOR != target_val.DESCRIPTOR:
            return False

        for field, f_val in filter_val.ListFields():
            if not hasattr(target_val, field.name):
                return False
            t_val = getattr(target_val, field.name)
            if not _matches_filter(f_val, t_val):
                return False
        return True

    if isinstance(filter_val, (list, tuple)) and isinstance(target_val, (list, tuple)):
        if not filter_val:
            return True
        for f_item in filter_val:
            if not any(_matches_filter(f_item, t_item) for t_item in target_val):
                return False
        return True

    if isinstance(filter_val, dict) and isinstance(target_val, dict):
        for k, v in filter_val.items():
            if k not in target_val or not _matches_filter(v, target_val[k]):
                return False
        return True

    if isinstance(filter_val, str) and isinstance(target_val, str):
        return filter_val == target_val or filter_val in target_val

    if isinstance(filter_val, bytes) and isinstance(target_val, bytes):
        return filter_val == target_val or filter_val in target_val

    return filter_val == target_val


class Recorder:
    def __init__(
        self,
        record_mode: bool = False,
        expectations_file: str | None = None,
        filter: str | None = None,
    ):
        self.record_mode = record_mode
        self.expectations_file = expectations_file
        self.filter = filter

        # Recorded expectations structure:
        # {
        #   "session": [ ... ],
        #   "tests": {
        #       "test_foo": [ ... ],
        #       "test_bar": [ ... ]
        #   }
        # }
        self.recorded_session_calls: list[dict[str, Any]] = []
        self.recorded_test_calls: dict[str, list[dict[str, Any]]] = {}

        # Replay expectations structure:
        self.replay_session_calls: list[dict[str, Any]] = []
        self.replay_test_calls: dict[str, list[dict[str, Any]]] = {}

        self.current_test_name: str | None = None

        # Per-test and per-session replay ignore rules
        self.session_replay_ignore_rules: list[ReplayIgnoreRule] = []
        self.local_replay_ignore_rules: list[ReplayIgnoreRule] = []

        if (
            not self.record_mode
            and self.expectations_file
            and os.path.exists(self.expectations_file)
        ):
            self._load_expectations()

    def replay_ignore(
        self,
        request: Any,
        ignore_fields: list[str] | str | None = None,
        ignore_field: list[str] | str | None = None,
        regex: str | None = None,
        test_name: str | None = None,
    ) -> ReplayIgnoreBuilder:
        fields = []
        if ignore_fields:
            if isinstance(ignore_fields, str):
                fields.append(ignore_fields)
            else:
                fields.extend(ignore_fields)
        if ignore_field:
            if isinstance(ignore_field, str):
                fields.append(ignore_field)
            else:
                fields.extend(ignore_field)

        rule = ReplayIgnoreRule(
            request_filter=request,
            ignore_fields=fields,
            regex=regex,
            remaining_times=-1,
            test_name=test_name or self.current_test_name,
        )
        registry = self.local_replay_ignore_rules
        return ReplayIgnoreBuilder(rule, registry)

    def session_replay_ignore(
        self,
        request: Any,
        ignore_fields: list[str] | str | None = None,
        ignore_field: list[str] | str | None = None,
        regex: str | None = None,
        test_name: str | None = None,
    ) -> ReplayIgnoreBuilder:
        fields = []
        if ignore_fields:
            if isinstance(ignore_fields, str):
                fields.append(ignore_fields)
            else:
                fields.extend(ignore_fields)
        if ignore_field:
            if isinstance(ignore_field, str):
                fields.append(ignore_field)
            else:
                fields.extend(ignore_field)

        rule = ReplayIgnoreRule(
            request_filter=request,
            ignore_fields=fields,
            regex=regex,
            remaining_times=-1,
            test_name=test_name,
        )
        return ReplayIgnoreBuilder(rule, self.session_replay_ignore_rules)

    def clear_local_replay_ignore_rules(self):
        self.local_replay_ignore_rules.clear()

    def clear_session_replay_ignore_rules(self):
        self.session_replay_ignore_rules.clear()

    def set_current_test(self, test_name: str | None):
        self.current_test_name = test_name
        if test_name and test_name not in self.recorded_test_calls:
            if not self.filter or self.filter in test_name:
                self.recorded_test_calls[test_name] = []

    def clear_current_test(self):
        self.current_test_name = None

    def has_replay_expectations(self, scope: Scope) -> bool:
        if scope == Scope.LOCAL:
            if (
                self.current_test_name
                and self.current_test_name in self.replay_test_calls
            ):
                return len(self.replay_test_calls[self.current_test_name]) > 0
            return False
        return len(self.replay_session_calls) > 0

    def _load_expectations(self):
        try:
            with open(self.expectations_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.replay_session_calls = []
                    self.replay_test_calls = data.get("tests", {})
                elif isinstance(data, list):
                    # Fallback / backward compatibility if simple list
                    self.replay_session_calls = data
                    self.replay_test_calls = {}
        except Exception as e:
            print(
                f"Warning: Failed to load expectations from {self.expectations_file}: {e}"
            )

    def save_recorded_expectations(self):
        if not self.record_mode or not self.expectations_file:
            return

        target_file = self.expectations_file
        workspace_dir = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
        if workspace_dir and not os.path.isabs(target_file):
            target_file = os.path.join(workspace_dir, target_file)

        target_dir = os.path.dirname(target_file)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        # Duplicate recorded session calls into each test's recorded calls
        tests_data = {}
        for test_name, calls in self.recorded_test_calls.items():
            tests_data[test_name] = list(self.recorded_session_calls) + calls

        payload = {
            "tests": tests_data,
        }

        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")

    def record_call(
        self, call_type: str, request_data: Any, response_data: Any, scope: Scope
    ):
        if not self.record_mode:
            return

        entry = {
            "type": call_type,
            "request": self._serialize(request_data),
            "response": self._serialize(response_data),
        }

        if scope == Scope.LOCAL and self.current_test_name:
            if self.filter and self.filter not in self.current_test_name:
                return
            if self.current_test_name not in self.recorded_test_calls:
                self.recorded_test_calls[self.current_test_name] = []
            self.recorded_test_calls[self.current_test_name].append(entry)
        else:
            self.recorded_session_calls.append(entry)

    def _serialize(self, obj: Any) -> Any:
        if isinstance(
            obj, (MainCommand, MainCommandResponse, BatchHttpRequest, BatchHttpResponse)
        ):
            return MessageToDict(obj, preserving_proto_field_name=True)
        if isinstance(obj, bytes):
            return {"__bytes__": bytes_to_b64(obj)}
        if isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serialize(v) for v in obj]
        return str(obj)

    def _deserialize_bytes(self, obj: Any) -> bytes:
        if isinstance(obj, dict) and "__bytes__" in obj:
            return b64_to_bytes(obj["__bytes__"])
        if isinstance(obj, str):
            return obj.encode("utf-8")
        return b""

    def _collect_ignore_rules_for_request(
        self,
        call_type: str,
        request_obj: Any,
    ) -> tuple[list[IgnoreRule], list[ReplayIgnoreRule]]:
        all_rules = self.session_replay_ignore_rules + self.local_replay_ignore_rules
        ignore_rules: list[IgnoreRule] = []
        matched_rules: list[ReplayIgnoreRule] = []

        for rule in all_rules:
            if rule.remaining_times == 0:
                continue

            if rule.test_name is not None and self.current_test_name is not None:
                if rule.test_name != self.current_test_name:
                    continue

            if not _matches_filter(rule.request_filter, request_obj):
                continue

            matched_rules.append(rule)
            for field_path in rule.ignore_fields:
                ignore_rules.append(IgnoreRule(path=field_path, regex=rule.regex))

        return ignore_rules, matched_rules

    def match_and_consume_replay(
        self,
        call_type: str,
        request_obj: Any,
        scope: Scope,
    ) -> tuple[Any | None, str | None]:
        """
        Finds the first replay entry matching call_type and request_obj in the specified scope.
        Returns (deserialized_response, None) or (None, failure_reason).
        """
        calls_list = None
        if scope == Scope.LOCAL:
            if (
                self.current_test_name
                and self.current_test_name in self.replay_test_calls
            ):
                calls_list = self.replay_test_calls[self.current_test_name]
        else:
            calls_list = self.replay_session_calls

        if not calls_list:
            scope_name = (
                f"test '{self.current_test_name}'"
                if scope == Scope.LOCAL
                else "session"
            )
            return (
                None,
                f"No recorded expectations found for {call_type} in {scope_name}.",
            )

        ignore_rules, matched_rules = self._collect_ignore_rules_for_request(
            call_type, request_obj
        )

        entry = calls_list[0]
        recorded_type = entry.get("type")

        if recorded_type != call_type:
            return None, (
                f"Call type mismatch: expected next call to be '{recorded_type}', "
                f"got '{call_type}'."
            )

        saved_req = entry.get("request")
        matched = False
        err = None

        if call_type == "send_main_command":
            expected_cmd = MainCommand()
            ParseDict(saved_req, expected_cmd)
            matched, err = partial_match(
                expected_cmd,
                request_obj,
                ignored_fields=ignore_rules,
                root_call=call_type,
            )
        elif call_type == "batch_http_request":
            expected_req = BatchHttpRequest()
            ParseDict(saved_req, expected_req)
            matched, err = partial_match(
                expected_req,
                request_obj,
                ignored_fields=ignore_rules,
                root_call=call_type,
            )
        elif call_type == "system_time":
            matched = True
        elif call_type == "open_clientfd":
            matched = saved_req == request_obj
            if not matched:
                err = format_colored_diff(
                    saved_req, request_obj, label="Mismatched open_clientfd path"
                )
        elif call_type == "write_sock":
            matched = saved_req.get("sock_id") == request_obj.get("sock_id")
            if not matched:
                err = format_colored_diff(
                    saved_req, request_obj, label="Mismatched write_sock request"
                )
        elif call_type == "read_sock":
            matched = saved_req.get("sock_id") == request_obj.get("sock_id")
            if not matched:
                err = format_colored_diff(
                    saved_req, request_obj, label="Mismatched read_sock request"
                )
        elif call_type == "hash":
            matched = saved_req.get("hash_type") == request_obj.get("hash_type")
            if not matched:
                err = format_colored_diff(
                    saved_req, request_obj, label="Mismatched hash request"
                )

        if matched:
            calls_list.pop(0)
            for rule in matched_rules:
                if rule.remaining_times > 0:
                    rule.remaining_times -= 1
            resp_payload = entry.get("response")
            return self._deserialize_response(call_type, resp_payload), None

        return (
            None,
            err or f"Recorded call ({call_type}) did not match incoming request.",
        )

    def _deserialize_response(self, call_type: str, resp_payload: Any) -> Any:
        if call_type == "send_main_command":
            resp = MainCommandResponse()
            ParseDict(resp_payload, resp)
            return resp
        if call_type == "batch_http_request":
            resp = BatchHttpResponse()
            ParseDict(resp_payload, resp)
            return resp
        if call_type in ("read_sock", "hash"):
            return self._deserialize_bytes(resp_payload)
        if call_type in ("system_time", "open_clientfd", "write_sock"):
            return int(resp_payload)
        return resp_payload
