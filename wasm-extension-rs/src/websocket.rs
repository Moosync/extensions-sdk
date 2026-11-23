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

use std::collections::HashMap;
use std::sync::{Arc, LazyLock, Mutex};

use crate::api::{self, MoosyncResult};
use extensions_proto::moosync::types::{
    ws_event_request, ws_send_request, WsCloseRequest, WsClosed, WsConnectRequest, WsEventRequest,
    WsSendRequest,
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WebSocketMessage {
    Text(String),
    Binary(Vec<u8>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WsCloseEvent {
    pub code: Option<u32>,
    pub reason: Option<String>,
    pub error: Option<String>,
}

impl From<WsClosed> for WsCloseEvent {
    fn from(closed: WsClosed) -> Self {
        Self {
            code: closed.code,
            reason: closed.reason,
            error: closed.error,
        }
    }
}

type MessageCallback = Arc<dyn Fn(WebSocketMessage) + Send + Sync>;
type CloseCallback = Arc<dyn Fn(WsCloseEvent) + Send + Sync>;

#[derive(Default)]
struct ConnectionHandlers {
    on_message: Option<MessageCallback>,
    on_close: Option<CloseCallback>,
}

static WS_HANDLERS: LazyLock<Mutex<HashMap<u64, ConnectionHandlers>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

pub struct WebSocketManager;

impl WebSocketManager {
    pub fn on_message(
        connection_id: u64,
        callback: impl Fn(WebSocketMessage) + Send + Sync + 'static,
    ) {
        let mut handlers = WS_HANDLERS.lock().unwrap();
        let entry = handlers.entry(connection_id).or_default();
        entry.on_message = Some(Arc::new(callback));
    }

    pub fn on_close(connection_id: u64, callback: impl Fn(WsCloseEvent) + Send + Sync + 'static) {
        let mut handlers = WS_HANDLERS.lock().unwrap();
        let entry = handlers.entry(connection_id).or_default();
        entry.on_close = Some(Arc::new(callback));
    }

    pub fn remove(connection_id: u64) {
        let mut handlers = WS_HANDLERS.lock().unwrap();
        handlers.remove(&connection_id);
    }

    fn message_callback(connection_id: u64) -> Option<MessageCallback> {
        let handlers = WS_HANDLERS.lock().unwrap();
        handlers
            .get(&connection_id)
            .and_then(|entry| entry.on_message.clone())
    }

    pub(crate) fn handle_event(req: WsEventRequest) {
        let connection_id = req.connection_id;
        match req.event {
            Some(ws_event_request::Event::Text(text)) => {
                if let Some(cb) = Self::message_callback(connection_id) {
                    cb(WebSocketMessage::Text(text));
                }
            }
            Some(ws_event_request::Event::Binary(binary)) => {
                if let Some(cb) = Self::message_callback(connection_id) {
                    cb(WebSocketMessage::Binary(binary));
                }
            }
            Some(ws_event_request::Event::Closed(closed)) => {
                let callback = {
                    let mut handlers = WS_HANDLERS.lock().unwrap();
                    handlers
                        .remove(&connection_id)
                        .and_then(|entry| entry.on_close)
                };
                if let Some(cb) = callback {
                    cb(closed.into());
                }
            }
            None => {}
        }
    }
}

#[derive(Debug, Clone)]
pub struct WebSocketClient {
    pub connection_id: u64,
}

impl WebSocketClient {
    pub fn connect(url: impl Into<String>) -> MoosyncResult<Self> {
        let req = WsConnectRequest {
            url: url.into(),
            headers: Default::default(),
            protocols: Vec::new(),
        };
        let resp = api::ws_connect(req)?;
        let mut handlers = WS_HANDLERS.lock().unwrap();
        handlers.entry(resp.connection_id).or_default();
        Ok(Self {
            connection_id: resp.connection_id,
        })
    }

    pub fn on_message(&self, callback: impl Fn(WebSocketMessage) + Send + Sync + 'static) {
        WebSocketManager::on_message(self.connection_id, callback);
    }

    pub fn on_close(&self, callback: impl Fn(WsCloseEvent) + Send + Sync + 'static) {
        WebSocketManager::on_close(self.connection_id, callback);
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

    pub fn close(&self, code: Option<u32>, reason: Option<String>) -> MoosyncResult<()> {
        WebSocketManager::remove(self.connection_id);
        let req = WsCloseRequest {
            connection_id: self.connection_id,
            code,
            reason,
        };
        api::ws_close(req)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex as StdMutex;

    #[test]
    fn test_websocket_manager_handle_event() {
        let conn_id = 12345;
        let received = Arc::new(StdMutex::new(Vec::new()));
        let closed = Arc::new(StdMutex::new(Vec::new()));

        let received_clone = received.clone();
        WebSocketManager::on_message(conn_id, move |msg| {
            received_clone.lock().unwrap().push(msg);
        });

        let closed_clone = closed.clone();
        WebSocketManager::on_close(conn_id, move |ev| {
            closed_clone.lock().unwrap().push(ev);
        });

        WebSocketManager::handle_event(WsEventRequest {
            connection_id: conn_id,
            event: Some(ws_event_request::Event::Text("hello-rs".into())),
        });
        WebSocketManager::handle_event(WsEventRequest {
            connection_id: conn_id,
            event: Some(ws_event_request::Event::Binary(vec![7, 8])),
        });
        WebSocketManager::handle_event(WsEventRequest {
            connection_id: conn_id,
            event: Some(ws_event_request::Event::Closed(WsClosed {
                code: Some(1000),
                reason: Some("normal".into()),
                error: None,
            })),
        });
        WebSocketManager::handle_event(WsEventRequest {
            connection_id: conn_id,
            event: Some(ws_event_request::Event::Text("ignored".into())),
        });

        let msgs = received.lock().unwrap();
        assert_eq!(
            *msgs,
            vec![
                WebSocketMessage::Text("hello-rs".into()),
                WebSocketMessage::Binary(vec![7, 8]),
            ]
        );

        let closes = closed.lock().unwrap();
        assert_eq!(
            *closes,
            vec![WsCloseEvent {
                code: Some(1000),
                reason: Some("normal".into()),
                error: None,
            }]
        );
    }
}
