"""Offline monitor regression checks; no stream or Docker host required."""
import io
import json
import math
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import monitor


class MockReply:
    status = 200
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, size):
        return self.payload[:size]


class MonitorTests(unittest.TestCase):
    def test_reject_other_station(self):
        with self.assertRaisesRegex(ValueError, "unexpected_station"):
            monitor.read_station(opener=lambda *_args, **_kw: MockReply(
                {"station": {"shortcode": "other"}, "is_online": True}
            ))

    def test_online_station(self):
        station = monitor.read_station(opener=lambda *_args, **_kw: MockReply(
            {"station": {"shortcode": "rcat_radio"}, "is_online": True}
        ))
        self.assertTrue(station["is_online"])

    def test_pcm_rms_detects_silence_and_audible_tone(self):
        silent = b"\\x00\\x00" * 8000
        self.assertEqual(monitor.decoded_level_dbfs(silent), -120)
        wave = b"".join(struct.pack("<h", round(4000 * math.sin(i / 15)))
                        for i in range(8000))
        self.assertGreater(monitor.decoded_level_dbfs(wave), -30)

    def test_pcm_malformed(self):
        for content in [b"", b"\\x00", b"\\x00\\x00" * 20]:
            with self.assertRaises(ValueError):
                monitor.decoded_level_dbfs(content)

    def test_decoding_failure_is_closed(self):
        class Result:
            returncode = 1
            stdout = b""
        with self.assertRaisesRegex(ValueError, "stream_decode_failed"):
            monitor.decode_stream(runner=lambda *_a, **_k: Result())

    def test_once_returns_nonzero_if_no_audio(self):
        with patch.object(monitor, "sample", return_value={
            "healthy": False, "reason": "station_offline"
        }), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(monitor.run(once=True), 2)

    def test_webhook_requires_https(self):
        with patch.object(monitor, "urlopen") as opening, patch("sys.stdout", new_callable=io.StringIO):
            monitor.send_webhook("http://example.test/hooks", "alert",
                                 {"reason": "station_offline"})
            opening.assert_not_called()

    def test_alert_does_not_send_credentials(self):
        # The structured event must contain only the station and reason.
        with patch.object(monitor, "urlopen") as opening:
            opening.return_value.__enter__.return_value.status = 200
            monitor.send_webhook("https://example.test/hooks", "alert",
                                 {"reason": "station_offline", "token": "secret"})
            message = json.loads(opening.call_args[0][0].data)
            self.assertNotIn("token", message)
            self.assertEqual(message["station"], "rcat_radio")


if __name__ == "__main__":
    unittest.main()
