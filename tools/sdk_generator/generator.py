#!/usr/bin/env python3
# Moosync
# Copyright (C) 2024, 2025, 2026 Moosync <support@moosync.app>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import os
import re
from typing import Any, Dict, List, Optional

from google.protobuf import (
    any_pb2,
    descriptor_pb2,
    descriptor_pool,
    duration_pb2,
    empty_pb2,
    struct_pb2,
)
from google.protobuf.internal import decoder
import jinja2


TAG_IS_EVENT_NOTIFICATION = 60001
TAG_HAS_WRAPPER = 60004
TAG_SDK_MANAGER = 60005


def to_snake_case(name: str) -> str:
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def to_camel_case(name: str) -> str:
    snake = to_snake_case(name)
    components = snake.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_pascal_case(name: str) -> str:
    return "".join(x.title() for x in to_snake_case(name).split("_"))


def format_doc(doc: str, style: str = "jsdoc", indent: int = 0, name: str = "") -> str:
    if not doc:
        return ""
    ind = " " * indent
    if style == "jsdoc":
        lines = [f"{ind}/**"]
        for line in doc.split("\n"):
            lines.append(f"{ind} * {line}".rstrip())
        lines.append(f"{ind} */")
        return "\n".join(lines)
    elif style == "rustdoc":
        lines = [f"{ind}/// {line}".rstrip() for line in doc.split("\n")]
        return "\n".join(lines)
    elif style == "godoc":
        prefix = f"{name} " if name else ""
        lines = [f"{ind}// {prefix}{line}".rstrip() for line in doc.split("\n")]
        return "\n".join(lines)
    elif style == "pydoc":
        if "\n" not in doc:
            return f'{ind}"""{doc}"""'
        lines = [f'{ind}"""', f"{ind}{doc}", f'{ind}"""']
        return "\n".join(lines)
    return doc


def find_proto_file() -> Optional[str]:
    candidates = [
        "protos/extension_service.proto",
        "core/types/protos/extension_service.proto",
    ]
    workspace_dir = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    if workspace_dir:
        for c in candidates:
            p = os.path.join(workspace_dir, c)
            if os.path.exists(p):
                return p
    for c in candidates:
        if os.path.exists(c):
            return c
    runfiles_dir = os.environ.get("TEST_SRCDIR", ".")
    for root, _, files in os.walk(runfiles_dir):
        if "extension_service.proto" in files:
            return os.path.join(root, "extension_service.proto")
    return None


def parse_proto_docs(proto_path: Optional[str]) -> Dict[str, str]:
    docs = {}
    if not proto_path or not os.path.exists(proto_path):
        return docs
    with open(proto_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"((?:[ \t]*(?://|/\*|\*).*?\n)+)[ \t]*rpc[ \t]+([A-Za-z0-9_]+)"
    )
    for match in pattern.finditer(content):
        raw_comment, rpc_name = match.groups()
        lines = []
        for line in raw_comment.splitlines():
            line = line.strip()
            if line.startswith("//"):
                line = line[2:].strip()
            elif line.startswith("/*"):
                line = line[2:].strip()
            elif line.startswith("*"):
                line = line[1:].strip()
            if line.endswith("*/"):
                line = line[:-2].strip()
            if line:
                lines.append(line)
        if lines:
            docs[rpc_name] = " ".join(lines)
    return docs


def decode_method_options(options_bytes: bytes) -> Dict[int, Any]:
    opts = {}
    pos = 0
    while pos < len(options_bytes):
        tag, pos = decoder._DecodeVarint(options_bytes, pos)
        field_num = tag >> 3
        wire_type = tag & 7
        if wire_type == 0:
            val, pos = decoder._DecodeVarint(options_bytes, pos)
            opts[field_num] = val
        elif wire_type == 2:
            length, pos = decoder._DecodeVarint(options_bytes, pos)
            opts[field_num] = options_bytes[pos : pos + length]
            pos += length
        else:
            break
    return opts


