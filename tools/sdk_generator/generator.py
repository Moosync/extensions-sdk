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
import sys
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
TAG_TRANSPORT = 60002
TAG_WASM_SYMBOL = 60003


def to_snake_case(name: str) -> str:
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def to_camel_case(name: str) -> str:
    snake = to_snake_case(name)
    components = snake.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_pascal_case(name: str) -> str:
    return "".join(x.title() for x in to_snake_case(name).split("_"))


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
            opts[field_num] = options_bytes[pos:pos+length].decode("utf-8", errors="replace")
            pos += length
        else:
            break
    return opts


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


def extract_metadata(pool: descriptor_pool.DescriptorPool) -> Dict[str, Any]:
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
    guest_service = service_file.services_by_name.get("ExtensionGuestService")

    host_methods = []
    if host_service:
        for m in host_service.methods:
            raw_opts = m.GetOptions().SerializeToString()
            custom_opts = decode_method_options(raw_opts)

            transport_val = custom_opts.get(TAG_TRANSPORT, 0)
            wasm_symbol_val = custom_opts.get(TAG_WASM_SYMBOL, "")

            req_name = m.input_type.name
            resp_name = m.output_type.name

            host_methods.append({
                "name": m.name,
                "snake_name": to_snake_case(m.name),
                "camel_name": to_camel_case(m.name),
                "pascal_name": to_pascal_case(m.name),
                "req_type": req_name,
                "resp_type": resp_name,
                "transport": transport_val,  # 0: MAIN_COMMAND, 1: DIRECT_HOST_FN
                "wasm_symbol": wasm_symbol_val or to_snake_case(m.name),
                "oneof_variant": host_req_to_oneof.get(req_name, to_snake_case(m.name)),
                "resp_oneof_variant": host_resp_to_oneof.get(resp_name, to_snake_case(m.name)),
            })

    guest_methods = []
    if guest_service:
        for m in guest_service.methods:
            raw_opts = m.GetOptions().SerializeToString()
            custom_opts = decode_method_options(raw_opts)

            is_event_val = bool(custom_opts.get(TAG_IS_EVENT_NOTIFICATION, 0))

            req_name = m.input_type.name
            resp_name = m.output_type.name

            guest_methods.append({
                "name": m.name,
                "snake_name": to_snake_case(m.name),
                "camel_name": to_camel_case(m.name),
                "pascal_name": to_pascal_case(m.name),
                "req_type": req_name,
                "resp_type": resp_name,
                "is_event": is_event_val,
                "oneof_variant": guest_req_to_oneof.get(req_name, to_snake_case(m.name)),
                "resp_oneof_variant": guest_resp_to_oneof.get(resp_name, to_snake_case(m.name)),
            })

    return {
        "host_methods": host_methods,
        "guest_methods": guest_methods,
    }


def render_template(
    template_dir: str, template_name: str, context: Dict[str, Any], output_path: str
):
    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
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
