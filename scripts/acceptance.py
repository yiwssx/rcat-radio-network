#!/usr/bin/env python3
"""Bounded read-only LAN acceptance probe: API, concurrent listener fetch, soak.

No login, no state mutation, no stream recording. Result is machine-readable
JSON. Application-level and real-audio tests remain independent human gates.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import ipaddress
import json
import statistics
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def validated_origin(origin):
    parts = urlsplit(origin)
    host = parts.hostname
    if parts.scheme != "http" or not host or parts.username or parts.password:
        raise ValueError("Expected http:// on an approved private LAN or internal portal")
    try:
        address = ipaddress.ip_address(host)
        allowed = address.is_loopback or address in ipaddress.ip_network("10.0.0.0/8") or (
            address in ipaddress.ip_network("172.16.0.0/12")) or (
            address in ipaddress.ip_network("192.168.0.0/16"))
    except ValueError:
        allowed = host == "portal"
    if not allowed or parts.path not in ("", "/") or parts.query or parts.fragment:
        raise ValueError("Refusing non-private or non-root target")
    if parts.port not in (None, 80, 8750):
        raise ValueError("Only listener portal ports 80/8750 are allowed")
    return origin.rstrip("/")


def get_nowplaying(origin):
    request = Request(origin + "/api/nowplaying/rcat_radio",
                      headers={"Accept": "application/json"})
    with urlopen(request, timeout=8) as response:
        if response.status != 200:
            raise ValueError("API non-200 response")
        raw = response.read(262145)
    if len(raw) > 262144:
        raise ValueError("API oversized response")
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("station"), dict):
        raise ValueError("Invalid station API schema")
    if payload["station"].get("shortcode") != "rcat_radio":
        raise ValueError("Wrong station")
    return bool(payload.get("is_online"))


def check_stream(origin, mount="radio.mp3"):
    started = time.monotonic()
    try:
        request = Request(origin + "/listen/rcat_radio/" + mount,
                          headers={"User-Agent": "RCAT-Radio-Acceptance/1.0"})
        with urlopen(request, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if response.status != 200 or not (
                    content_type.startswith("audio/") or
                    content_type == "application/ogg"):
                return {"ok": False, "reason": "stream_http_or_mime"}
            payload = response.read(2048)
            if len(payload) < 512:
                return {"ok": False, "reason": "stream_too_short"}
            return {"ok": True, "elapsed_ms": round((time.monotonic()-started)*1000)}
    except (URLError, HTTPError, OSError, TimeoutError, ValueError):
        return {"ok": False, "reason": "stream_unreachable"}


def run_round(origin, clients, mount):
    began = time.monotonic()
    try:
        online = get_nowplaying(origin)
    except (URLError, HTTPError, OSError, TimeoutError, ValueError,
            json.JSONDecodeError):
        online = False
    with ThreadPoolExecutor(max_workers=clients) as pool:
        results = list(pool.map(lambda _: check_stream(origin, mount),
                                range(clients)))
    success = sum(1 for result in results if result["ok"])
    latencies = [result["elapsed_ms"] for result in results if result["ok"]]
    return {
        "station_online": online,
        "clients": clients,
        "passed": success,
        "failed": clients - success,
        "max_fetch_ms": max(latencies) if latencies else None,
        "median_fetch_ms": round(statistics.median(latencies)) if latencies else None,
        "round_duration_ms": round((time.monotonic()-began)*1000),
        "ok": online and success == clients,
    }


def run(origin, clients=5, mount="radio.mp3", duration=0, interval=60):
    started = time.monotonic()
    summary = {
        "station": "rcat_radio", "scope": "LAN_SMOKE_NOT_FULL_ACCEPTANCE",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "configured_clients": clients, "requested_duration_sec": duration,
        "rounds": 0, "passing_rounds": 0, "failed_rounds": 0,
        "max_fetch_ms": None,
    }
    while True:
        outcome = run_round(origin, clients, mount)
        summary["rounds"] += 1
        summary["passing_rounds" if outcome["ok"] else "failed_rounds"] += 1
        if outcome["max_fetch_ms"] is not None:
            summary["max_fetch_ms"] = max(
                summary["max_fetch_ms"] or 0, outcome["max_fetch_ms"])
        if not duration or time.monotonic() - started >= duration:
            break
        time.sleep(min(interval, max(0, duration - (time.monotonic()-started))))
    summary["elapsed_sec"] = round(time.monotonic() - started, 1)
    summary["status"] = "PASS" if summary["failed_rounds"] == 0 else "FAIL"
    summary["limitations"] = [
        "HTTP bytes and MIME only; no audio loudness or human listening",
        "No iOS/Android browser, DJ failover, isolation or backup restore proof",
    ]
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0 if summary["status"] == "PASS" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://portal")
    parser.add_argument("--clients", type=int, choices=(5, 20, 50), default=5)
    parser.add_argument("--mount", choices=("radio.mp3",), default="radio.mp3")
    parser.add_argument("--duration", type=int, default=0)
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()
    if not 0 <= args.duration <= 86400 or not 5 <= args.interval <= 3600:
        parser.error("duration 0..86400 and interval 5..3600 required")
    try:
        origin = validated_origin(args.origin)
    except ValueError as error:
        parser.error(str(error))
    return run(origin, args.clients, args.mount, args.duration, args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
