import unittest
from core.types.protos import extensions_pb2
from moosync_edk.process import ChildProcess


class TestChildProcess(unittest.TestCase):
    def test_handle_event_output_and_exited(self):
        proc = ChildProcess(process_id=88, pid=101)
        stdout_chunks = []
        stderr_chunks = []
        exit_codes = []

        proc.on_stdout(stdout_chunks.append)
        proc.on_stderr(stderr_chunks.append)
        proc.on_exit(exit_codes.append)

        ChildProcess._handle_event(
            extensions_pb2.ProcessEventRequest(
                process_id=88,
                output=extensions_pb2.ProcessOutput(stdout=b"out-py", stderr=b"err-py"),
            )
        )
        ChildProcess._handle_event(
            extensions_pb2.ProcessEventRequest(process_id=88, exited=3)
        )
        ChildProcess._handle_event(
            extensions_pb2.ProcessEventRequest(
                process_id=88,
                output=extensions_pb2.ProcessOutput(stdout=b"ignored"),
            )
        )

        self.assertEqual(stdout_chunks, [b"out-py"])
        self.assertEqual(stderr_chunks, [b"err-py"])
        self.assertEqual(exit_codes, [3])


if __name__ == "__main__":
    unittest.main()
