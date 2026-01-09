use extensions_proto::moosync::types::PlayerState;
use extensions_proto::moosync::types::*;
use extensions_proto::struct_proto::google::protobuf::Struct as ProtoStruct;
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

impl Extract<Option<ProtoStruct>> for GetEntityResponse {
    fn extract(self) -> Option<ProtoStruct> {
        self.entity
    }
}

impl Extract<Option<ProtoStruct>> for GetQueueResponse {
    fn extract(self) -> Option<ProtoStruct> {
        self.queue
    }
}
