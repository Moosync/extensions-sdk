use extensions_proto::moosync::types::PlayerState;
use extensions_proto::moosync::types::*;
use serde_json::{Map, Value};
use songs_proto::moosync::types::Song;

pub trait Extract<T> {
    fn extract(self) -> T;
}

impl Extract<Vec<Song>> for GetSongResponse {
    fn extract(self) -> Vec<Song> {
        self.songs
    }
}

impl Extract<Option<Song>> for GetCurrentSongResponse {
    fn extract(self) -> Option<Song> {
        self.song
    }
}

impl Extract<PlayerState> for GetPlayerStateResponse {
    fn extract(self) -> PlayerState {
        self.state()
    }
}

impl Extract<f64> for GetVolumeResponse {
    fn extract(self) -> f64 {
        self.volume
    }
}

impl Extract<f64> for GetTimeResponse {
    fn extract(self) -> f64 {
        self.time
    }
}

impl Extract<PreferenceData> for GetPreferenceResponse {
    fn extract(self) -> PreferenceData {
        self.data.unwrap_or_default()
    }
}

impl Extract<PreferenceData> for GetSecureResponse {
    fn extract(self) -> PreferenceData {
        self.data.unwrap_or_default()
    }
}

impl Extract<String> for AddPlaylistResponse {
    fn extract(self) -> String {
        self.playlist_id
    }
}

// Struct to Value conversion

// fn proto_value_to_serde(v: ProtoValue) -> Value {
//     match v.kind {
//         Some(Kind::NullValue(_)) => Value::Null,
//         Some(Kind::NumberValue(n)) => {
//             Value::Number(serde_json::Number::from_f64(n).unwrap_or(serde_json::Number::from(0)))
//         } // Handle NaN?
//         Some(Kind::StringValue(s)) => Value::String(s),
//         Some(Kind::BoolValue(b)) => Value::Bool(b),
//         Some(Kind::StructValue(s)) => Value::Object(proto_struct_to_serde(s)),
//         Some(Kind::ListValue(l)) => {
//             Value::Array(l.values.into_iter().map(proto_value_to_serde).collect())
//         }
//         None => Value::Null,
//     }
// }

// fn proto_struct_to_serde(s: Struct) -> Map<String, Value> {
//     let mut map = Map::new();
//     for (k, v) in s.fields {
//         map.insert(k, proto_value_to_serde(v));
//     }
//     map
// }

pub fn google_struct_to_serde(
    s: extensions_proto::struct_proto::google::protobuf::Struct,
) -> Value {
    // Need to convert extensions_proto Struct to prost_types Struct or handle manually.
    // Since generated code is generated, the types might be identical in structure but distinct in type system.
    // I essentially need to map fields.
    // extensions_proto::struct_proto::google::protobuf::Struct has fields: generic map.
    // It's easier to just map it here.

    let mut map = Map::new();
    for (k, v) in s.fields {
        map.insert(k, google_value_to_serde(v));
    }
    Value::Object(map)
}

pub fn google_value_to_serde(v: extensions_proto::struct_proto::google::protobuf::Value) -> Value {
    use extensions_proto::struct_proto::google::protobuf::value::Kind;
    match v.kind {
        Some(Kind::NullValue(_)) => Value::Null,
        Some(Kind::NumberValue(n)) => {
            Value::Number(serde_json::Number::from_f64(n).unwrap_or(serde_json::Number::from(0)))
        }
        Some(Kind::StringValue(s)) => Value::String(s),
        Some(Kind::BoolValue(b)) => Value::Bool(b),
        Some(Kind::StructValue(s)) => google_struct_to_serde(s),
        Some(Kind::ListValue(l)) => {
            Value::Array(l.values.into_iter().map(google_value_to_serde).collect())
        }
        None => Value::Null,
    }
}

impl Extract<Value> for GetEntityResponse {
    fn extract(self) -> Value {
        if let Some(s) = self.entity {
            google_struct_to_serde(s)
        } else {
            Value::Null
        }
    }
}

impl Extract<Value> for GetQueueResponse {
    fn extract(self) -> Value {
        if let Some(s) = self.queue {
            google_struct_to_serde(s)
        } else {
            Value::Null
        }
    }
}
