#!/usr/bin/env python
"""Publish minimized, expiring LibreTime show schedule on existing RMS Apache.

Python 2.7/3 stdlib only. Does not expose IOT server/API credentials or
change Docker/Apache/audio. Only the seven-day public show grid is emitted.
"""
from __future__ import print_function

import argparse
from datetime import datetime, timedelta
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
    from html import unescape as html_unescape
except ImportError:
    from urllib2 import HTTPRedirectHandler, ProxyHandler, Request, build_opener
    from urllib2 import HTTPError, URLError
    from HTMLParser import HTMLParser
    html_unescape = HTMLParser().unescape

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)

UPSTREAM = "http://10.10.1.100:8700/api/week-info/"
DOCROOT = "/var/www/radio-listener"
TARGET = os.path.join(DOCROOT, "radio-schedule.json")
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
THAILAND_OFFSET = timedelta(hours=7)
MAX_RESPONSE = 524288
MAX_AGE_SECONDS = 3600
MAX_SHOWS = 500


class Blocked(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("upstream redirect rejected")


def get_json():
    opener = build_opener(ProxyHandler({}), NoRedirect())
    response = opener.open(Request(UPSTREAM, headers={"Accept": "application/json"}), timeout=8)
    try:
        if response.getcode() != 200:
            raise Blocked("upstream HTTP must be 200")
        if response.info().get("Content-Type", "").lower().split(";", 1)[0].strip() != "application/json":
            raise Blocked("upstream content type must be JSON")
        raw = response.read(MAX_RESPONSE + 1)
    finally:
        response.close()
    if len(raw) > MAX_RESPONSE:
        raise Blocked("upstream response oversized")
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise Blocked("upstream not a complete JSON document")


def sanitize_text(value):
    if not isinstance(value, string_types):
        return None
    cleaned = "".join(ch for ch in html_unescape(value) if ord(ch) >= 32 and ord(ch) != 127).strip()
    return cleaned[:160] or None


def parse_local(value):
    if not isinstance(value, string_types):
        return None
    try:
        # LibreTime legacy week-info timestamps are in the configured station time zone.
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def project(payload, now=None):
    if not isinstance(payload, dict) or any(not isinstance(payload.get(day), list) for day in WEEKDAYS):
        raise Blocked("LibreTime week-info schema unavailable; check public schedule API preference")
    now = int(time.time() if now is None else now)
    local_today = (datetime.utcfromtimestamp(now) + THAILAND_OFFSET).date()
    limit = local_today + timedelta(days=7)
    shows = []
    for day in WEEKDAYS:
        for entry in payload[day]:
            if not isinstance(entry, dict):
                continue
            title = sanitize_text(entry.get("name"))
            start = parse_local(entry.get("start_timestamp") or entry.get("starts"))
            end = parse_local(entry.get("end_timestamp") or entry.get("ends"))
            if not title or start is None or end is None:
                continue
            duration = (end - start).total_seconds()
            if not (0 < duration <= 86400) or not (local_today <= start.date() < limit):
                continue
            shows.append({"title": title,
                          "starts_at": start.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                          "ends_at": end.strftime("%Y-%m-%dT%H:%M:%S+07:00")})
            if len(shows) > MAX_SHOWS:
                raise Blocked("unexpectedly large public show schedule")
    shows.sort(key=lambda item: (item["starts_at"], item["title"]))
    return {"rcat_public_schedule": {"schema": 1, "timezone": "Asia/Bangkok",
                                     "generated_at": now, "expires_at": now + MAX_AGE_SECONDS},
            "shows": shows}


def publish(data):
    if not os.path.isdir(DOCROOT) or os.path.islink(DOCROOT):
        raise Blocked("radio listener DocumentRoot unavailable")
    try:
        old_stat = os.lstat(TARGET)
    except OSError as exc:
        if exc.errno != errno.ENOENT:
            raise
    else:
        if not stat.S_ISREG(old_stat.st_mode):
            raise Blocked("public schedule target is not a regular file")
        with open(TARGET, "rb") as old:
            previous = old.read(MAX_RESPONSE + 1)
        if len(previous) > MAX_RESPONSE:
            raise Blocked("existing target too large")
        try:
            old_data = json.loads(previous.decode("ascii"))
        except (ValueError, UnicodeError):
            raise Blocked("existing target not owned by RRN schedule")
        if not isinstance(old_data, dict) or not isinstance(old_data.get("rcat_public_schedule"), dict) or old_data["rcat_public_schedule"].get("schema") != 1:
            raise Blocked("existing target not owned by RRN schedule")

    temp = None
    try:
        fd, temp = tempfile.mkstemp(dir=DOCROOT, prefix=".rrn28-", suffix=".tmp")
        with os.fdopen(fd, "wb") as output:
            encoded = json.dumps(data, ensure_ascii=True, separators=(",", ":"),
                                 allow_nan=False).encode("ascii")
            output.write(encoded + b"\n")
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temp, 0o644)
        os.rename(temp, TARGET)
        temp = None
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)


def main():
    parser = argparse.ArgumentParser(description="RCAT seven-day public schedule exporter")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--probe", action="store_true")
    actions.add_argument("--apply", action="store_true")
    flags = parser.parse_args()
    data = project(get_json())
    if flags.apply:
        if os.geteuid() != 0:
            raise Blocked("apply requires RMS root")
        publish(data)
        print("RRN28_SCHEDULE=UPDATED COUNT=" + str(len(data["shows"])))
    else:
        print("RRN28_SCHEDULE_PROBE=PASS COUNT=" + str(len(data["shows"])))


if __name__ == "__main__":
    try:
        main()
    except (Blocked, HTTPError, URLError, SocketTimeout, OSError, IOError) as exc:
        print("RRN28_SCHEDULE=BLOCKED (" + type(exc).__name__ +
              "; check allowed public week-info access)", file=sys.stderr)
        sys.exit(2)
