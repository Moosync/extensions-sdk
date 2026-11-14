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

use crate::api::Extension;
pub use crate::generated_dispatcher::handle_command;
use extism_pdk::FnResult;
use std::{cell::RefCell, rc::Rc};

thread_local!(
    static EXTENSION: RefCell<Option<Rc<Box<dyn Extension>>>> = RefCell::new(None);
);

#[tracing::instrument(level = "debug", skip(extension))]
pub fn register_extension(extension: Box<dyn Extension>) -> FnResult<()> {
    EXTENSION.with(|ext| {
        ext.borrow_mut().replace(Rc::new(extension));
    });
    Ok(())
}

pub(crate) fn with_extension<F, R>(f: F) -> Result<R, extism_pdk::Error>
where
    F: FnOnce(&dyn Extension) -> Result<R, extism_pdk::Error>,
{
    EXTENSION.with(|ext| {
        if let Some(ext) = ext.borrow().as_ref() {
            f(ext.as_ref().as_ref())
        } else {
            Err(extism_pdk::Error::msg("Extension not registered"))
        }
    })
}

#[derive(Debug)]
pub enum MoosyncError {
    String(String),
}

impl From<String> for MoosyncError {
    fn from(e: String) -> Self {
        MoosyncError::String(e)
    }
}

impl From<extism_pdk::Error> for MoosyncError {
    fn from(e: extism_pdk::Error) -> Self {
        MoosyncError::String(e.to_string())
    }
}

impl From<&str> for MoosyncError {
    fn from(s: &str) -> Self {
        MoosyncError::String(s.to_string())
    }
}

impl std::fmt::Display for MoosyncError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MoosyncError::String(s) => write!(f, "{}", s),
        }
    }
}

impl std::error::Error for MoosyncError {}
