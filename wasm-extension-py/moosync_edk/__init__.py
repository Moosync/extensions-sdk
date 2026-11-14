# Moosync Python Extension SDK (moosync_edk)

import os
import sys
from datetime import timedelta
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar, Union

import extism
from core.types.protos import extensions_pb2, preferences_pb2, songs_pb2, themes_pb2, ui_pb2
from core.types.protos.extensions_pb2 import *
from core.types.protos.preferences_pb2 import *
from core.types.protos.songs_pb2 import *
from core.types.protos.ui_pb2 import *
from google.protobuf.duration_pb2 import Duration
from google.protobuf.message import Message

edk_paths = [p + "/moosync_edk" for p in sys.path if p.endswith("wasm-extension-py")]
if "__file__" in globals():
    edk_paths.append(os.path.dirname(os.path.abspath(__file__)))

__package__ = "moosync_edk"
__path__ = edk_paths
if "moosync_edk" not in sys.modules:
    sys.modules["moosync_edk"] = sys.modules[__name__]


@extism.import_fn("extism:host/user", "send_main_command")
def send_main_command_raw(data: int) -> int: ...


def send_main_command(command: extensions_pb2.MainCommand) -> extensions_pb2.MainCommandResponse:
    serialized = command.SerializeToString()
    mem = extism.memory.alloc(serialized)
    if mem is None:
        raise RuntimeError("Failed to allocate memory for main command")
    res_offset = send_main_command_raw(mem.offset)
    res_handle = extism.memory.find(res_offset)
    if res_handle is None:
        raise RuntimeError(f"Failed to find memory for response at offset {res_offset}")
    res_bytes = extism.memory.bytes(res_handle)
    extism.memory.free(mem)
    res = extensions_pb2.MainCommandResponse()
    res.ParseFromString(res_bytes)
    return res


_extension_instance = None


def register_extension(instance):
    global _extension_instance
    _extension_instance = instance


def get_extension():
    return _extension_instance


from .generated_api import *
from .generated_dispatcher import *
from .platform import PlatformInfo, get_platform
from .cache import get_cache, set_cache
from .socket import SocketClient
from .websocket import WebSocketClient, WebSocketMessage
from .lrc import parse_lrc
from .http import (
    HttpRequest,
    HttpResponse,
    HttpResult,
    http_batch_request,
    http_batch_get,
    http_request,
    http_get,
)
from .process import ChildProcess, spawn_process

class CustomPrint:
    buf = ""

    def write(self, text):
        self.buf += text
        self.flush()

    def flush(self):
        extism.log(extism.LogLevel.Debug, self.buf)
        self.buf = ""

def duration_to_proto(td: timedelta) -> Duration:
    """Convert datetime.timedelta to google.protobuf.Duration."""
    duration = Duration()
    duration.seconds = int(td.total_seconds())
    duration.nanos = int((td.microseconds % 1000000) * 1000)
    return duration

def proto_to_duration(d: Duration) -> timedelta:
    """Convert google.protobuf.Duration to datetime.timedelta."""
    return timedelta(seconds=d.seconds, microseconds=int(d.nanos / 1000))

# Import extension module at the end to avoid circular dependency issues
extension_module = None
try:
    import sdk_main as extension_module
except ImportError as e:
    print(f"WARNING: Could not import 'main' module: {e}")

@extism.plugin_fn
def entry():
    sys.stdout = CustomPrint()
    print("PYTHON: entry() called")
    if extension_module:
        if hasattr(extension_module, "entry"):
            print("PYTHON: Calling extension_module.entry()")
            extension_module.entry()
        else:
            print("WARNING: 'main' module does not have an 'entry' function")
    else:
        raise Exception("Extension module not loaded")

ExtensionApi.get_platform = staticmethod(get_platform)
