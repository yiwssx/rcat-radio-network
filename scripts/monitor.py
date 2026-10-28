#!/usr/bin/env python3
"""Read-only broadcast availability and decoded-audio silence monitor.

Runs inside an optional isolated container; no Docker socket or admin token.
Emits structured JSON to stdout; optional owner-configured HTTPS alert webhook.
A healthy HTTP response alone is *not* considered healthy audio.
"""
import argparse
from array import array
from datetime import datetime, timezone
import json
import math
import os
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


API_URL = "http://portal/api/nowplaying/rcat_radio"
STREAM_URL = "http://portal/listen/rcat_radio/radio.mp3"
STATION = "rcat_radio"


def event(kind, **fields):
    record = {"ts": datetime.now(timezone.utc).isoformat(), "event": kind, **fields}
    print(json.dumps(record, ensure_ascii=False, separators=(",", ":")), flush=True)


def read_station(url=API_URL, opener=urlopen):
    # Fixed read-only URL: never call an administrative or arbitrary API.
    with opener(Request(url, headers={"Accept": "application/json"}), timeout=8) as response:
        if response.status != 200:
            raise ValueError("nowplaying_http_failure")
        raw = response.read(262145)
    if len(raw) > 262144:
        raise ValueError("nowplaying_response_too_large")
    obj = json.loads(raw)
    if not isinstance(obj, dict) or not isinstance(obj.get("station"), dict):
        raise ValueError("invalid_nowplaying_schema")
    if obj["station"].get("shortcode") != STATION:
        raise ValueError("unexpected_station")
    if not obj.get("is_online"):
        raise ValueError("station_offline")
    return obj


def decoded_level_dbfs(pcm):
    """16-bit signed little-endian mono PCM RMS, independent of MP3 headers."""
    if not pcm or len(pcm) % 2:
        raise ValueError("invalid_audio_samples")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    if len(samples) < 8000:
        raise ValueError("too_few_decoded_samples")
    rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    return -120.0 if rms == 0 else 20.0 * math.log10(rms / 32768.0)


def decode_stream(url=STREAM_URL, runner=subprocess.run):
    cmd = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-rw_timeout", "5000000", "-i", url,
        "-t", "5", "-vn", "-ar", "8000", "-ac", "1",
        "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1",
    ]
    try:
        proc = runner(cmd, capture_output=True, timeout=18, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("stream_decode_failed") from error
    if proc.returncode != 0:
        raise ValueError("stream_decode_failed")
    return decoded_level_dbfs(proc.stdout)


def sample(threshold=-50.0):
    try:
        station = read_station()
        level = decode_stream()
        if level < threshold:
            return {"healthy": False, "reason": "decoded_audio_silent",
                    "level_dbfs": round(level, 1)}
        return {"healthy": True, "reason": "playing",
                "level_dbfs": round(level, 1),
                "live_dj": bool((station.get("live") or {}).get("is_live"))}
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
        detail = str(error)
        allowed = {
            "nowplaying_http_failure", "nowplaying_response_too_large",
            "invalid_nowplaying_schema", "unexpected_station", "station_offline",
            "stream_decode_failed", "invalid_audio_samples",
            "too_few_decoded_samples",
        }
        return {"healthy": False, "reason": detail if detail in allowed else "endpoint_unavailable"}


def send_webhook(url, kind, result):
    if not url:
        return
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        event("webhook_rejected", reason="requires_https_url")
        return
    payload = json.dumps({"station": STATION, "event": kind,
                          "reason": result["reason"],
                          "time": datetime.now(timezone.utc).isoformat()}).encode()
    request = Request(url, data=payload, headers={"Content-Type": "application/json"},
                      method="POST")
    try:
        with urlopen(request, timeout=8) as response:
            if not 200 <= response.status < 300:
                event("webhook_failure", reason="non_2xx_response")
    except (HTTPError, URLError, OSError, TimeoutError):
        event("webhook_failure", reason="delivery_error")


def run(once=False, interval=30, failures=3, recoveries=2, threshold=-50.0,
        webhook=""):
    consecutive_failures = 0
    consecutive_recoveries = 0
    alerting = False
    while True:
        result = sample(threshold)
        event("sample", **result)
        if result["healthy"]:
            consecutive_failures = 0
            consecutive_recoveries += 1
            if alerting and consecutive_recoveries >= recoveries:
                event("recovered", reason="decoded_audio_restored")
                send_webhook(webhook, "recovered", result)
                alerting = False
        else:
            consecutive_recoveries = 0
            consecutive_failures += 1
            if not alerting and consecutive_failures >= failures:
                event("alert", **result)
                send_webhook(webhook, "alert", result)
                alerting = True
        if once:
            return 0 if result["healthy"] else 2
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--failures", type=int, default=3)
    parser.add_argument("--recoveries", type=int, default=2)
    parser.add_argument("--silence-dbfs", type=float, default=-50.0)
    args = parser.parse_args()
    if not 5 <= args.interval <= 3600 or not 1 <= args.failures <= 20:
        parser.error("interval must be 5-3600 seconds and failures 1-20")
    if not 1 <= args.recoveries <= 20 or not -100 <= args.silence_dbfs <= -5:
        parser.error("recoveries must be 1-20 and silence threshold -100..-5")
    return run(args.once, args.interval, args.failures, args.recoveries,
               args.silence_dbfs, os.environ.get("RRN_ALERT_WEBHOOK_URL", ""))


if __name__ == "__main__":
    raise SystemExit(main())
