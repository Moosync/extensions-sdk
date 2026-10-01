import difflib
import json
import re
from typing import Any
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message

from moounit.models import ReplayIgnoreRule

COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_CYAN = "\033[36m"
COLOR_BOLD = "\033[1m"


class ReplayIgnoreBuilder:
    def __init__(self, rule: ReplayIgnoreRule, registry: list[ReplayIgnoreRule]):
        self._rule = rule
        self._registry = registry
        self._registry.append(rule)

    def times(self, n: int) -> "ReplayIgnoreBuilder":
        self._rule.remaining_times = n
        return self


class IgnoreRule:
    def __init__(self, path: str, regex: str | None = None):
        self.path = path.strip()
        self.regex = regex
        self._compiled_regex = re.compile(regex) if regex else None

    def matches_path(self, field_path: str) -> bool:
        # Strip array indexing e.g. requests[0].body -> requests.body
        normalized_path = re.sub(r"\[\d+\]", "", field_path)
        p = self.path.lower()
        fp = field_path.lower()
        np = normalized_path.lower()

        if fp == p or np == p:
            return True
        if fp.startswith(p + ".") or np.startswith(p + "."):
            return True
        if fp.endswith("." + p) or np.endswith("." + p):
            return True
        if f".{p}." in f".{fp}." or f".{p}." in f".{np}.":
            return True
        if p == fp.split(".")[-1] or p == np.split(".")[-1]:
            return True
        if p.split(".")[-1] == np.split(".")[-1]:
            return True
        return False

    def apply_regex(self, value: Any) -> Any:
        if self._compiled_regex is None:
            return value

        if isinstance(value, str):
            return self._compiled_regex.sub("", value)
        if isinstance(value, bytes):
            try:
                decoded = value.decode("utf-8")
                stripped = self._compiled_regex.sub("", decoded)
                return stripped.encode("utf-8")
            except UnicodeDecodeError:
                pattern_bytes = self.regex.encode("utf-8")
                return re.sub(pattern_bytes, b"", value)
        return value


def parse_ignore_rules(ignored_fields: list[Any] | None) -> list[IgnoreRule]:
    if not ignored_fields:
        return []

    rules: list[IgnoreRule] = []
    for item in ignored_fields:
        if isinstance(item, IgnoreRule):
            rules.append(item)
        elif isinstance(item, dict):
            path = item.get("path") or ""
            regex = item.get("regex")
            rules.append(IgnoreRule(path=path, regex=regex))
        elif isinstance(item, str):
            m = re.match(r"^(.*?)(?:\[(?:regex:)?(.*?)\]|:re:(.*))$", item)
            if m:
                path = m.group(1).strip()
                regex = (m.group(2) if m.group(2) is not None else m.group(3)).strip()
                rules.append(IgnoreRule(path=path, regex=regex))
            else:
                rules.append(IgnoreRule(path=item, regex=None))
    return rules


def get_applicable_rules(field_path: str, rules: list[IgnoreRule]) -> list[IgnoreRule]:
    return [rule for rule in rules if rule.matches_path(field_path)]


def should_ignore(field_path: str, ignored_fields: list[Any] | None) -> bool:
    rules = parse_ignore_rules(ignored_fields)
    matching = get_applicable_rules(field_path, rules)
    return any(rule.regex is None for rule in matching)


def apply_value_regexes(field_path: str, val: Any, rules: list[IgnoreRule]) -> Any:
    current = val
    for rule in rules:
        if rule.matches_path(field_path) and rule.regex is not None:
            current = rule.apply_regex(current)
    return current


def format_colored_diff(
    expected_val: Any, actual_val: Any, label: str = "Mismatch"
) -> str:
    """
    Renders a unified diff between expected and actual values with ANSI terminal colors.
    """

    def _to_lines(val: Any) -> list[str]:
        if isinstance(val, Message):
            d = MessageToDict(val, preserving_proto_field_name=True)
            s = json.dumps(d, indent=2)
        elif isinstance(val, (dict, list)):
            s = json.dumps(val, indent=2, default=str)
        elif isinstance(val, bytes):
            try:
                s = val.decode("utf-8")
            except Exception:
                s = repr(val)
        else:
            s = str(val)
        return s.splitlines(keepends=True)

    exp_lines = _to_lines(expected_val)
    act_lines = _to_lines(actual_val)

    exp_lines = [line if line.endswith("\n") else line + "\n" for line in exp_lines]
    act_lines = [line if line.endswith("\n") else line + "\n" for line in act_lines]

    diff = list(
        difflib.unified_diff(
            exp_lines,
            act_lines,
            fromfile="expected",
            tofile="actual",
            lineterm="\n",
        )
    )

    if not diff:
        return f"{COLOR_BOLD}expected:{COLOR_RESET}\n{expected_val!r}\n{COLOR_BOLD}actual:{COLOR_RESET}\n{actual_val!r}"

    colored_lines = []
    for line in diff:
        line_clean = line.rstrip("\n")
        if line.startswith("---") or line.startswith("+++"):
            colored_lines.append(f"{COLOR_BOLD}{line_clean}{COLOR_RESET}")
        elif line.startswith("@@"):
            colored_lines.append(f"{COLOR_CYAN}{line_clean}{COLOR_RESET}")
        elif line.startswith("-"):
            colored_lines.append(f"{COLOR_RED}{line_clean}{COLOR_RESET}")
        elif line.startswith("+"):
            colored_lines.append(f"{COLOR_GREEN}{line_clean}{COLOR_RESET}")
        else:
            colored_lines.append(line_clean)

    diff_str = "\n".join(colored_lines)
    return f"{COLOR_BOLD}{label} (unified diff):{COLOR_RESET}\n{diff_str}"


