import re
from core.types.protos import songs_pb2

def parse_lrc(lrc_text: str) -> songs_pb2.Lyrics:
    """Parses standard LRC content into a Lyrics proto."""
    trimmed = lrc_text.strip()
    if not trimmed:
        raise ValueError("Empty LRC text")

    lines = []
    has_timestamps = False

    time_re = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]")

    for raw_line in trimmed.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matches = list(time_re.finditer(line))
        if matches:
            has_timestamps = True
            last_match = matches[-1]
            text = line[last_match.end():].strip()

            for m in matches:
                minutes = int(m.group(1))
                seconds = int(m.group(2))
                frac_str = m.group(3) or "0"
                if len(frac_str) == 1:
                    millis = int(frac_str) * 100
                elif len(frac_str) == 2:
                    millis = int(frac_str) * 10
                elif len(frac_str) == 3:
                    millis = int(frac_str)
                else:
                    millis = int(frac_str[:3])

                time_ms = minutes * 60000 + seconds * 1000 + millis
                lines.append(songs_pb2.LyricLine(text=text, time_ms=time_ms))
        elif not has_timestamps:
            if not line.startswith("[") or not line.endswith("]"):
                lines.append(songs_pb2.LyricLine(text=line, time_ms=0))

    if has_timestamps:
        lines.sort(key=lambda l: l.time_ms)

    return songs_pb2.Lyrics(lines=lines, is_synced=has_timestamps)
