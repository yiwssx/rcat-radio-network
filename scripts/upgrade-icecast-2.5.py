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


def compose_args(source_path=COMPOSE_FILE, override_path=OVERRIDE):
    return [
        "docker", "compose", "--project-directory", str(RUNTIME),
        "--env-file", str(ENV_FILE), "-p", PROJECT,
        "-f", str(source_path), "-f", str(override_path),
    ]


def model(source_path=COMPOSE_FILE, override_path=OVERRIDE):
    return json.loads(call(compose_args(source_path, override_path)
                           + ["config", "--format", "json"]).stdout)


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
    override_src = OVERRIDE.read_text(encoding="utf-8")
    # The original RRN-01 override pins Icecast 2.4.4 too.
    build_override_candidate(override_src)
    return before, src, override_src


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


def differing_paths(left, right, location="model", limit=12):
    """Report only JSON key paths, never values or environment secrets."""
    if type(left) is not type(right):
        return [location]
    if isinstance(left, dict):
        found = []
        for key in sorted(set(left) | set(right)):
            loc = location + "." + key
            if key not in left or key not in right:
                found.append(loc)
            else:
                found.extend(differing_paths(left[key], right[key], loc, limit))
            if len(found) >= limit:
                break
        return found[:limit]
    if isinstance(left, list):
        found = []
        if len(left) != len(right):
            found.append(location + ".length")
        for i in range(min(len(left), len(right))):
            found.extend(differing_paths(left[i], right[i],
                                         location + "[" + str(i) + "]", limit))
            if len(found) >= limit:
                break
        return found[:limit]
    return [] if left == right else [location]


def verify_model(before, after):
    require(set(after.get("services", {})) == SERVICES,
            "Upgrade changed radio service set")
    expected = json.loads(json.dumps(before))
    expected["services"]["icecast"]["image"] = NEW
    diff = differing_paths(expected, after)
    require(not diff, "Upgrade would change Compose settings other than "
            "Icecast image; differing keys ONLY: " + ", ".join(diff))


def build_candidate(src):
    replacement, count = IMAGE_PATTERN.subn(
        lambda m: m.group(1) + NEW + m.group(2), src
    )
    require(count == 1, "Expected exactly one base Icecast image pin")
    return replacement


def build_override_candidate(src):
    # Change the image within the Icecast service only, never other services.
    section_pattern = re.compile(
        r"(?ms)^  icecast:[ \t]*\n(.*?)(?=^  [A-Za-z_][\w-]*:[ \t]*\n|\Z)"
    )
    sections = list(section_pattern.finditer(src))
    require(len(sections) == 1,
            "Expected exactly one Icecast service in radio.override.yml")
    section = sections[0]
    body, count = IMAGE_PATTERN.subn(
        lambda m: m.group(1) + NEW + m.group(2), section.group(1)
    )
    require(count == 1,
            "Expected exactly one pinned 2.4.4 image in Icecast override")
    return src[:section.start(1)] + body + src[section.end(1):]


def preflight_candidate(before, base_replacement, override_replacement):
    # Render both candidates, without editing live files or pulling images.
    candidates = []
    try:
        for content in (base_replacement, override_replacement):
            fd, name = tempfile.mkstemp(
                prefix=".radio-icecast-preflight-", suffix=".yml",
                dir=RUNTIME
            )
            candidates.append(Path(name))
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fp:
                fp.write(content)
                fp.flush()
            require(candidates[-1].is_file(),
                    "Could not prepare temporary Compose candidate")
        verify_model(before, model(*candidates))
    finally:
        for candidate in candidates:
            candidate.unlink(missing_ok=True)


def write_snapshot(path, content):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fp:
        fp.write(content)
        fp.flush()
        os.fsync(fp.fileno())


def recreate_icecast():
    call(compose_args() + [
        "up", "-d", "--no-deps", "--pull", "never",
        "--force-recreate", "icecast",
    ], timeout=180)


