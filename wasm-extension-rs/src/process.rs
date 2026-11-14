// Moosync
// Copyright (C) 2024, 2025  Moosync <support@moosync.app>
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

use std::collections::HashMap;
use crate::api::MoosyncResult;

pub struct ChildProcess {
    pub id: usize,
    pub pid: u32,
}

impl ChildProcess {
    pub fn write_stdin(&self, data: &[u8]) -> MoosyncResult<u64> {
        let req = extensions_proto::moosync::types::WriteProcessStdinRequest {
            process_id: self.id as u64,
            data: data.to_vec(),
        };
        let resp = crate::api::host_api::write_process_stdin(req)?;
        Ok(resp.bytes_written)
    }

    pub fn read_stdout(&self, max_bytes: Option<u64>) -> MoosyncResult<Vec<u8>> {
        let req = extensions_proto::moosync::types::ReadProcessStdoutRequest {
            process_id: self.id as u64,
            max_bytes,
        };
        let resp = crate::api::host_api::read_process_stdout(req)?;
        Ok(resp.data)
    }

    pub fn kill(&self) -> MoosyncResult<bool> {
        let req = extensions_proto::moosync::types::KillProcessRequest {
            process_id: self.id as u64,
        };
        let resp = crate::api::host_api::kill_process(req)?;
        Ok(resp.success)
    }

    pub fn get_status(&self) -> MoosyncResult<(bool, Option<i32>)> {
        let req = extensions_proto::moosync::types::GetProcessStatusRequest {
            process_id: self.id as u64,
        };
        let resp = crate::api::host_api::get_process_status(req)?;
        Ok((resp.is_running, resp.exit_code))
    }
}

pub fn spawn_process(
    path: impl Into<String>,
    args: &[impl AsRef<str>],
    env: &HashMap<String, String>,
) -> MoosyncResult<ChildProcess> {
    let req = extensions_proto::moosync::types::SpawnProcessRequest {
        path: path.into(),
        args: args.iter().map(|s| s.as_ref().to_string()).collect(),
        env: env.clone(),
    };
    let resp = crate::api::host_api::spawn_process(req)?;
    Ok(ChildProcess {
        id: resp.process_id as usize,
        pid: resp.pid,
    })
}

pub fn notify_player_event(
    req: extensions_proto::moosync::types::NotifyPlayerEventRequest,
) -> MoosyncResult<()> {
    crate::api::host_api::notify_player_event(req)?;
    Ok(())
}
