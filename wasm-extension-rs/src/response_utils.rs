use extensions_proto::moosync::types::PlayerState;
use extensions_proto::moosync::types::*;
use songs_proto::moosync::types::{Album, Artist, Genre, LyricLine, Lyrics, Playlist, Song};

/// Converts a standard Rust `Duration` into a protobuf `Duration`.
pub fn duration_to_proto(d: std::time::Duration) -> duration_proto::google::protobuf::Duration {
    duration_proto::google::protobuf::Duration {
        seconds: d.as_secs() as i64,
        nanos: d.subsec_nanos() as i32,
    }
}

/// Converts a protobuf `Duration` into a standard Rust `Duration`.
pub fn proto_to_duration(d: &duration_proto::google::protobuf::Duration) -> std::time::Duration {
    let secs = if d.seconds >= 0 { d.seconds as u64 } else { 0 };
    let nanos = if d.nanos >= 0 { d.nanos as u32 } else { 0 };
    std::time::Duration::new(secs, nanos)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LrcParseError {
    Empty,
}

impl std::fmt::Display for LrcParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LrcParseError::Empty => write!(f, "LRC content is empty"),
        }
    }
}

impl std::error::Error for LrcParseError {}

/// Parses standard LRC content or plain lyrics into a `Lyrics` proto.
/// Returns `Ok(Lyrics)` or `Err(LrcParseError::Empty)` if input contains no text.
#[tracing::instrument(level = "debug", skip_all)]
pub fn parse_lrc(lrc_text: &str) -> Result<Lyrics, LrcParseError> {
    let trimmed = lrc_text.trim();
    if trimmed.is_empty() {
        return Err(LrcParseError::Empty);
    }

    let mut lines = Vec::new();
    let mut has_timestamps = false;

    for line in trimmed.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }

        let mut remaining = line;
        let mut timestamps = Vec::new();

        while remaining.starts_with('[') {
            if let Some(close_idx) = remaining.find(']') {
                let tag = &remaining[1..close_idx];
                if let Some(ms) = parse_lrc_timestamp(tag) {
                    timestamps.push(ms);
                    remaining = &remaining[close_idx + 1..];
                } else if tag.contains(':') && !tag.chars().next().is_some_and(|c| c.is_ascii_digit()) {
                    remaining = &remaining[close_idx + 1..];
                } else {
                    break;
                }
            } else {
                break;
            }
        }

        let text = strip_inline_lrc_tags(remaining);
        if !timestamps.is_empty() {
            has_timestamps = true;
            for time_ms in timestamps {
                lines.push(LyricLine {
                    text: text.clone(),
                    time_ms,
                });
            }
        } else if !has_timestamps && !text.is_empty() {
            lines.push(LyricLine {
                text,
                time_ms: 0,
            });
        }
    }

    if has_timestamps {
        lines.sort_by_key(|l| l.time_ms);
    }

    Ok(Lyrics {
        lines,
        is_synced: has_timestamps,
    })
}

fn strip_inline_lrc_tags(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let mut rest = input.trim();
    while let Some(open_idx) = rest.find('<') {
        if let Some(rel_close) = rest[open_idx + 1..].find('>') {
            let tag = &rest[open_idx + 1..open_idx + 1 + rel_close];
            if parse_lrc_timestamp(tag).is_some() {
                out.push_str(&rest[..open_idx]);
                rest = &rest[open_idx + 1 + rel_close + 1..];
                continue;
            }
        }
        out.push_str(&rest[..open_idx + 1]);
        rest = &rest[open_idx + 1..];
    }
    out.push_str(rest);
    out.split_whitespace().collect::<Vec<_>>().join(" ")
}

