"""Focused, isolated public schedule tests. No IOT/RMS network access."""
from datetime import datetime
import calendar
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name("rrn28-public-schedule-rms.py")
spec = importlib.util.spec_from_file_location("rrn28_schedule", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def upstream():
    source = {name: [] for name in mod.WEEKDAYS}
    source["monday"] = [{
        "name": "เพลงไทย &amp; เกษตร", "start_timestamp": "2026-11-16 08:00:00",
        "end_timestamp": "2026-11-16 09:00:00",
        "internal_path": "/var/secret", "url": "http://internal/"
    }]
    return source


NOW = calendar.timegm(datetime(2026, 11, 15, 6, 0, 0).timetuple())


class ScheduleTests(unittest.TestCase):
    def test_whitelist_and_timezone(self):
        result = mod.project(upstream(), now=NOW)
        self.assertEqual(len(result["shows"]), 1)
        self.assertEqual(result["shows"][0], {
            "title": "เพลงไทย & เกษตร",
            "starts_at": "2026-11-16T08:00:00+07:00",
            "ends_at": "2026-11-16T09:00:00+07:00"
        })
        self.assertEqual(result["rcat_public_schedule"]["timezone"], "Asia/Bangkok")
        encoded = json.dumps(result, ensure_ascii=True)
        self.assertNotIn("/var/secret", encoded)
        self.assertNotIn("internal", encoded)
        self.assertNotIn("instance_id", encoded)

    def test_missing_public_api_schema_rejected(self):
        for raw in ({}, {"monday": []}, {"monday": "error"}, None):
            with self.assertRaises(mod.Blocked):
                mod.project(raw, now=NOW)

    def test_old_or_out_of_range_shows_filtered(self):
        data = upstream()
        data["tuesday"] = [{"name": "Old", "starts": "2026-11-03 08:00:00",
                             "ends": "2026-11-03 09:00:00"}]
        data["sunday"] = [{"name": "Invalid", "starts": "2026-11-15 09:00:00",
                            "ends": "2026-11-15 08:00:00"}]
        self.assertEqual(len(mod.project(data, now=NOW)["shows"]), 1)

    def test_empty_week_is_valid_not_fake_programs(self):
        data = {name: [] for name in mod.WEEKDAYS}
        self.assertEqual(mod.project(data, now=NOW)["shows"], [])

    def test_publication_is_atomic_and_does_not_replace_unrelated_document(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "radio-schedule.json"
            with patch.object(mod, "DOCROOT", folder), patch.object(mod, "TARGET", str(destination)):
                mod.publish(mod.project(upstream(), now=NOW))
                self.assertTrue(destination.read_bytes().endswith(b"\n"))
                self.assertEqual(json.loads(destination.read_text())["shows"][0]["title"], "เพลงไทย & เกษตร")
                self.assertFalse(list(Path(folder).glob(".rrn28-*.tmp")))
                destination.write_text('{"other":"owner"}')
                with self.assertRaises(mod.Blocked):
                    mod.publish(mod.project(upstream(), now=NOW))
                self.assertEqual(json.loads(destination.read_text()), {"other": "owner"})


if __name__ == "__main__":
    unittest.main()
