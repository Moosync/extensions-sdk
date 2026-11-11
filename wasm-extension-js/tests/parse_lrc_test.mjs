import assert from "node:assert";
import test from "node:test";
import { parseLrc, parseLrcTimestamp } from "../lib/src/lrc.js";

test("parseLrc empty input returns error", () => {
    assert.throws(() => parseLrc(""), /Empty LRC text/);
    assert.throws(() => parseLrc("   \n\t  "), /Empty LRC text/);
});

test("parseLrc synced lyrics", () => {
    const lrc = "[00:12.50]Line 1\n[00:15.80]Line 2\n[01:02.00]Line 3";
    const res = parseLrc(lrc);
    assert.strictEqual(res.isSynced, true);
    assert.strictEqual(res.lines.length, 3);
    assert.strictEqual(res.lines[0].text, "Line 1");
    assert.strictEqual(res.lines[0].timeMs, 12500n);
    assert.strictEqual(res.lines[1].text, "Line 2");
    assert.strictEqual(res.lines[1].timeMs, 15800n);
    assert.strictEqual(res.lines[2].text, "Line 3");
    assert.strictEqual(res.lines[2].timeMs, 62000n);
});

test("parseLrc metadata and multiple timestamps", () => {
    const lrc = "[ti:Song Title]\n[ar:Artist Name]\n[00:01.00][00:05.00]Repeated line";
    const res = parseLrc(lrc);
    assert.strictEqual(res.isSynced, true);
    assert.strictEqual(res.lines.length, 2);
    assert.strictEqual(res.lines[0].timeMs, 1000n);
    assert.strictEqual(res.lines[0].text, "Repeated line");
    assert.strictEqual(res.lines[1].timeMs, 5000n);
    assert.strictEqual(res.lines[1].text, "Repeated line");
});

test("parseLrc plain lyrics", () => {
    const plain = "First line\nSecond line\nThird line";
    const res = parseLrc(plain);
    assert.strictEqual(res.isSynced, false);
    assert.strictEqual(res.lines.length, 3);
    assert.strictEqual(res.lines[0].text, "First line");
    assert.strictEqual(res.lines[0].timeMs, 0n);
});

test("parseLrcTimestamp valid and invalid", () => {
    assert.strictEqual(parseLrcTimestamp("00:01.50"), 1500n);
    assert.strictEqual(parseLrcTimestamp("01:30.123"), 90123n);
    assert.strictEqual(parseLrcTimestamp("02:00.5"), 120500n);
    assert.strictEqual(parseLrcTimestamp("00:00.00"), 0n);
    assert.strictEqual(parseLrcTimestamp("invalid"), null);
    assert.strictEqual(parseLrcTimestamp("ti:Title"), null);
});
