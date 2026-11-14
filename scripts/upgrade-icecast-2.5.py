#!/usr/bin/env python3
"""Operator-gated upgrade of RCAT's EXISTING Icecast container only.

This is a migration for the installed radio runtime, not a fresh installer.
It leaves LibreTime 4.5.0, data volumes, NAT, TLS certificates, the listener UI,
and every other Docker Compose service unchanged. No credentials are printed.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

PROJECT = "rcat_radio_network"
RUNTIME = Path("/opt/rcat-libretime-runtime")
PRIVATE = Path("/etc/rcat-radio-network")
BACKUPS = Path("/var/backups/rcat-radio-network")
COMPOSE_FILE = RUNTIME / "docker-compose.yml"
OVERRIDE = RUNTIME / "radio.override.yml"
ENV_FILE = PRIVATE / "compose.env"
CONTAINER = PROJECT + "-icecast-1"
OLD = "ghcr.io/libretime/icecast:2.4.4"
NEW = "ghcr.io/libretime/icecast:2.5.0"
SERVICES = {
    "postgres", "rabbitmq", "playout", "liquidsoap", "analyzer",
    "worker", "api", "legacy", "nginx", "icecast",
}
IMAGE_PATTERN = re.compile(
    r"(?m)^(\s*image:\s*)ghcr\.io/libretime/icecast:2\.4\.4(\s*(?:#.*)?)$"
)


class Stop(Exception):
    pass


def require(ok, why):
    if not ok:
        raise Stop(why)


def call(args, timeout=120, allowed=(0,)):
    try:
        result = subprocess.run(
            args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Stop("Command unavailable or timed out: " + args[0]) from exc
    if result.returncode not in allowed:
        raise Stop("Command failed: " + " ".join(args[:2])
                   + " (status " + str(result.returncode) + ")")
    return result


def compose_args():
    return [
        "docker", "compose", "--project-directory", str(RUNTIME),
        "--env-file", str(ENV_FILE), "-p", PROJECT,
        "-f", str(COMPOSE_FILE), "-f", str(OVERRIDE),
    ]


def model():
    return json.loads(call(compose_args() + ["config", "--format", "json"]).stdout)


def inspect():
    items = json.loads(call(["docker", "inspect", CONTAINER]).stdout)
    require(len(items) == 1, "Expected exactly one radio Icecast container")
    return items[0]


def check_files():
    require(os.geteuid() == 0, "Root access required; use sudo")
    for path in (COMPOSE_FILE, OVERRIDE, ENV_FILE):
        require(path.is_file() and not path.is_symlink(),
                "Missing or symlinked required radio file: " + str(path))
    require(BACKUPS.is_dir() and not BACKUPS.is_symlink(),
            "Radio backup directory missing")
    require((BACKUPS.stat().st_mode & 0o022) == 0,
            "Radio backup directory must not be group/world writable")
    require(any(BACKUPS.glob("rcat_radio_network-*.tar.gz.sha256")),
            "No existing completed RRN-06 backup checksum sidecar; stop")


def check_runtime():
    before = model()
    require(set(before.get("services", {})) == SERVICES,
            "Expected isolated ten-service LibreTime project")
    require(before["services"]["icecast"].get("image") == OLD,
            "Icecast in Compose is not the expected 2.4.4 source")
    require(any(str(p.get("target")) == "8443"
                for p in before["services"]["icecast"].get("ports", [])),
            "Expected the existing Icecast native TLS port 8443")
    obj = inspect()
    labels = obj["Config"].get("Labels", {})
    require(labels.get("com.docker.compose.project") == PROJECT
            and labels.get("com.docker.compose.service") == "icecast",
            "Not the intended radio-only Icecast container")
    require(obj["State"]["Running"], "Radio Icecast is not running")
    require(obj["Config"]["Image"] == OLD,
            "Running image differs from pinned Icecast 2.4.4")
    src = COMPOSE_FILE.read_text(encoding="utf-8")
    require(len(IMAGE_PATTERN.findall(src)) == 1,
            "Base Compose must contain exactly one pinned 2.4.4 image")
    require(call(["docker", "image", "inspect", OLD]).returncode == 0,
            "Old rollback image not available")
    return before, src


def atomic_replace(path, text):
    fd, candidate = tempfile.mkstemp(prefix=".radio-icecast-", dir=path.parent)
    try:
        os.fchmod(fd, path.stat().st_mode & 0o777)
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            fp.write(text)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(candidate, path)
    finally:
        if os.path.exists(candidate):
            os.unlink(candidate)


def verify_model(before):
    after = model()
    require(set(after.get("services", {})) == SERVICES,
            "Upgrade changed radio service set")
    expected = json.loads(json.dumps(before))
    expected["services"]["icecast"]["image"] = NEW
    require(after == expected,
            "Upgrade would change Compose settings other than Icecast image")


def recreate_icecast():
    call(compose_args() + [
        "up", "-d", "--no-deps", "--pull", "never",
        "--force-recreate", "icecast",
    ], timeout=180)


def verify_https_stream():
    obj = inspect()
    require(obj["State"]["Running"] and obj["Config"]["Image"] == NEW,
            "New Icecast image not running")
    # An endless stream intentionally ends curl at max-time; status 28 is
    # acceptable ONLY if a valid TLS exchange delivered actual MP3 bytes.
    test = call([
        "curl", "--noproxy", "*", "-sS", "--max-time", "7",
        "--resolve", "radio.rcat.ac.th:8443:10.10.1.100",
        "-o", "/dev/null", "-w", "%{http_code} %{size_download} %{ssl_verify_result}",
        "https://radio.rcat.ac.th:8443/main.mp3",
    ], timeout=12, allowed=(0, 28))
    fields = test.stdout.strip().split()
    require(len(fields) == 3 and fields[0] == "200" and fields[2] == "0"
            and float(fields[1]) >= 4096,
            "Icecast TLS/MP3 stream could not be verified for 7 seconds")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", action="store_true", help="Read-only preflight")
    p.add_argument("--apply", action="store_true", help="Upgrade only Icecast")
    p.add_argument("--approve-brief-stream-reconnect", action="store_true",
                   help="Acknowledge brief public audio interruption")
    args = p.parse_args()
    require(not (args.plan and args.apply), "Choose plan OR apply")
    require(not args.approve_brief_stream_reconnect or args.apply,
            "Approval flag is only valid with --apply")
    if args.apply:
        require(args.approve_brief_stream_reconnect,
                "Apply needs --approve-brief-stream-reconnect")

    check_files()
    before, src = check_runtime()
    print("RADIO_UPGRADE_SCOPE=ICECAST_ONLY")
    print("SOURCE_IMAGE=" + OLD)
    print("TARGET_IMAGE=" + NEW)
    print("LIBRETIME=UNCHANGED_4.5.0")
    if not args.apply:
        print("RADIO_UPGRADE=READY_PLAN_ONLY")
        return

    # Pull BEFORE touching running configuration or services.
    call(["docker", "pull", NEW], timeout=300)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUPS / ("icecast-compose-before-2.5.0-" + now + ".yml")
    require(not backup.exists(), "Refusing overwrite of rollback snapshot")
    with backup.open("x", encoding="utf-8") as fp:
        os.chmod(backup, 0o600)
        fp.write(src)
    replacement = IMAGE_PATTERN.sub(lambda m: m.group(1) + NEW + m.group(2), src)
    require(replacement != src, "No pinned image replaced")
    changed = False
    try:
        atomic_replace(COMPOSE_FILE, replacement)
        changed = True
        verify_model(before)
        recreate_icecast()
        verify_https_stream()
    except Exception:
        if changed:
            try:
                atomic_replace(COMPOSE_FILE, src)
                recreate_icecast()
                print("RADIO_UPGRADE_ROLLBACK=OLD_IMAGE_RESTORED")
            except Exception:
                print("RADIO_UPGRADE_ROLLBACK=FAILED_OPERATOR_ATTENTION_REQUIRED",
                      file=sys.stderr)
        raise
    print("RADIO_UPGRADE=HOST_HTTPS_STREAM_PASS")
    print("ROLLBACK_COMPOSE_SNAPSHOT=" + str(backup))
    print("MOBILE_2_SECOND_PLAYBACK=NOT_YET_VERIFIED")
    print("OTHER_RADIO_SERVICES_AND_VOLUMES=UNMODIFIED_BY_SCRIPT")


if __name__ == "__main__":
    try:
        main()
    except (Stop, ValueError, KeyError, TypeError, OSError) as exc:
        print("RADIO_UPGRADE=STOPPED: " + str(exc), file=sys.stderr)
        sys.exit(1)
