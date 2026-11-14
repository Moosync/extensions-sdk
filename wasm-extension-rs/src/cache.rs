use crate::api::MoosyncResult;
use crate::handler::MoosyncError;
use extensions_proto::moosync::types::{GetCacheRequest, SetCacheRequest};

pub fn get_cache<T: prost::Message + Default>(key: &str) -> MoosyncResult<Option<T>> {
    let req = GetCacheRequest {
        key: key.to_string(),
    };
    let resp = crate::api::host_get_cache(req)?;
    if let Some(data) = resp.data {
        if !data.is_empty() {
            let msg = T::decode(data.as_slice())
                .map_err(|e| MoosyncError::String(e.to_string()))?;
            return Ok(Some(msg));
        }
    }
    Ok(None)
}

pub fn set_cache<T: prost::Message>(key: &str, data: &T) -> MoosyncResult<()> {
    set_cache_with_ttl(key, data, None)
}

pub fn set_cache_with_ttl<T: prost::Message>(
    key: &str,
    data: &T,
    ttl_seconds: Option<u64>,
) -> MoosyncResult<()> {
    let req = SetCacheRequest {
        key: key.to_string(),
        data: data.encode_to_vec(),
        ttl_seconds,
    };
    let resp = crate::api::host_set_cache(req)?;
    if resp.success {
        Ok(())
    } else {
        Err(MoosyncError::String("Failed to set cache".to_string()))
    }
}
