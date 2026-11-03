import unittest

from moosync_edk import parse_lrc


class TestParseLrc(unittest.TestCase):
    def test_parse_lrc_empty(self):
        with self.assertRaises(ValueError):
            parse_lrc("")
        with self.assertRaises(ValueError):
            parse_lrc("   \n\t  ")

    def test_parse_lrc_synced(self):
        lrc = "[00:12.50]Line 1\n[00:15.80]Line 2\n[01:02.00]Line 3"
        lyrics = parse_lrc(lrc)
        self.assertTrue(lyrics.is_synced)
        self.assertEqual(len(lyrics.lines), 3)
        self.assertEqual(lyrics.lines[0].text, "Line 1")
        self.assertEqual(lyrics.lines[0].time_ms, 12500)
        self.assertEqual(lyrics.lines[1].text, "Line 2")
        self.assertEqual(lyrics.lines[1].time_ms, 15800)
        self.assertEqual(lyrics.lines[2].text, "Line 3")
        self.assertEqual(lyrics.lines[2].time_ms, 62000)

    def test_parse_lrc_metadata_and_multiple_timestamps(self):
        lrc = "[ti:Song Title]\n[ar:Artist Name]\n[00:01.00][00:05.00]Repeated line"
        lyrics = parse_lrc(lrc)
        self.assertTrue(lyrics.is_synced)
        self.assertEqual(len(lyrics.lines), 2)
        self.assertEqual(lyrics.lines[0].time_ms, 1000)
        self.assertEqual(lyrics.lines[0].text, "Repeated line")
        self.assertEqual(lyrics.lines[1].time_ms, 5000)
        self.assertEqual(lyrics.lines[1].text, "Repeated line")

    def test_parse_lrc_plain(self):
        plain = "First line\nSecond line\nThird line"
        lyrics = parse_lrc(plain)
        self.assertFalse(lyrics.is_synced)
        self.assertEqual(len(lyrics.lines), 3)
        self.assertEqual(lyrics.lines[0].text, "First line")
        self.assertEqual(lyrics.lines[0].time_ms, 0)


if __name__ == "__main__":
    unittest.main()
