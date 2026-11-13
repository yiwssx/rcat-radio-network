#!/usr/bin/env python3
"""RRN-05: narrowly fix LibreTime 4.5.0 LAN login URL after the port bind.

Official LibreTime troubleshooting: /login 'Oops' can arise when the browser
origin does not equal general.public_url. Modify exactly three public URL
fields in the EXISTING private config, not Docker bindings or server data.
No Mikrotik, public DNS, firewall, DB, images, radio volumes or engine edits.

WARNING: the previously observed MikroTik public DST-NAT may expose the
LAN-bound Admin (8700) and Show DJ (8605) services to WAN as well.
"""
import datetime as dt
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener

PROJECT = "rcat_radio_network"
PRIVATE = Path("/etc/rcat-radio-network")
CONFIG = PRIVATE / "config.yml"
BACKUPS = Path("/var/backups/rcat-radio-network")
LAN = "10.10.1.100"
BASE = "http://" + LAN
EXPECTED = {
    "postgres", "rabbitmq", "playout", "liquidsoap",
    "analyzer", "worker", "api", "legacy", "nginx", "icecast",
}
BINDINGS = {
    "icecast": ("8000/tcp", "8600"),
    "liquidsoap": ("8002/tcp", "8605"),
    "nginx": ("8080/tcp", "8700"),
}
OPENER = build_opener(ProxyHandler({}))


class Blocked(Exception):
    pass


def require(value, message):
    if not value:
        raise Blocked(message)


