#!/usr/bin/env python3
"""RRN-27: publish a minimal, expiring same-origin JSON snapshot on existing RMS.

Run once per minute from the existing RMS host's cron *only after* the upstream
LibreTime endpoint has been repaired. Does not change Apache, Docker or audio.
"""
import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

UPSTREAM = "http://10.10.1.100:8700/api/live-info-v2/"  # Existing private IOT LAN route.
DOCROOT = Path("/var/www/radio-listener")              # Existing RMS radio-only webroot.
TARGET = DOCROOT / "radio-metadata.json"
MAX_RESPONSE = 262144
MAX_AGE_SECONDS = 180


class Blocked(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("upstream redirected instead of returning public metadata")


def get_json():
    # No environment-proxy forwarding, no cookies, no API key and no redirects.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    req = Request(UPSTREAM, headers={"Accept": "application/json"})
    with opener.open(req, timeout=7) as response:
        if response.status != 200:
            raise Blocked("upstream HTTP is not 200")
        content_type = response.headers.get("Content-Type", "").lower()
        if content_type.split(";", 1)[0].strip() != "application/json":
            raise Blocked("upstream does not return application/json")
        data = response.read(MAX_RESPONSE + 1)
    if len(data) > MAX_RESPONSE:
        raise Blocked("upstream JSON exceeds the bounded size")
    try:
        return json.loads(data.decode("utf-8"))  # Reject trailing HTML / 500 pages.
    except (UnicodeError, ValueError) as exc:
        raise Blocked("upstream response is not exactly one valid UTF-8 JSON value") from exc


def nonempty(value):
    if not isinstance(value, str):
        return None
    # Bound output and remove control codes. Content is rendered as text, never HTML.
    cleaned = "".join(ch for ch in value if ord(ch) >= 32 and ord(ch) != 127).strip()
    return cleaned[:240] or None


def project(payload, now=None):
    if not isinstance(payload, dict) or not isinstance(payload.get("tracks"), dict):
        raise Blocked("unrecognized LibreTime tracks schema")
    raw = payload["tracks"]
    result = {}
    for slot in ("previous", "current", "next"):
        value = raw.get(slot)
        if not isinstance(value, dict):
            result[slot] = None
            continue
        meta = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
        kind = nonempty(value.get("type"))
        kind = kind if kind in ("track", "webstream", "livestream") else "unknown"
        title = nonempty(meta.get("track_title")) or nonempty(meta.get("title")) or nonempty(value.get("name"))
        if not title:
            result[slot] = None
            continue
        item = {"type": kind, "metadata": {"track_title": title}}
        artist = nonempty(meta.get("artist_name")) or nonempty(meta.get("artist"))
        if kind == "track" and artist:
            item["metadata"]["artist_name"] = artist
        result[slot] = item
    now = int(time.time() if now is None else now)
    return {
        "rcat_public_feed": {"schema": 1, "generated_at": now,
                             "expires_at": now + MAX_AGE_SECONDS},
        "tracks": result,
    }


def publish(data):
    if not DOCROOT.is_dir() or DOCROOT.is_symlink():
        raise Blocked("existing RMS radio webroot missing or unsafe")
    if TARGET.is_symlink():
        raise Blocked("existing metadata target is a symlink")
    if TARGET.exists():
        if not stat.S_ISREG(TARGET.stat().st_mode):
            raise Blocked("existing metadata target is not a regular file")
        # Never replace an unrelated owner's pre-existing document.
        try:
            existing = json.loads(TARGET.read_text(encoding="ascii"))
            if existing.get("rcat_public_feed", {}).get("schema") != 1:
                raise Blocked("target exists and was not created by RRN-27")
        except (ValueError, UnicodeError, AttributeError):
            raise Blocked("target exists but is not RRN-27 metadata") from None
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=str(DOCROOT),
                                         prefix=".rrn27-", suffix=".tmp",
                                         encoding="ascii", delete=False) as f:
            tmp = f.name
            # ASCII-escaped Thai avoids the legacy Apache default charset issue.
            json.dump(data, f, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, str(TARGET))
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser(description="RRN-27 read-only sanitized metadata exporter")
    flags = parser.add_mutually_exclusive_group(required=True)
    flags.add_argument("--probe", action="store_true", help="check upstream safely; no write")
    flags.add_argument("--apply", action="store_true", help="publish sanitized snapshot to RMS")
    args = parser.parse_args()
    metadata = project(get_json())
    if args.apply:
        if os.geteuid() != 0:
            raise Blocked("--apply requires RMS operator root; no privilege escalation")
        publish(metadata)
        print("RRN27_METADATA=UPDATED (public minimal JSON only)")
    else:
        print("RRN27_UPSTREAM=PASS; RRN27_SCHEMA=PASS; metadata content withheld")


if __name__ == "__main__":
    try:
        main()
    except (Blocked, HTTPError, URLError, TimeoutError, OSError) as exc:
        # Do not print raw response, song filenames, private metadata or cookies.
        category = type(exc).__name__
        print("RRN27_METADATA=BLOCKED (" + category + "; examine private LibreTime logs)", file=sys.stderr)
        sys.exit(2)
