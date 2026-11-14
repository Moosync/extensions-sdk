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

from typing import Dict, List, Optional, Tuple

from core.types.protos import extensions_pb2
from moosync_edk import generated_api


class ChildProcess:
    def __init__(self, process_id: int, pid: int):
        self.id = process_id
        self.pid = pid

    def write_stdin(self, data: bytes) -> int:
        req = extensions_pb2.WriteProcessStdinRequest(
            process_id=self.id,
            data=data,
        )
        resp = generated_api.write_process_stdin(req)
        return resp.bytes_written

    def read_stdout(self, max_bytes: Optional[int] = None) -> bytes:
        kwargs = {"process_id": self.id}
        if max_bytes is not None:
            kwargs["max_bytes"] = max_bytes
        req = extensions_pb2.ReadProcessStdoutRequest(**kwargs)
        resp = generated_api.read_process_stdout(req)
        return resp.data

    def kill(self) -> bool:
        req = extensions_pb2.KillProcessRequest(process_id=self.id)
        resp = generated_api.kill_process(req)
        return resp.success

    def get_status(self) -> Tuple[bool, Optional[int]]:
        req = extensions_pb2.GetProcessStatusRequest(process_id=self.id)
        resp = generated_api.get_process_status(req)
        return resp.is_running, resp.exit_code if resp.HasField("exit_code") else None


def spawn_process(
    path: str,
    args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
) -> ChildProcess:
    req = extensions_pb2.SpawnProcessRequest(
        path=path,
        args=args or [],
        env=env or {},
    )
    resp = generated_api.spawn_process(req)
    return ChildProcess(resp.process_id, resp.pid)


def notify_player_event(req: extensions_pb2.NotifyPlayerEventRequest) -> extensions_pb2.NotifyPlayerEventResponse:
    return generated_api.notify_player_event(req)