def docker(args, stage, timeout=60):
    env = {
        "HOME": "/root",
        "DOCKER_CONTEXT": "default",
        "PATH": os.environ.get(
            "PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ),
    }
    try:
        result = subprocess.run(
            ["docker", *args], capture_output=True, text=True,
            env=env, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        raise Blocked(stage + ": Docker command unavailable or timed out") from None
    # Never expose Docker stdout/stderr of a failed command (might hold secrets).
    require(result.returncode == 0,
            stage + ": Docker command exit=" + str(result.returncode))
    return result.stdout.strip()


def radio_containers():
    ids = docker(["ps", "-aq", "--filter",
                  "label=com.docker.compose.project=" + PROJECT],
                 "radio_inventory", 30).splitlines()
    require(len(ids) == 10, "Expected 10 existing radio containers")
    data = json.loads(docker(["inspect", *ids], "inspect_radio", 40))
    found = {
        item["Config"]["Labels"].get("com.docker.compose.service"): item
        for item in data
    }
    require(len(found) == 10 and set(found) == EXPECTED,
            "Unexpected radio project services")
    return found


def radio_ready():
    current = radio_containers()
    if not all(item["State"]["Running"] for item in current.values()):
        return False
    for service, (port, published) in BINDINGS.items():
        mapping = current[service]["HostConfig"]["PortBindings"]
        bind = mapping.get(port) or []
        if len(bind) != 1 or bind[0].get("HostIp") != LAN or \
                bind[0].get("HostPort") != published:
            return False
    return True


def tcp(host, port):
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def fetch(path):
    url = BASE + ":8700" + path
    try:
        with OPENER.open(url, timeout=5) as response:
            return response.status, response.geturl(), response.read(200000).decode(
                "utf-8", errors="replace"
            )
    except HTTPError as error:
        return error.code, error.geturl(), error.read(200000).decode(
            "utf-8", errors="replace"
        )
    except (URLError, OSError, ValueError):
        return 0, "", ""


def icecast_ready():
    try:
        with OPENER.open(BASE + ":8600/status-json.xsl", timeout=4) as response:
            return response.status == 200
    except Exception:
        return False


def login_ready():
    code, final_url, body = fetch("/login")
    if code != 200 or not final_url.startswith(BASE + ":8700/"):
        return False
    lowered = body.lower()
    if "oops!" in lowered and "something went wrong" in lowered:
        return False
    return "<form" in lowered and "password" in lowered


def wait_until(predicate, timeout):
    cutoff = time.monotonic() + timeout
    while time.monotonic() < cutoff:
        if predicate():
            return True
        time.sleep(2)
    return False


def replacement(text):
    old_general = '  public_url: "http://127.0.0.1:8700"'
    new_general = '  public_url: "' + BASE + ':8700"'
    old_stream = '        public_url: "http://127.0.0.1:8600/main.mp3"'
    new_stream = '        public_url: "' + BASE + ':8600/main.mp3"'
    for old, new in ((old_general, new_general), (old_stream, new_stream)):
        require(text.count(old) == 1 and new not in text,
                "Expected unique original LibreTime public URL not found")
        text = text.replace(old, new, 1)

    # Restrict the DJ Show URL change to stream.inputs.show; do not touch any
    # other YAML 'public_url' or any auth, codec or secret fields.
    header = "\n    show:\n"
    require(text.count(header) == 1, "Expected Show Source section not found")
    a = text.index(header) + len(header)
    outputs = text.find("\n  outputs:\n", a)
    require(outputs > a, "Expected output stream boundary not found")
    block = text[a:outputs]
    blank = "      public_url:\n"
    require(block.count(blank) == 1,
            "Expected blank Show Source public URL not found")
    block = block.replace(blank,
                          '      public_url: "' + BASE + ':8605/show"\n', 1)
    text = text[:a] + block + text[outputs:]
    return text


def save_original(original):
    require(BACKUPS.is_dir() and not BACKUPS.is_symlink() and
            BACKUPS.stat().st_uid == 0 and
            BACKUPS.stat().st_mode & 0o077 == 0,
            "Root-only radio backup directory not ready")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BACKUPS / ("libretime-config-before-lan-url-" + stamp + ".yml")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(original)
        fh.flush()
        os.fsync(fh.fileno())
    return path


def write_in_place(content):
    # The file is bind-mounted into LibreTime containers. Keep the inode
    # and original mode/ownership so the running bind mount sees the update.
    with open(CONFIG, "r+", encoding="utf-8") as fh:
        fh.seek(0)
        fh.write(content)
        fh.truncate()
        fh.flush()
        os.fsync(fh.fileno())


def restart_readers(containers):
    # Only legacy + API read the changed web origin for login/API CORS.
    # Does not recreate/remove radio containers or restart the engine.
    for service in ("api", "legacy"):
        docker(["restart", "-t", "15", containers[service]["Id"]],
               "restart_radio_" + service, 120)


def recover(original, containers):
    write_in_place(original)
    restart_readers(containers)
    require(wait_until(
        lambda: radio_ready() and tcp(LAN, 8605) and icecast_ready()
        and 200 <= fetch("/")[0] < 400, 75
    ), "Rollback did not restore radio HTTP/TCP readiness")
    print("RRN05_URL_ROLLBACK=RADIO_HEALTH_CONFIRMED", flush=True)


def apply():
    require(os.geteuid() == 0, "Run as root on RCAT radio host")
    require(PRIVATE.is_dir() and not PRIVATE.is_symlink() and
            PRIVATE.stat().st_mode & 0o077 == 0,
            "Radio private config directory missing/unsafe")
    require(CONFIG.is_file() and not CONFIG.is_symlink() and
            CONFIG.stat().st_uid == 0,
            "Radio private config file missing/unsafe")
    require(radio_ready(), "Radio LAN containers and bindings not ready")
    require(tcp(LAN, 8605) and icecast_ready() and
            200 <= fetch("/")[0] < 400,
            "Radio LAN ports/UI or Icecast not responding")

    original = CONFIG.read_text(encoding="utf-8")
    if ('  public_url: "' + BASE + ':8700"' in original and
        '        public_url: "' + BASE + ':8600/main.mp3"' in original and
        '      public_url: "' + BASE + ':8605/show"' in original):
        require(login_ready(), "LAN public URLs already set but login page unhealthy")
        print("RRN05_PUBLIC_URL=ALREADY_APPLIED")
        return

    updated = replacement(original)
    backup = save_original(original)
    print("RRN05_PRIVATE_CONFIG_BACKUP=" + str(backup), flush=True)

    stage = "write_radio_public_urls"
    try:
        write_in_place(updated)
        stage = "restart_radio_api_legacy"
        restart_readers(radio_containers())
        stage = "verify_lan_login"
        require(wait_until(
            lambda: radio_ready() and tcp(LAN, 8605) and icecast_ready()
            and login_ready(), 90
        ), "LAN login page not healthy after URL change")
    except Exception as error:
        print("RRN05_FAILED_STAGE=" + stage, flush=True)
        print("RRN05_ERROR=" + str(error), flush=True)
        try:
            recover(original, radio_containers())
        except Exception as rollback_error:
            print("RRN05_URL_ROLLBACK=NEEDS_OPERATOR_ATTENTION", flush=True)
            print("RRN05_ROLLBACK_ERROR=" + str(rollback_error), flush=True)
        raise Blocked("LAN public URL fix not accepted; see rollback outcome") from None

    print("RRN05_PUBLIC_URL=PASS")
    print("libretime_url=" + BASE + ":8700/login")
    print("icecast_public_url=" + BASE + ":8600/main.mp3")
    print("show_public_url=" + BASE + ":8605/show")
    print("radio_containers_running=10")
    print("login_html=HTTP_200_FORM_PRESENT_NO_OOPS")
    print("admin_login_credentials=NOT_TESTED")
    print("public_mikrotik_nat=UNCHANGED_POSSIBLE_WAN_EXPOSURE")


if __name__ == "__main__":
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--apply", action="store_true", required=True)
        parser.parse_args()
        apply()
    except Blocked as exc:
        print("RRN05_STATUS=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(2)