def partial_match(
    expected: Message,
    actual: Message,
    ignored_fields: list[Any] | None = None,
    path_prefix: str = "",
    root_call: str = "",
) -> tuple[bool, str | None]:
    """
    Compares expected and actual protobuf messages.
    Ignores fields matching dot-notation patterns in ignored_fields.
    Supports value-level regexes to strip dynamic content before comparison.
    Returns (True, None) if matched, or (False, error_message) if mismatched.
    """
    if expected.DESCRIPTOR != actual.DESCRIPTOR:
        msg = (
            f"Message type mismatch at '{path_prefix}': expected "
            f"{expected.DESCRIPTOR.name}, got {actual.DESCRIPTOR.name}."
        )
        return False, msg

    rules = parse_ignore_rules(ignored_fields)

    for field in expected.DESCRIPTOR.fields:
        field_path = f"{path_prefix}.{field.name}" if path_prefix else field.name

        matching_rules = get_applicable_rules(field_path, rules)
        if any(r.regex is None for r in matching_rules):
            continue

        expected_val = getattr(expected, field.name)
        actual_val = getattr(actual, field.name)

        if (
            isinstance(expected_val, (list, tuple))
            or "Repeated" in type(expected_val).__name__
        ):
            if len(expected_val) != len(actual_val):
                err = (
                    f"Length mismatch at '{field_path}': expected {len(expected_val)} elements, "
                    f"got {len(actual_val)} elements."
                )
                tip = _format_ignore_tip(root_call, field_path)
                return False, f"{err}\n{tip}"

            for idx, (exp_item, act_item) in enumerate(zip(expected_val, actual_val)):
                elem_path = f"{field_path}[{idx}]"
                if isinstance(exp_item, Message) and isinstance(act_item, Message):
                    matched, err = partial_match(
                        exp_item, act_item, rules, elem_path, root_call
                    )
                    if not matched:
                        return False, err
                else:
                    exp_norm = apply_value_regexes(elem_path, exp_item, rules)
                    act_norm = apply_value_regexes(elem_path, act_item, rules)
                    if exp_norm != act_norm:
                        diff = format_colored_diff(
                            exp_item, act_item, label=f"Field mismatch at '{elem_path}'"
                        )
                        tip = _format_ignore_tip(root_call, field_path)
                        return False, f"{diff}\n{tip}"
        elif (
            hasattr(field, "message_type")
            and field.message_type
            and field.message_type.GetOptions().map_entry
        ):
            all_keys = set(expected_val.keys()) | set(actual_val.keys())
            for key in sorted(all_keys):
                entry_path = f"{field_path}.{key}"
                entry_matching = get_applicable_rules(entry_path, rules)
                if any(r.regex is None for r in entry_matching):
                    continue
                exp_entry = expected_val.get(key)
                act_entry = actual_val.get(key)

                exp_norm = apply_value_regexes(entry_path, exp_entry, rules)
                act_norm = apply_value_regexes(entry_path, act_entry, rules)
                if exp_norm != act_norm:
                    diff = format_colored_diff(
                        exp_entry, act_entry, label=f"Field mismatch at '{entry_path}'"
                    )
                    tip = _format_ignore_tip(root_call, entry_path)
                    return False, f"{diff}\n{tip}"
        else:
            is_set = False
            try:
                is_set = expected.HasField(field.name)
            except ValueError:
                is_set = field in {f for f, _ in expected.ListFields()}

            if not is_set:
                continue

            if isinstance(expected_val, Message) and isinstance(actual_val, Message):
                matched, err = partial_match(
                    expected_val, actual_val, rules, field_path, root_call
                )
                if not matched:
                    return False, err
            else:
                exp_norm = apply_value_regexes(field_path, expected_val, rules)
                act_norm = apply_value_regexes(field_path, actual_val, rules)
                if exp_norm != act_norm:
                    diff = format_colored_diff(
                        expected_val,
                        actual_val,
                        label=f"Field mismatch at '{field_path}'",
                    )
                    tip = _format_ignore_tip(root_call, field_path)
                    return False, f"{diff}\n{tip}"

    return True, None


def _format_ignore_tip(root_call: str, field_path: str) -> str:
    return (
        f"Tip: If '{field_path}' contains dynamic data (e.g. timestamp, random token), "
        f"you can ignore it in your test using replay_ignore:\n"
        f"    moounit.replay_ignore(\n"
        f"        request=BatchHttpRequest(...),\n"
        f'        ignore_fields=["{field_path}"],\n'
        f"    )"
    )
