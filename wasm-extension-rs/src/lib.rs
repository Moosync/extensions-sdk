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

pub use extism_pdk::{config, error, info, log, warn};
use extism_pdk::{plugin_fn, FnResult, Prost};

// Re-export generated types
pub use duration_proto;
pub use extension_service_proto;
pub use extensions_proto;
pub use preferences_proto;
pub use prost;
pub use prost_types;
pub use serde;
pub use serde_json;
pub use songs_proto;
pub use themes_proto;
pub use tracing;
pub use ui_proto;

#[path = "generated_api.rs"]
pub mod api;
pub mod cache;
pub mod generated_dispatcher;
pub mod handler;
pub mod http;
pub mod platform;
pub mod process;
pub mod response_utils;
pub mod socket;
pub mod websocket;

pub mod types {
    pub use crate::api::MoosyncResult;
    pub use crate::handler::MoosyncError;
    pub use crate::platform::PlatformInfo;
    pub use crate::process::ChildProcess;
    pub use crate::response_utils::LrcParseError;
    pub use crate::socket::SocketClient;
    pub use crate::websocket::{WebSocketClient, WebSocketMessage};
    pub use duration_proto::google::protobuf::Duration;
    pub use extensions_proto::moosync::types::*;
    pub use extensions_proto::struct_proto::google::protobuf::{
        value, ListValue, Struct, Value,
    };
    pub use preferences_proto::moosync::types::*;
    pub use songs_proto::moosync::types::*;
    pub use themes_proto::moosync::types::*;
    pub use ui_proto::moosync::types::*;
}

pub use api::MoosyncResult;
pub use handler::MoosyncError;

unsafe extern "C" {
    fn init();
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn entry() -> FnResult<()> {
    unsafe {
        init();
    }
    Ok(())
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn handle_extension_command(
    Prost(cmd): Prost<types::ExtensionCommand>,
) -> FnResult<Prost<types::ExtensionCommandResponse>> {
    let res = handler::handle_command(cmd)?;
    Ok(Prost(res))
}
