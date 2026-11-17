#!/usr/bin/env python3
import os
import tempfile
import unittest
from tools.sdk_generator.generator import (
    build_descriptor_pool,
    extract_metadata,
    render_template,
)


class GeneratorTest(unittest.TestCase):
    def test_metadata_extraction(self):
        desc_files = []
        runfiles_dir = os.environ.get("TEST_SRCDIR", ".")
        for root, _, files in os.walk(runfiles_dir):
            for f in files:
                if f.endswith("-descriptor-set.proto.bin") or f.endswith(".proto.bin"):
                    desc_files.append(os.path.join(root, f))

        self.assertTrue(len(desc_files) > 0, "Descriptor sets should be present")
        pool = build_descriptor_pool(desc_files)
        metadata = extract_metadata(pool)

        host_methods = metadata["host_methods"]
        guest_methods = metadata["guest_methods"]

        self.assertGreaterEqual(len(host_methods), 20)
        self.assertGreaterEqual(len(guest_methods), 20)

        sys_time = next((m for m in host_methods if m["name"] == "SystemTime"), None)
        self.assertIsNotNone(sys_time)
        self.assertEqual(sys_time["oneof_variant"], "system_time")
        self.assertFalse(sys_time["has_wrapper"])

        open_fd = next((m for m in host_methods if m["name"] == "OpenClientFd"), None)
        self.assertIsNotNone(open_fd)
        self.assertEqual(open_fd["oneof_variant"], "open_client_fd")
        self.assertTrue(open_fd["has_wrapper"])

        get_song = next((m for m in host_methods if m["name"] == "GetSong"), None)
        self.assertIsNotNone(get_song)
        self.assertEqual(get_song["oneof_variant"], "get_song")

        queue_changed = next((m for m in guest_methods if m["name"] == "SongQueueChanged"), None)
        self.assertIsNotNone(queue_changed)
        self.assertTrue(queue_changed["is_event"])

        req_playlists = next((m for m in guest_methods if m["name"] == "RequestedPlaylists"), None)
        self.assertIsNotNone(req_playlists)
        self.assertFalse(req_playlists["is_event"])

        templates_base = "tools/sdk_generator/templates"
        with tempfile.TemporaryDirectory() as tmp_dir:
            for lang in ["rust", "ts", "go", "py"]:
                lang_dir = os.path.join(templates_base, lang)
                out_api = os.path.join(tmp_dir, f"{lang}_api.txt")
                out_disp = os.path.join(tmp_dir, f"{lang}_disp.txt")
                render_template(lang_dir, "api.jinja", metadata, out_api)
                render_template(lang_dir, "dispatcher.jinja", metadata, out_disp)
                self.assertTrue(os.path.exists(out_api))
                self.assertTrue(os.path.exists(out_disp))
                self.assertGreater(os.path.getsize(out_api), 100)
                self.assertGreater(os.path.getsize(out_disp), 100)

            moounit_dir = os.path.join(templates_base, "moounit")
            out_moounit = os.path.join(tmp_dir, "moounit_generated.py")
            render_template(moounit_dir, "client.jinja", metadata, out_moounit)
            self.assertTrue(os.path.exists(out_moounit))
            self.assertGreater(os.path.getsize(out_moounit), 100)
            with open(out_moounit, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("class GeneratedMoounitGuestClient(GeneratedMoounitExpectationClient):", content)
            self.assertIn("class GeneratedMoounitExpectationClient:", content)
            self.assertIn("MAIN_COMMAND_DEFAULT_RESPONSES", content)
            self.assertIn("def expect_spawn_process(", content)
            self.assertIn("def expect_open_client_fd(", content)
            self.assertIn("def expect_system_time(", content)
            self.assertIn("def expect_batch_http_request(", content)
            self.assertIn("def requested_cover_art(", content)
            self.assertIn("def can_play(", content)
            self.assertIn("def player_play(", content)

            self.assertTrue(get_song.get("doc"), "Docstring should be extracted for GetSong")
            with open(os.path.join(tmp_dir, "rust_api.txt"), "r", encoding="utf-8") as f:
                rust_content = f.read()
                self.assertIn("/// Queries and retrieves song entities matching the given criteria from the host database.", rust_content)
            with open(os.path.join(tmp_dir, "ts_api.txt"), "r", encoding="utf-8") as f:
                ts_content = f.read()
                self.assertIn("/**", ts_content)
                self.assertIn("Queries and retrieves song entities matching the given criteria from the host database.", ts_content)


if __name__ == "__main__":
    unittest.main()
