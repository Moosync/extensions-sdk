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
use extensions_proto::moosync::types::{
    ws_receive_response, ws_send_request, WsCloseRequest, WsConnectRequest, WsReceiveRequest,
    WsSendRequest,
};

#[derive(Debug, Clone)]
pub struct WebSocketClient {
    pub connection_id: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WebSocketMessage {
    Text(String),
    Binary(Vec<u8>),
}

impl WebSocketClient {
    pub fn connect(url: impl Into<String>) -> MoosyncResult<Self> {
        let req = WsConnectRequest {
            url: url.into(),
            headers: Default::default(),
            protocols: Vec::new(),
        };
        let resp = api::ws_connect(req)?;
        Ok(Self {
            connection_id: resp.connection_id,
        })
    }

    pub fn send_text(&self, text: impl Into<String>) -> MoosyncResult<()> {
        let req = WsSendRequest {
            connection_id: self.connection_id,
            payload: Some(ws_send_request::Payload::Text(text.into())),
        };
        api::ws_send(req)?;
        Ok(())
    }

    pub fn send_binary(&self, data: &[u8]) -> MoosyncResult<()> {
        let req = WsSendRequest {
            connection_id: self.connection_id,
            payload: Some(ws_send_request::Payload::Binary(data.to_vec())),
        };
        api::ws_send(req)?;
        Ok(())
    }

    pub fn receive(&self, timeout_ms: Option<u64>) -> MoosyncResult<Option<WebSocketMessage>> {
        let req = WsReceiveRequest {
            connection_id: self.connection_id,
            timeout_ms,
        };
        let resp = api::ws_receive(req)?;
        match resp.payload {
            Some(ws_receive_response::Payload::Text(t)) => Ok(Some(WebSocketMessage::Text(t))),
            Some(ws_receive_response::Payload::Binary(b)) => Ok(Some(WebSocketMessage::Binary(b))),
            None => Ok(None),
        }
    }

    pub fn close(&self, code: Option<u32>, reason: Option<String>) -> MoosyncResult<()> {
        let req = WsCloseRequest {
            connection_id: self.connection_id,
            code,
            reason,
        };
        api::ws_close(req)?;
        Ok(())
    }
}