def decode_sdk_manager_options(raw_bytes: Optional[bytes]) -> Optional[Dict[str, str]]:
    if not raw_bytes:
        return None
    fields = decode_method_options(raw_bytes)
    rust = fields.get(1, b"").decode("utf-8", errors="replace")
    go = fields.get(2, b"").decode("utf-8", errors="replace")
    py = fields.get(3, b"").decode("utf-8", errors="replace")
    ts = fields.get(4, b"").decode("utf-8", errors="replace")
    if not (rust or go or py or ts):
        return None
    py_mod = py.rsplit(".", 1)[0] if "." in py else py
    ts_parts = ts.rsplit(".", 1)
    ts_mod = ts_parts[0] if len(ts_parts) == 2 else ts
    ts_class = ts_parts[1] if len(ts_parts) == 2 else ts
    return {
        "rust": rust,
        "go": go,
        "py": py,
        "py_module": py_mod,
        "ts": ts_class,
        "ts_module": ts_mod,
    }


def build_descriptor_pool(descriptor_files: List[str]) -> descriptor_pool.DescriptorPool:
    pool = descriptor_pool.Default()
    for path in descriptor_files:
        fds = descriptor_pb2.FileDescriptorSet()
        with open(path, "rb") as f:
            fds.ParseFromString(f.read())
        for file_proto in fds.file:
            try:
                pool.Add(file_proto)
            except Exception:
                pass
    return pool


def extract_metadata(
    pool: descriptor_pool.DescriptorPool, proto_file: Optional[str] = None
) -> Dict[str, Any]:
    if proto_file is None:
        proto_file = find_proto_file()
    proto_docs = parse_proto_docs(proto_file)

    ext_cmd = pool.FindMessageTypeByName("moosync.types.ExtensionCommand")
    ext_resp = pool.FindMessageTypeByName("moosync.types.ExtensionCommandResponse")
    main_cmd = pool.FindMessageTypeByName("moosync.types.MainCommand")
    main_resp = pool.FindMessageTypeByName("moosync.types.MainCommandResponse")

    guest_req_to_oneof = {
        f.message_type.name: f.name for f in ext_cmd.fields if f.containing_oneof
    }
    guest_resp_to_oneof = {
        f.message_type.name: f.name for f in ext_resp.fields if f.containing_oneof
    }

    host_req_to_oneof = {
        f.message_type.name: f.name for f in main_cmd.fields if f.containing_oneof
    }
    host_resp_to_oneof = {
        f.message_type.name: f.name for f in main_resp.fields if f.containing_oneof
    }

    service_file = pool.FindFileByName("core/types/protos/extension_service.proto")
    host_service = service_file.services_by_name.get("ExtensionHostService")

    host_methods = []
    if host_service:
        for m in host_service.methods:
            raw_opts = m.GetOptions().SerializeToString()
            custom_opts = decode_method_options(raw_opts)

            has_wrapper_val = bool(custom_opts.get(TAG_HAS_WRAPPER, 0))
            req_name = m.input_type.name
            resp_name = m.output_type.name

            host_methods.append({
                "name": m.name,
                "snake_name": to_snake_case(m.name),
                "camel_name": to_camel_case(m.name),
                "pascal_name": to_pascal_case(m.name),
                "req_type": req_name,
                "resp_type": resp_name,
                "has_wrapper": has_wrapper_val,
                "oneof_variant": host_req_to_oneof.get(req_name, to_snake_case(m.name)),
                "resp_oneof_variant": host_resp_to_oneof.get(resp_name, to_snake_case(m.name)),
                "doc": proto_docs.get(m.name, ""),
            })

    guest_services = []
    guest_methods = []
    internal_guest_methods = []
    for service_name, s in service_file.services_by_name.items():
        if service_name == "ExtensionHostService":
            continue

        trait_name = service_name
        if trait_name.endswith("Service"):
            trait_name = trait_name[: -len("Service")]

        methods_in_service = []
        for m in s.methods:
            raw_opts = m.GetOptions().SerializeToString()
            custom_opts = decode_method_options(raw_opts)

            is_event_val = bool(custom_opts.get(TAG_IS_EVENT_NOTIFICATION, 0))
            sdk_manager_val = decode_sdk_manager_options(custom_opts.get(TAG_SDK_MANAGER))
            is_sdk_internal_val = sdk_manager_val is not None
            req_name = m.input_type.name
            resp_name = m.output_type.name

            method_info = {
                "name": m.name,
                "snake_name": to_snake_case(m.name),
                "camel_name": to_camel_case(m.name),
                "pascal_name": to_pascal_case(m.name),
                "req_type": req_name,
                "resp_type": resp_name,
                "is_event": is_event_val,
                "oneof_variant": guest_req_to_oneof.get(req_name, to_snake_case(m.name)),
                "resp_oneof_variant": guest_resp_to_oneof.get(resp_name, to_snake_case(m.name)),
                "service_trait": trait_name,
                "sdk_manager": sdk_manager_val,
                "doc": proto_docs.get(m.name, ""),
            }
            if is_sdk_internal_val:
                internal_guest_methods.append(method_info)
            else:
                methods_in_service.append(method_info)
                guest_methods.append(method_info)

        if methods_in_service:
            guest_services.append({
                "name": service_name,
                "trait_name": trait_name,
                "methods": methods_in_service,
            })

    return {
        "host_methods": host_methods,
        "guest_methods": guest_methods,
        "internal_guest_methods": internal_guest_methods,
        "all_guest_methods": guest_methods + internal_guest_methods,
        "guest_services": guest_services,
    }


