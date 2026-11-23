package api

import (
	"bytes"
	"testing"

	extensions "github.com/moosync/moosync/types/extensions"
)

func TestChildProcessHandleEvent(t *testing.T) {
	proc := &ChildProcess{ID: 777, PID: 42}
	var stdoutBuf bytes.Buffer
	var stderrBuf bytes.Buffer
	var exitCodes []int32

	proc.OnStdout(func(data []byte) {
		stdoutBuf.Write(data)
	})
	proc.OnStderr(func(data []byte) {
		stderrBuf.Write(data)
	})
	proc.OnExit(func(code int32) {
		exitCodes = append(exitCodes, code)
	})

	defaultChildProcess.handleEvent(&extensions.ProcessEventRequest{
		ProcessId: 777,
		Event: &extensions.ProcessEventRequest_Output{
			Output: &extensions.ProcessOutput{
				Stdout: []byte("out "),
				Stderr: []byte("err"),
			},
		},
	})
	defaultChildProcess.handleEvent(&extensions.ProcessEventRequest{
		ProcessId: 777,
		Event:     &extensions.ProcessEventRequest_Exited{Exited: 5},
	})
	defaultChildProcess.handleEvent(&extensions.ProcessEventRequest{
		ProcessId: 777,
		Event: &extensions.ProcessEventRequest_Output{
			Output: &extensions.ProcessOutput{
				Stdout: []byte("ignored"),
			},
		},
	})

	if stdoutBuf.String() != "out " {
		t.Fatalf("unexpected stdout: %q", stdoutBuf.String())
	}
	if stderrBuf.String() != "err" {
		t.Fatalf("unexpected stderr: %q", stderrBuf.String())
	}
	if len(exitCodes) != 1 || exitCodes[0] != 5 {
		t.Fatalf("unexpected exit codes: %v", exitCodes)
	}
}
