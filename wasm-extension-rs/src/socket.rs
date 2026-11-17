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

use crate::api::{self, MoosyncResult};
use extensions_proto::moosync::types::{OpenClientFdRequest, ReadSockRequest, WriteSockRequest};

#[derive(Debug, Clone)]
pub struct SocketClient {
    pub sock_id: i64,
}

impl SocketClient {
    pub fn connect(path: impl Into<String>) -> MoosyncResult<Self> {
        let resp = api::host_open_client_fd(OpenClientFdRequest { path: path.into() })?;
        if resp.sock_id < 0 {
            return Err("Failed to connect to socket".into());
        }
        Ok(Self {
            sock_id: resp.sock_id,
        })
    }

    pub fn write(&self, data: &[u8]) -> MoosyncResult<i64> {
        let resp = api::host_write_sock(WriteSockRequest {
            sock_id: self.sock_id,
            buf: data.to_vec(),
        })?;
        Ok(resp.bytes_written)
    }

    pub fn read(&self, read_len: u64) -> MoosyncResult<Vec<u8>> {
        let resp = api::host_read_sock(ReadSockRequest {
            sock_id: self.sock_id,
            read_len,
        })?;
        Ok(resp.data)
    }
}

pub fn open_sock(path: impl Into<String>) -> MoosyncResult<SocketClient> {
    SocketClient::connect(path)
}