def render_template(
    template_dir: str, template_name: str, context: Dict[str, Any], output_path: str
):
    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    env.filters["format_doc"] = format_doc
    template = env.get_template(template_name)
    rendered = template.render(context)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)


def main():
    parser = argparse.ArgumentParser(description="Moosync Extension SDK Generator")
    parser.add_argument(
        "--descriptor-sets",
        nargs="+",
        required=True,
        help="Path to proto descriptor set files",
    )
    parser.add_argument(
        "--templates-dir",
        required=True,
        help="Path to templates directory",
    )
    parser.add_argument(
        "--lang",
        choices=["rust", "ts", "go", "python"],
        help="Target language",
    )
    parser.add_argument("--out-api", help="Output path for generated API file")
    parser.add_argument(
        "--out-dispatcher",
        help="Output path for generated dispatcher file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate SDKs for all supported languages into workspace tree",
    )

    args = parser.parse_args()
    pool = build_descriptor_pool(args.descriptor_sets)
    metadata = extract_metadata(pool)

    if args.all:
        workspace_dir = os.environ.get("BUILD_WORKSPACE_DIRECTORY", os.getcwd())
        targets = [
            ("rust", "wasm-extension-rs/src/generated_api.rs", "wasm-extension-rs/src/generated_dispatcher.rs"),
            ("go", "wasm-extension-go/pkg/api/generated_api.go", "wasm-extension-go/pkg/api/generated_exports.go"),
            ("py", "wasm-extension-py/moosync_edk/generated_api.py", "wasm-extension-py/moosync_edk/generated_dispatcher.py"),
            ("ts", "wasm-extension-js/src/generated_api.ts", "wasm-extension-js/src/generated_events.ts"),
        ]
        for lang_key, api_rel, disp_rel in targets:
            templates_lang_dir = os.path.join(args.templates_dir, lang_key)
            out_api = os.path.join(workspace_dir, api_rel)
            out_disp = os.path.join(workspace_dir, disp_rel)
            render_template(templates_lang_dir, "api.jinja", metadata, out_api)
            render_template(templates_lang_dir, "dispatcher.jinja", metadata, out_disp)

        moounit_templates_dir = os.path.join(args.templates_dir, "moounit")
        moounit_out = os.path.join(workspace_dir, "moounit/generated.py")
        render_template(moounit_templates_dir, "client.jinja", metadata, moounit_out)
        return

    if not args.lang or not args.out_api or not args.out_dispatcher:
        parser.error("Either --all or (--lang, --out-api, --out-dispatcher) must be specified.")

    lang_dir_name = "py" if args.lang == "python" else args.lang
    templates_lang_dir = os.path.join(args.templates_dir, lang_dir_name)
    render_template(
        templates_lang_dir, "api.jinja", metadata, args.out_api
    )
    render_template(
        templates_lang_dir, "dispatcher.jinja", metadata, args.out_dispatcher
    )


if __name__ == "__main__":
    main()