fn parse_lrc_timestamp(tag: &str) -> Option<i64> {
    let parts: Vec<&str> = tag.split(':').collect();
    if parts.len() != 2 {
        return None;
    }

    let minutes: i64 = parts[0].parse().ok()?;
    let sec_parts: Vec<&str> = parts[1].split('.').collect();
    let seconds: i64 = sec_parts[0].parse().ok()?;

    let millis: i64 = if sec_parts.len() > 1 {
        let frac = sec_parts[1];
        match frac.len() {
            1 => frac.parse::<i64>().ok()? * 100,
            2 => frac.parse::<i64>().ok()? * 10,
            3 => frac.parse::<i64>().ok()?,
            _ => frac[..3].parse::<i64>().ok()?,
        }
    } else {
        0
    };

    Some(minutes * 60_000 + seconds * 1_000 + millis)
}

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

impl Extract<Vec<Album>> for GetAlbumsResponse {
    fn extract(self) -> Vec<Album> {
        self.albums
    }
}

impl Extract<Vec<Artist>> for GetArtistsResponse {
    fn extract(self) -> Vec<Artist> {
        self.artists
    }
}

impl Extract<Vec<Genre>> for GetGenresResponse {
    fn extract(self) -> Vec<Genre> {
        self.genres
    }
}

impl Extract<Vec<Playlist>> for GetPlaylistsResponse {
    fn extract(self) -> Vec<Playlist> {
        self.playlists
    }
}

impl Extract<Option<QueueState>> for GetQueueResponse {
    fn extract(self) -> Option<QueueState> {
        self.queue
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_lrc_empty() {
        assert!(parse_lrc("").is_err());
        assert!(parse_lrc("   \n\t  ").is_err());
    }

    #[test]
    fn test_parse_lrc_synced() {
        let lrc = "[00:12.50]Line 1\n[00:15.80]Line 2\n[01:02.00]Line 3";
        let lyrics = parse_lrc(lrc).unwrap();
        assert!(lyrics.is_synced);
        assert_eq!(lyrics.lines.len(), 3);
        assert_eq!(lyrics.lines[0].text, "Line 1");
        assert_eq!(lyrics.lines[0].time_ms, 12500);
        assert_eq!(lyrics.lines[1].text, "Line 2");
        assert_eq!(lyrics.lines[1].time_ms, 15800);
        assert_eq!(lyrics.lines[2].text, "Line 3");
        assert_eq!(lyrics.lines[2].time_ms, 62000);
    }

    #[test]
    fn test_parse_lrc_metadata_and_multiple_timestamps() {
        let lrc = "[ti:Song Title]\n[ar:Artist Name]\n[00:01.00][00:05.00]Repeated line";
        let lyrics = parse_lrc(lrc).unwrap();
        assert!(lyrics.is_synced);
        assert_eq!(lyrics.lines.len(), 2);
        assert_eq!(lyrics.lines[0].time_ms, 1000);
        assert_eq!(lyrics.lines[0].text, "Repeated line");
        assert_eq!(lyrics.lines[1].time_ms, 5000);
        assert_eq!(lyrics.lines[1].text, "Repeated line");
    }

    #[test]
    fn test_parse_lrc_plain() {
        let plain = "First line\nSecond line\nThird line";
        let lyrics = parse_lrc(plain).unwrap();
        assert!(!lyrics.is_synced);
        assert_eq!(lyrics.lines.len(), 3);
        assert_eq!(lyrics.lines[0].text, "First line");
        assert_eq!(lyrics.lines[0].time_ms, 0);
    }

    #[test]
    fn test_parse_lrc_timestamp() {
        assert_eq!(parse_lrc_timestamp("00:01.50"), Some(1500));
        assert_eq!(parse_lrc_timestamp("01:30.123"), Some(90123));
        assert_eq!(parse_lrc_timestamp("02:00.5"), Some(120500));
        assert_eq!(parse_lrc_timestamp("00:00.00"), Some(0));
        assert_eq!(parse_lrc_timestamp("invalid"), None);
        assert_eq!(parse_lrc_timestamp("ti:Title"), None);
    }
}
