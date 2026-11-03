package api

import (
	"testing"
)

func TestParseLrcEmpty(t *testing.T) {
	_, err := ParseLrc("")
	if err == nil {
		t.Fatal("expected error for empty LRC, got nil")
	}

	_, err = ParseLrc("   \n\t  ")
	if err == nil {
		t.Fatal("expected error for whitespace LRC, got nil")
	}
}

func TestParseLrcSynced(t *testing.T) {
	lrc := `[00:12.50]Line 1
[00:15.80]Line 2
[01:02.00]Line 3`

	lyrics, err := ParseLrc(lrc)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if !lyrics.GetIsSynced() {
		t.Errorf("expected is_synced to be true")
	}

	if len(lyrics.GetLines()) != 3 {
		t.Fatalf("expected 3 lines, got %d", len(lyrics.GetLines()))
	}

	expected := []struct {
		text string
		time int64
	}{
		{"Line 1", 12500},
		{"Line 2", 15800},
		{"Line 3", 62000},
	}

	for i, exp := range expected {
		line := lyrics.GetLines()[i]
		if line.GetText() != exp.text {
			t.Errorf("line %d: expected text %q, got %q", i, exp.text, line.GetText())
		}
		if line.GetTimeMs() != exp.time {
			t.Errorf("line %d: expected time %d, got %d", i, exp.time, line.GetTimeMs())
		}
	}
}

func TestParseLrcMetadataAndMultipleTimestamps(t *testing.T) {
	lrc := `[ti:Song Title]
[ar:Artist Name]
[al:Album Name]
[00:01.00][00:05.00]Repeated line`

	lyrics, err := ParseLrc(lrc)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if !lyrics.GetIsSynced() {
		t.Errorf("expected is_synced to be true")
	}

	if len(lyrics.GetLines()) != 2 {
		t.Fatalf("expected 2 lines, got %d", len(lyrics.GetLines()))
	}

	if lyrics.GetLines()[0].GetTimeMs() != 1000 || lyrics.GetLines()[0].GetText() != "Repeated line" {
		t.Errorf("unexpected first line: %+v", lyrics.GetLines()[0])
	}
	if lyrics.GetLines()[1].GetTimeMs() != 5000 || lyrics.GetLines()[1].GetText() != "Repeated line" {
		t.Errorf("unexpected second line: %+v", lyrics.GetLines()[1])
	}
}

func TestParseLrcPlain(t *testing.T) {
	plain := `First line
Second line
Third line`

	lyrics, err := ParseLrc(plain)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if lyrics.GetIsSynced() {
		t.Errorf("expected is_synced to be false")
	}

	if len(lyrics.GetLines()) != 3 {
		t.Fatalf("expected 3 lines, got %d", len(lyrics.GetLines()))
	}

	if lyrics.GetLines()[0].GetText() != "First line" || lyrics.GetLines()[0].GetTimeMs() != 0 {
		t.Errorf("unexpected line: %+v", lyrics.GetLines()[0])
	}
}

func TestParseLrcTimestamp(t *testing.T) {
	cases := []struct {
		tag      string
		expected int64
		valid    bool
	}{
		{"00:01.50", 1500, true},
		{"01:30.123", 90123, true},
		{"02:00.5", 120500, true},
		{"00:00.00", 0, true},
		{"invalid", 0, false},
		{"ti:Title", 0, false},
	}

	for _, tc := range cases {
		ms, ok := parseLrcTimestamp(tc.tag)
		if ok != tc.valid {
			t.Errorf("tag %q: expected valid=%v, got %v", tc.tag, tc.valid, ok)
		}
		if tc.valid && ms != tc.expected {
			t.Errorf("tag %q: expected ms=%d, got %d", tc.tag, tc.expected, ms)
		}
	}
}
