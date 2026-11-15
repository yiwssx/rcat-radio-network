#!/usr/bin/env python
"""RRN-27: publish an expiring same-origin JSON snapshot on existing RMS.

Uses only Python 2.7/3 standard libraries already present on the approved host.
Run from one radio-only cron entry after the public feed is accepted.
Does not change Apache, Docker, Icecast, LibreTime or audio.
"""
from __future__ import print_function

import argparse
import errno
import json
import os
import stat
import sys
import tempfile
import time
from socket import timeout as SocketTimeout

try:
    from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
    from urllib.error import HTTPError, URLError
except ImportError:  # Python 2.7 on the existing RMS host; no new runtime.
    from urllib2 import HTTPRedirectHandler, ProxyHandler, Request, build_opener
    from urllib2 import HTTPError, URLError

try:
    string_types = (basestring,)
except NameError:  # Python 3
    string_types = (str,)

UPSTREAM = "http://10.10.1.100:8700/api/live-info-v2/"  # Existing private IOT LAN route.
DOCROOT = "/var/www/radio-listener"             # Verify the current RMS Apache DocumentRoot.
TARGET = os.path.join(DOCROOT, "radio-metadata.json")
MAX_RESPONSE = 262144
MAX_AGE_SECONDS = 180


class Blocked(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("upstream redirected instead of returning public metadata")


def get_json():
    # No environment proxy, cookies, API key or redirects. LAN only.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    req = Request(UPSTREAM, headers={"Accept": "application/json"})
    response = opener.open(req, timeout=7)
    try:
        if response.getcode() != 200:
            raise Blocked("upstream HTTP is not 200")
        content_type = response.info().get("Content-Type", "").lower()
        if content_type.split(";", 1)[0].strip() != "application/json":
            raise Blocked("upstream does not return application/json")
        data = response.read(MAX_RESPONSE + 1)
    finally:
        response.close()
    if len(data) > MAX_RESPONSE:
        raise Blocked("upstream JSON exceeds the bounded size")
    try:
        return json.loads(data.decode("utf-8"))  # Reject trailing HTML/500 pages.
    except (UnicodeError, ValueError):
        raise Blocked("upstream is not exactly one valid UTF-8 JSON value")

def nonempty(value):
    if not isinstance(value, string_types):
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
    if not os.path.isdir(DOCROOT) or os.path.islink(DOCROOT):
        raise Blocked("existing RMS radio webroot missing or unsafe")

    try:
        target_stat = os.lstat(TARGET)  # Do not follow an existing target symlink.
    except OSError as exc:
        if exc.errno != errno.ENOENT:
            raise
    else:
        if not stat.S_ISREG(target_stat.st_mode):
            raise Blocked("existing metadata target is not a regular file")
        # Never replace an unrelated existing Apache document.
        try:
            with open(TARGET, "rb") as existing_file:
                existing_bytes = existing_file.read(MAX_RESPONSE + 1)
            if len(existing_bytes) > MAX_RESPONSE:
                raise Blocked("existing target exceeds expected size")
            existing = json.loads(existing_bytes.decode("ascii"))
            if not isinstance(existing, dict) or not isinstance(existing.get("rcat_public_feed"), dict) or existing["rcat_public_feed"].get("schema") != 1:
                raise Blocked("target exists and is not RRN-27 metadata")
        except (UnicodeError, ValueError, AttributeError):
            raise Blocked("existing target is not RRN-27 metadata")

    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=DOCROOT, prefix=".rrn27-", suffix=".tmp")
        with os.fdopen(fd, "wb") as output:
            # ASCII escapes preserve Thai on legacy Apache/Python 2.
            encoded = json.dumps(data, ensure_ascii=True,
                                 separators=(",", ":"), allow_nan=False).encode("ascii")
            output.write(encoded + b"\\n")
            output.flush()
            os.fsync(output.fileno())
        os.chmod(tmp, 0o644)
        os.rename(tmp, TARGET)  # Atomic replace on RMS/Linux, including Python 2.7.
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
    except (Blocked, HTTPError, URLError, SocketTimeout, OSError, IOError) as exc:
        # Do not print raw response, song filenames, private metadata or cookies.
        category = type(exc).__name__
        print("RRN27_METADATA=BLOCKED (" + category + "; examine private LibreTime logs)", file=sys.stderr)
        sys.exit(2)