def verify_https_ready():
    # The player mount may be absent briefly while Liquidsoap reconnects.
    # Do not roll back a healthy Icecast 2.5 HTTPS service merely because
    # /main.mp3 has not yet received source audio within seven seconds.
    last = "not attempted"
    for attempt in range(1, 7):
        obj = inspect()
        require(obj["State"]["Running"] and obj["Config"]["Image"] == NEW,
                "Icecast 2.5.0 failed to remain running")
        try:
            test = subprocess.run([
                "curl", "--noproxy", "*", "--silent", "--show-error",
                "--connect-timeout", "2", "--max-time", "5",
                "--resolve", "radio.rcat.ac.th:8443:10.10.1.100",
                "--output", "/dev/null",
                "--write-out", "%{http_code} %{ssl_verify_result}",
                "https://radio.rcat.ac.th:8443/",
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=7, check=False)
            fields = test.stdout.strip().split()
            code, tls = fields if len(fields) == 2 else ("unknown", "unknown")
            last = "curl=" + str(test.returncode) + " http=" + code + " tls=" + tls
            if test.returncode == 0 and tls == "0" and code in {"200", "302", "403"}:
                print("RADIO_ICECAST_250_HTTPS=READY")
                return
        except (OSError, subprocess.TimeoutExpired):
            last = "curl=timeout_or_unavailable"
        if attempt < 6:
            subprocess.run(["sleep", "2"], check=False)
    raise Stop("Icecast 2.5 HTTPS not ready after 6 bounded attempts; " + last)


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
    before, src, override_src = check_runtime()
    print("RADIO_UPGRADE_SCOPE=ICECAST_ONLY")
    print("SOURCE_IMAGE=" + OLD)
    print("TARGET_IMAGE=" + NEW)
    print("LIBRETIME=UNCHANGED_4.5.0")
    replacement = build_candidate(src)
    override_replacement = build_override_candidate(override_src)
    preflight_candidate(before, replacement, override_replacement)
    print("RADIO_UPGRADE_COMPOSE_DIFF=ICECAST_IMAGE_ONLY")
    print("RADIO_UPGRADE_IMAGE_PINS=BASE_AND_RADIO_OVERRIDE")
    if not args.apply:
        print("RADIO_UPGRADE=READY_PLAN_ONLY")
        return

    # Pull BEFORE touching running configuration or services.
    call(["docker", "pull", NEW], timeout=300)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUPS / ("icecast-compose-before-2.5.0-" + now + ".yml")
    override_backup = BACKUPS / (
        "icecast-override-before-2.5.0-" + now + ".yml"
    )
    require(not backup.exists() and not override_backup.exists(),
            "Refusing overwrite of rollback snapshots")
    write_snapshot(backup, src)
    write_snapshot(override_backup, override_src)
    originals = ((COMPOSE_FILE, src), (OVERRIDE, override_src))
    changed = []
    recreation_attempted = False
    try:
        for path, content in (
            (COMPOSE_FILE, replacement),
            (OVERRIDE, override_replacement),
        ):
            atomic_replace(path, content)
            changed.append(path)
        verify_model(before, model())
        recreation_attempted = True
        recreate_icecast()
        verify_https_ready()
    except Exception:
        if changed:
            try:
                for path, original in originals:
                    if path in changed:
                        atomic_replace(path, original)
                if recreation_attempted:
                    recreate_icecast()
                    print("RADIO_UPGRADE_ROLLBACK=OLD_IMAGE_RESTORED")
                else:
                    print("RADIO_UPGRADE_ROLLBACK=CONFIG_RESTORED_NO_RESTART")
            except Exception:
                print("RADIO_UPGRADE_ROLLBACK=FAILED_OPERATOR_ATTENTION_REQUIRED",
                      file=sys.stderr)
        raise
    print("RADIO_UPGRADE=ICECAST_250_HTTPS_READY")
    print("RADIO_MP3_SOURCE=NOT_A_DEPLOYMENT_GATE")
    print("ROLLBACK_COMPOSE_SNAPSHOT=" + str(backup))
    print("ROLLBACK_OVERRIDE_SNAPSHOT=" + str(override_backup))
    print("MOBILE_2_SECOND_PLAYBACK=NOT_YET_VERIFIED")
    print("OTHER_RADIO_SERVICES_AND_VOLUMES=UNMODIFIED_BY_SCRIPT")


if __name__ == "__main__":
    try:
        main()
    except (Stop, ValueError, KeyError, TypeError, OSError) as exc:
        print("RADIO_UPGRADE=STOPPED: " + str(exc), file=sys.stderr)
        sys.exit(1)
