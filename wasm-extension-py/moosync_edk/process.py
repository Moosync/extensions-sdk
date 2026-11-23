from collections.abc import Callable
from core.types.protos import extensions_pb2
from moosync_edk.generated_api import (
    spawn_process as host_spawn_process,
    write_process_stdin as host_write_process_stdin,
    read_process_stdout as host_read_process_stdout,
    kill_process as host_kill_process,
    get_process_status as host_get_process_status,
)


class _ProcessHandlers:
    def __init__(self) -> None:
        self.on_stdout: Callable[[bytes], None] | None = None
        self.on_stderr: Callable[[bytes], None] | None = None
        self.on_exit: Callable[[int], None] | None = None


class ChildProcess:
    _handlers: dict[int, _ProcessHandlers] = {}

    def __init__(self, process_id: int, pid: int):
        self.id = process_id
        self.pid = pid

    @classmethod
    def _handle_event(cls, req: extensions_pb2.ProcessEventRequest) -> None:
        process_id = req.process_id
        field = req.WhichOneof("event")
        if field == "output":
            entry = cls._handlers.get(process_id)
            if entry:
                if req.output.stdout and entry.on_stdout:
                    entry.on_stdout(req.output.stdout)
                if req.output.stderr and entry.on_stderr:
                    entry.on_stderr(req.output.stderr)
        elif field == "exited":
            entry = cls._handlers.pop(process_id, None)
            if entry and entry.on_exit:
                entry.on_exit(req.exited)

    def write_stdin(self, data: bytes | str) -> int:
        if isinstance(data, str):
            data = data.encode("utf-8")
        req = extensions_pb2.WriteProcessStdinRequest(
            process_id=self.id,
            data=data,
        )
        resp = host_write_process_stdin(req)
        return resp.bytes_written if resp else 0

    def read_stdout(self, max_bytes: int | None = None) -> bytes:
        kwargs: dict[str, int] = {"process_id": self.id}
        if max_bytes is not None:
            kwargs["max_bytes"] = max_bytes
        req = extensions_pb2.ReadProcessStdoutRequest(**kwargs)
        resp = host_read_process_stdout(req)
        return resp.data if resp else b""

    def read_stdout_string(self, max_bytes: int | None = None) -> str:
        data = self.read_stdout(max_bytes)
        return data.decode("utf-8", errors="replace")

    def on_stdout(self, callback: Callable[[bytes], None]) -> None:
        entry = ChildProcess._handlers.setdefault(self.id, _ProcessHandlers())
        entry.on_stdout = callback

    def on_stderr(self, callback: Callable[[bytes], None]) -> None:
        entry = ChildProcess._handlers.setdefault(self.id, _ProcessHandlers())
        entry.on_stderr = callback

    def on_exit(self, callback: Callable[[int], None]) -> None:
        entry = ChildProcess._handlers.setdefault(self.id, _ProcessHandlers())
        entry.on_exit = callback

    def kill(self) -> bool:
        req = extensions_pb2.KillProcessRequest(process_id=self.id)
        resp = host_kill_process(req)
        return resp.success if resp else False

    def get_status(self) -> tuple[bool, int | None]:
        req = extensions_pb2.GetProcessStatusRequest(process_id=self.id)
        resp = host_get_process_status(req)
        if resp:
            return resp.is_running, resp.exit_code if resp.HasField("exit_code") else None
        return False, None


def spawn_process(
    path: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> ChildProcess:
    req = extensions_pb2.SpawnProcessRequest(
        path=path,
        args=args or [],
        env=env or {},
    )
    resp = host_spawn_process(req)
    if not resp:
        raise RuntimeError("Failed to spawn process: no response from host")
    return ChildProcess(resp.process_id, resp.pid)
