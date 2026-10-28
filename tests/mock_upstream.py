#!/usr/bin/env python3
"""CI-only benign mock. Never deployed to the RCAT host."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/nowplaying/rcat_radio":
            content = json.dumps({
                "station": {"shortcode": "rcat_radio",
                            "listen_url": "/listen/rcat_radio/radio.mp3"},
                "is_online": True, "listeners": {"current": 2},
                "now_playing": {"song": {"title": "RCAT test tone"}},
            }).encode()
            kind = "application/json"
        elif self.path == "/listen/rcat_radio/radio.mp3":
            content = b"FAKE_AUDIO_TEST_BYTES_" * 128
            kind = "audio/mpeg"
        elif self.path in ("/api/nowplaying/other_station", "/admin", "/login"):
            content = b"SHOULD_NEVER_BE_REACHABLE"
            kind = "text/plain"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8700), Handler).serve_forever()
