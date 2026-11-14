// Moosync
// Copyright (C) 2024, 2025, 2026 Moosync <support@moosync.app>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

package api

import (
	extensions "github.com/moosync/moosync/types/extensions"
)

type ChildProcess struct {
	ID  uint64
	PID uint32
}

func (c *ChildProcess) WriteStdin(data []byte) (uint64, error) {
	resp, err := WriteProcessStdin(&extensions.WriteProcessStdinRequest{
		ProcessId: c.ID,
		Data:      data,
	})
	if err != nil {
		return 0, err
	}
	return resp.BytesWritten, nil
}

func (c *ChildProcess) ReadStdout(maxBytes uint64) ([]byte, error) {
	var max *uint64
	if maxBytes > 0 {
		max = &maxBytes
	}
	resp, err := ReadProcessStdout(&extensions.ReadProcessStdoutRequest{
		ProcessId: c.ID,
		MaxBytes:  max,
	})
	if err != nil {
		return nil, err
	}
	return resp.Data, nil
}

func (c *ChildProcess) Kill() (bool, error) {
	resp, err := KillProcess(&extensions.KillProcessRequest{
		ProcessId: c.ID,
	})
	if err != nil {
		return false, err
	}
	return resp.Success, nil
}

func (c *ChildProcess) GetStatus() (bool, *int32, error) {
	resp, err := GetProcessStatus(&extensions.GetProcessStatusRequest{
		ProcessId: c.ID,
	})
	if err != nil {
		return false, nil, err
	}
	return resp.IsRunning, resp.ExitCode, nil
}

func StartProcess(path string, args []string, env map[string]string) (*ChildProcess, error) {
	resp, err := SpawnProcess(&extensions.SpawnProcessRequest{
		Path: path,
		Args: args,
		Env:  env,
	})
	if err != nil {
		return nil, err
	}
	return &ChildProcess{
		ID:  resp.ProcessId,
		PID: resp.Pid,
	}, nil
}
