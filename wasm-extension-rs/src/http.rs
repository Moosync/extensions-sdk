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
use extism_pdk::{host_fn, Prost};
pub use extensions_proto::moosync::types::{
    BatchHttpRequest, BatchHttpResponse, HttpRequest as ProtoHttpRequest,
    HttpResponse as ProtoHttpResponse,
};
use crate::handler::MoosyncError;

#[host_fn]
extern "ExtismHost" {
    fn batch_http_request(req: Prost<BatchHttpRequest>) -> Prost<BatchHttpResponse>;
}

#[derive(Debug, Clone, Default)]
pub struct HttpRequest {
    pub url: String,
    pub method: String,
    pub headers: HashMap<String, String>,
    pub body: Option<Vec<u8>>,
    pub timeout_ms: Option<u64>,
}

impl HttpRequest {
    pub fn new<S: Into<String>>(url: S) -> Self {
        Self {
            url: url.into(),
            method: "GET".to_string(),
            headers: HashMap::new(),
            body: None,
            timeout_ms: None,
        }
    }

    pub fn get<S: Into<String>>(url: S) -> Self {
        Self::new(url)
    }

    pub fn post<S: Into<String>>(url: S) -> Self {
        Self {
            url: url.into(),
            method: "POST".to_string(),
            headers: HashMap::new(),
            body: None,
            timeout_ms: None,
        }
    }

    pub fn method<S: Into<String>>(mut self, method: S) -> Self {
        self.method = method.into();
        self
    }

    pub fn header<K: Into<String>, V: Into<String>>(mut self, key: K, value: V) -> Self {
        self.headers.insert(key.into(), value.into());
        self
    }

    pub fn headers(mut self, headers: HashMap<String, String>) -> Self {
        self.headers.extend(headers);
        self
    }

    pub fn body<B: Into<Vec<u8>>>(mut self, body: B) -> Self {
        self.body = Some(body.into());
        self
    }

    pub fn json<T: serde::Serialize>(mut self, data: &T) -> Result<Self, serde_json::Error> {
        let bytes = serde_json::to_vec(data)?;
        self.headers
            .insert("Content-Type".to_string(), "application/json".to_string());
        self.body = Some(bytes);
        Ok(self)
    }

    pub fn timeout_ms(mut self, timeout_ms: u64) -> Self {
        self.timeout_ms = Some(timeout_ms);
        self
    }
}

impl From<HttpRequest> for ProtoHttpRequest {
    fn from(req: HttpRequest) -> Self {
        ProtoHttpRequest {
            url: req.url,
            method: req.method,
            headers: req.headers,
            body: req.body,
            timeout_ms: req.timeout_ms,
        }
    }
}

impl From<&HttpRequest> for ProtoHttpRequest {
    fn from(req: &HttpRequest) -> Self {
        ProtoHttpRequest {
            url: req.url.clone(),
            method: req.method.clone(),
            headers: req.headers.clone(),
            body: req.body.clone(),
            timeout_ms: req.timeout_ms,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct HttpResponse {
    pub status_code: u32,
    pub status_text: String,
    pub headers: HashMap<String, String>,
    pub body: Vec<u8>,
    pub error: Option<String>,
}

impl HttpResponse {
    pub fn is_success(&self) -> bool {
        self.status_code >= 200 && self.status_code < 300 && self.error.is_none()
    }

    pub fn text(&self) -> Result<String, std::string::FromUtf8Error> {
        String::from_utf8(self.body.clone())
    }

    pub fn json<T: serde::de::DeserializeOwned>(&self) -> Result<T, serde_json::Error> {
        serde_json::from_slice(&self.body)
    }
}

impl From<ProtoHttpResponse> for HttpResponse {
    fn from(resp: ProtoHttpResponse) -> Self {
        HttpResponse {
            status_code: resp.status_code,
            status_text: resp.status_text,
            headers: resp.headers,
            body: resp.body,
            error: resp.error,
        }
    }
}

/// Executes a single HTTP request on the host runner.
pub fn request(request: &HttpRequest) -> Result<HttpResponse, MoosyncError> {
    let mut responses = batch_request(std::slice::from_ref(request))?;
    let Some(resp) = responses.pop() else {
        return Err(MoosyncError::String(
            "Host runner returned empty response".to_string(),
        ));
    };
    Ok(resp)
}

/// Convenience helper to perform a GET request for a URL.
pub fn get<S: AsRef<str>>(
    url: S,
    headers: Option<&HashMap<String, String>>,
) -> Result<HttpResponse, MoosyncError> {
    let mut req = HttpRequest::get(url.as_ref());
    if let Some(h) = headers {
        req = req.headers(h.clone());
    }
    request(&req)
}

/// Executes multiple HTTP requests concurrently in parallel on the host.
pub fn batch_request(requests: &[HttpRequest]) -> Result<Vec<HttpResponse>, MoosyncError> {
    if requests.is_empty() {
        return Ok(Vec::new());
    }
    let proto_requests: Vec<ProtoHttpRequest> = requests.iter().map(Into::into).collect();
    let batch = BatchHttpRequest {
        requests: proto_requests,
    };
    let res = unsafe { batch_http_request(Prost(batch)) }
        .map_err(|e| MoosyncError::String(format!("batch_http_request failed: {e:?}")))?;
    Ok(res.0.responses.into_iter().map(Into::into).collect())
}

/// Convenience helper to perform parallel GET requests for a list of URLs.
pub fn batch_get<S: AsRef<str>>(
    urls: &[S],
    headers: Option<&HashMap<String, String>>,
) -> Result<Vec<HttpResponse>, MoosyncError> {
    let requests: Vec<HttpRequest> = urls
        .iter()
        .map(|u| {
            let mut req = HttpRequest::get(u.as_ref());
            if let Some(h) = headers {
                req = req.headers(h.clone());
            }
            req
        })
        .collect();
    batch_request(&requests)
}
