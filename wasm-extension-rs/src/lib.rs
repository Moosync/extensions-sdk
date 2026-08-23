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
pub use extensions_proto;
pub use songs_proto;
pub use themes_proto;
pub use ui_proto;
pub use duration_proto;
pub use prost_types;
pub use extensions_proto::moosync::types::*;
pub use songs_proto::moosync::types::*;
pub use themes_proto::moosync::types::*;
pub use ui_proto::moosync::types::*;

pub mod api;
pub mod handler;
pub mod http;
pub mod response_utils;

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
    Prost(cmd): Prost<ExtensionCommand>,
) -> FnResult<Prost<ExtensionCommandResponse>> {
    let res = handler::handle_command(cmd)?;
    Ok(Prost(res))
}

/// Converts a standard Rust `Duration` into a protobuf `Duration`.
pub fn duration_to_proto(d: std::time::Duration) -> duration_proto::google::protobuf::Duration {
    duration_proto::google::protobuf::Duration {
        seconds: d.as_secs() as i64,
        nanos: d.subsec_nanos() as i32,
    }
}
