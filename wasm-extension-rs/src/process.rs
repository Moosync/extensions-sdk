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
use std::sync::{Arc, LazyLock, Mutex};

use extensions_proto::moosync::types::{
    GetProcessStatusRequest, KillProcessRequest, ProcessEventRequest, ReadProcessStdoutRequest,
    SpawnProcessRequest, WriteProcessStdinRequest, process_event_request,
};

use crate::api::{self, MoosyncResult};
use crate::handler::MoosyncError;

type OutputCallback = Arc<dyn Fn(&[u8]) + Send + Sync>;
type ExitCallback = Arc<dyn Fn(i32) + Send + Sync>;

#[derive(Default)]
struct ProcessHandlers {
    on_stdout: Option<OutputCallback>,
    on_stderr: Option<OutputCallback>,
    on_exit: Option<ExitCallback>,
}

static PROCESS_HANDLERS: LazyLock<Mutex<HashMap<u64, ProcessHandlers>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

pub struct ChildProcess {
    pub id: usize,
    pub pid: u32,
}

impl ChildProcess {
    pub(crate) fn handle_event(req: ProcessEventRequest) {
        let process_id = req.process_id;
        match req.event {
            Some(process_event_request::Event::Output(output)) => {
                let (on_stdout, on_stderr) = {
                    let handlers = PROCESS_HANDLERS.lock().unwrap();
                    handlers
                        .get(&process_id)
                        .map(|entry| (entry.on_stdout.clone(), entry.on_stderr.clone()))
                        .unwrap_or((None, None))
                };
                if !output.stdout.is_empty()
                    && let Some(cb) = on_stdout
                {
                    cb(&output.stdout);
                }
                if !output.stderr.is_empty()
                    && let Some(cb) = on_stderr
                {
                    cb(&output.stderr);
                }
            }
            Some(process_event_request::Event::Exited(code)) => {
                let cb = {
                    let mut handlers = PROCESS_HANDLERS.lock().unwrap();
                    handlers
                        .remove(&process_id)
                        .and_then(|entry| entry.on_exit)
                };
                if let Some(cb) = cb {
                    cb(code);
                }
            }
            None => {}
        }
    }

    fn update_handlers(&self, f: impl FnOnce(&mut ProcessHandlers)) {
        let mut handlers = PROCESS_HANDLERS.lock().unwrap();
        let entry = handlers.entry(self.id as u64).or_default();
        f(entry);
    }

    pub fn on_stdout<F>(&self, callback: F)
    where
        F: Fn(&[u8]) + Send + Sync + 'static,
    {
        self.update_handlers(|entry| entry.on_stdout = Some(Arc::new(callback)));
    }

    pub fn on_stderr<F>(&self, callback: F)
    where
        F: Fn(&[u8]) + Send + Sync + 'static,
    {
        self.update_handlers(|entry| entry.on_stderr = Some(Arc::new(callback)));
    }

    pub fn on_exit<F>(&self, callback: F)
    where
        F: Fn(i32) + Send + Sync + 'static,
    {
        self.update_handlers(|entry| entry.on_exit = Some(Arc::new(callback)));
    }

    pub fn write_stdin(&self, data: &[u8]) -> MoosyncResult<u64> {
        let req = WriteProcessStdinRequest {
            process_id: self.id as u64,
            data: data.to_vec(),
        };
        let resp = api::write_process_stdin(req)?;
        Ok(resp.bytes_written)
    }

    pub fn read_stdout(&self, max_bytes: Option<u64>) -> MoosyncResult<Vec<u8>> {
        let req = ReadProcessStdoutRequest {
            process_id: self.id as u64,
            max_bytes,
        };
        let resp = api::read_process_stdout(req)?;
        Ok(resp.data)
    }

    pub fn read_stdout_string(&self, max_bytes: Option<u64>) -> MoosyncResult<String> {
        let bytes = self.read_stdout(max_bytes)?;
        String::from_utf8(bytes).map_err(|e| MoosyncError::String(e.to_string()))
    }

    pub fn kill(&self) -> MoosyncResult<bool> {
        let req = KillProcessRequest {
            process_id: self.id as u64,
        };
        let resp = api::kill_process(req)?;
        Ok(resp.success)
    }

    pub fn get_status(&self) -> MoosyncResult<(bool, Option<i32>)> {
        let req = GetProcessStatusRequest {
            process_id: self.id as u64,
        };
        let resp = api::get_process_status(req)?;
        Ok((resp.is_running, resp.exit_code))
    }
}

pub fn spawn_process(
    path: impl Into<String>,
    args: &[impl AsRef<str>],
    env: &HashMap<String, String>,
) -> MoosyncResult<ChildProcess> {
    let req = SpawnProcessRequest {
        path: path.into(),
        args: args.iter().map(|s| s.as_ref().to_string()).collect(),
        env: env.clone(),
    };
    let resp = api::host_spawn_process(req)?;
    Ok(ChildProcess {
        id: resp.process_id as usize,
        pid: resp.pid,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use extensions_proto::moosync::types::ProcessOutput;

    #[test]
    fn test_child_process_handle_event() {
        let proc = ChildProcess { id: 9876, pid: 100 };
        let stdout_buf = Arc::new(Mutex::new(Vec::new()));
        let stderr_buf = Arc::new(Mutex::new(Vec::new()));
        let exit_codes = Arc::new(Mutex::new(Vec::new()));

        let out_clone = stdout_buf.clone();
        proc.on_stdout(move |data| out_clone.lock().unwrap().extend_from_slice(data));
        let err_clone = stderr_buf.clone();
        proc.on_stderr(move |data| err_clone.lock().unwrap().extend_from_slice(data));
        let exit_clone = exit_codes.clone();
        proc.on_exit(move |code| exit_clone.lock().unwrap().push(code));

        ChildProcess::handle_event(ProcessEventRequest {
            process_id: 9876,
            event: Some(process_event_request::Event::Output(ProcessOutput {
                stdout: b"hello ".to_vec(),
                stderr: b"warn".to_vec(),
            })),
        });
        ChildProcess::handle_event(ProcessEventRequest {
            process_id: 9876,
            event: Some(process_event_request::Event::Exited(0)),
        });
        ChildProcess::handle_event(ProcessEventRequest {
            process_id: 9876,
            event: Some(process_event_request::Event::Output(ProcessOutput {
                stdout: b"ignored".to_vec(),
                stderr: Vec::new(),
            })),
        });

        assert_eq!(*stdout_buf.lock().unwrap(), b"hello ");
        assert_eq!(*stderr_buf.lock().unwrap(), b"warn");
        assert_eq!(*exit_codes.lock().unwrap(), vec![0]);
    }
}
