from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import acceptance


class AcceptanceUnitTests(unittest.TestCase):
    def test_private_target_allowed(self):
        self.assertEqual(acceptance.validated_origin("http://192.168.1.5:8750/"),
                         "http://192.168.1.5:8750")
        self.assertEqual(acceptance.validated_origin("http://portal"),
                         "http://portal")

    def test_block_public_and_admin_targets(self):
        for origin in ["https://example.org", "http://8.8.8.8:8750",
                       "http://127.0.0.1:8700", "http://example.com",
                       "http://portal/admin", "http://portal@evil.test/"]:
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                acceptance.validated_origin(origin)

    def test_round_failure_is_reported(self):
        with patch.object(acceptance, "get_nowplaying", return_value=True), patch.object(
            acceptance, "check_stream", return_value={"ok": False,
                                                       "reason": "stream_unreachable"}
        ):
            result = acceptance.run_round("http://portal", 5, "radio.mp3")
        self.assertEqual(result["failed"], 5)
        self.assertFalse(result["ok"])

    def test_all_five_streams_pass(self):
        with patch.object(acceptance, "get_nowplaying", return_value=True), patch.object(
            acceptance, "check_stream", return_value={"ok": True, "elapsed_ms": 25}
        ):
            result = acceptance.run_round("http://portal", 5, "radio.mp3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["median_fetch_ms"], 25)


if __name__ == "__main__":
    unittest.main()
