import { LyricLine, Lyrics } from "./protos/songs_pb.js";

/**
 * Parses LRC-formatted lyric text into a structured {@link Lyrics} protobuf message.
 */
export function parseLrc(lrcText: string): Lyrics {
  const trimmed = lrcText.trim();
  if (!trimmed) {
    throw new Error("Empty LRC text");
  }

  const lines: LyricLine[] = [];
  let hasTimestamps = false;

  for (const rawLine of trimmed.split("\n")) {
    const line = rawLine.trim();
    if (!line) continue;

    let remaining = line;
    const timestamps: bigint[] = [];

    while (remaining.startsWith("[")) {
      const closeIdx = remaining.indexOf("]");
      if (closeIdx === -1) break;
      const tag = remaining.slice(1, closeIdx);
      const ms = parseLrcTimestamp(tag);
      if (ms !== null) {
        timestamps.push(ms);
        remaining = remaining.slice(closeIdx + 1);
      } else if (tag.includes(":") && !/^\d/.test(tag)) {
        remaining = remaining.slice(closeIdx + 1);
      } else {
        break;
      }
    }

    const text = remaining.trim();
    if (timestamps.length > 0) {
      hasTimestamps = true;
      for (const timeMs of timestamps) {
        lines.push(new LyricLine({ text, timeMs }));
      }
    } else if (!hasTimestamps && text.length > 0) {
      lines.push(new LyricLine({ text, timeMs: 0n }));
    }
  }

  if (hasTimestamps) {
    lines.sort((a, b) => Number(a.timeMs - b.timeMs));
  }

  return new Lyrics({
    lines,
    isSynced: hasTimestamps,
  });
}

export function parseLrcTimestamp(tag: string): bigint | null {
  const parts = tag.split(":");
  if (parts.length !== 2) return null;
  const min = parseInt(parts[0], 10);
  if (isNaN(min)) return null;

  const secParts = parts[1].split(".");
  const sec = parseInt(secParts[0], 10);
  if (isNaN(sec)) return null;

  let millis = 0;
  if (secParts.length > 1) {
    const frac = secParts[1];
    const val = parseInt(frac, 10);
    if (!isNaN(val)) {
      if (frac.length === 1) millis = val * 100;
      else if (frac.length === 2) millis = val * 10;
      else if (frac.length === 3) millis = val;
      else millis = parseInt(frac.slice(0, 3), 10);
    }
  }

  return BigInt(min * 60000 + sec * 1000 + millis);
}
