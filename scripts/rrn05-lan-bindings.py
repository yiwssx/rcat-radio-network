#!/usr/bin/env python3
"""RRN-05: one-command scoped LAN binding change for the existing radio stack.

Expose existing listener (8600), Show DJ (8605), and web UI (8700) on the
host's 10.10.1.100 address. Fix LibreTime's matching browser-visible URLs.
Recreate only radio Icecast/Liquidsoap/nginx; restart five radio config readers.
Does not change MikroTik, Docker Engine, DNS, firewall, external RCAT services,
named Docker volumes, images, credentials, or the legacy checkout.
Important: existing MikroTik public dst-nat rules can forward WAN traffic to
these three ports; a LAN IP bind does NOT make them private behind dst-nat.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time

PROJECT = "rcat_radio_network"
LAN = "10.10.1.100"
RUNTIME = Path("/opt/rcat-libretime-runtime")
PRIVATE = Path("/etc/rcat-radio-network")
BACKUP = Path("/var/backups/rcat-radio-network")
OVERRIDE = RUNTIME / "radio.override.yml"
CONFIG = PRIVATE / "config.yml"
SERVICES = {"postgres", "rabbitmq", "playout", "liquidsoap",
            "analyzer", "worker", "api", "legacy", "nginx", "icecast"}
PORTS = {"icecast": (8600, 8000), "liquidsoap": (8605, 8002),
         "nginx": (8700, 8080)}
RECREATE = ("icecast", "liquidsoap", "nginx")
RESTART = ("playout", "analyzer", "worker", "api", "legacy")


class Blocked(Exception):
    pass


def need(ok, msg):
    if not ok:
        raise Blocked(msg)


def command(argv, timeout=120):
    env = {"PATH": os.environ.get("PATH", "/usr/local/sbin:/usr/local/bin:"
                                 "/usr/sbin:/usr/bin:/sbin:/bin"),
           "HOME": "/root", "DOCKER_CONTEXT": "default"}
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout, env=env, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Blocked("Radio-scoped command failed to run or timed out") from e
    # Docker Compose renders secrets; never echo stdout/stderr on error.
    need(p.returncode == 0, "Radio-scoped command failed: " + argv[0])
    return p.stdout.strip()


def compose():
    return ["docker", "compose", "--project-directory", str(RUNTIME),
            "--env-file", str(PRIVATE / "compose.env"), "-p", PROJECT,
            "-f", str(RUNTIME / "docker-compose.yml"),
            "-f", str(OVERRIDE)]


def file_check(p):
    need(p.is_file() and not p.is_symlink(), "Missing or symlinked radio file")
    need(p.resolve().is_relative_to(RUNTIME.resolve()) or
         p.resolve().is_relative_to(PRIVATE.resolve()),
         "File outside the two isolated radio paths")


def running_services():
    ids = command(["docker", "ps", "-q", "--filter",
                   "label=com.docker.compose.project=" + PROJECT], 30).splitlines()
    need(len(ids) == 10, "Expected 10 running radio containers")
    data = json.loads(command(["docker", "inspect", *ids], 45))
    names = [x["Config"]["Labels"].get("com.docker.compose.service") for x in data]
    need(set(names) == SERVICES and len(set(names)) == 10,
         "Unexpected radio Compose service layout")


def host_lan_present():
    interfaces = json.loads(command(["ip", "-j", "-4", "addr", "show"], 30))
    need(any(x.get("local") == LAN
             for item in interfaces for x in item.get("addr_info", [])),
         "Expected LAN address is not assigned to the RCAT Host")


def rewrite(override, config):
    old_ports = {
        "127.0.0.1:8600:8000": LAN + ":8600:8000",
        "127.0.0.1:8605:8002": LAN + ":8605:8002",
        "127.0.0.1:8700:8080": LAN + ":8700:8080",
    }
    new_override = override
    for old, new in old_ports.items():
        need(new_override.count(old) == 1, "Unexpected old radio port mapping")
        need(new_override.count(new) == 0, "New mapping already present")
        new_override = new_override.replace(old, new, 1)

    old_urls = {
        "http://127.0.0.1:8700": "http://" + LAN + ":8700",
        "http://127.0.0.1:8600/main.mp3": "http://" + LAN + ":8600/main.mp3",
    }
    new_config = config
    for old, new in old_urls.items():
        need(new_config.count(old) == 1, "Unexpected original public URL")
        need(new_config.count(new) == 0, "LAN URL already configured")
        new_config = new_config.replace(old, new, 1)

    # Avoid showing the wrong Liquidsoap source port (8002) in DJ settings:
    # advertised Show URL should use host-mapped 8605, while internal port
    # stays 8002 for LibreTime itself.
    show = re.search(r"(?ms)^    show:\n(.*?)^      public_url:\s*$", new_config)
    need(show is not None, "LibreTime Show Source settings not found")
    block = show.group(0)
    need(block.count("      public_url:") == 1, "Unexpected show URL structure")
    new_config = new_config.replace(
        block, block.replace("      public_url:",
                             '      public_url: "http://' + LAN + ':8605/show"'), 1)
    return new_override, new_config


def write_in_place(path, content):
    # Keep the existing inode: the vendor bind-mounts this exact file in
    # running radio containers. Preserve its existing file permissions.
    with open(path, "r+", encoding="utf-8") as f:
        f.seek(0)
        f.write(content)
        f.truncate()
        f.flush()
        os.fsync(f.fileno())


def check_model(host):
    model = json.loads(command(compose() + ["config", "--format", "json"], 60))
    need(model.get("name") == PROJECT, "Unexpected Compose project")
    services = model.get("services", {})
    need(set(services) == SERVICES, "Unexpected Compose service list")
    ports = set()
    for service, spec in services.items():
        for p in spec.get("ports", []):
            ports.add((service, str(p.get("host_ip", "")),
                       int(p.get("published", -1)),
                       int(p.get("target", -1)), p.get("protocol", "tcp")))
    expected = {(name, host, outer, inner, "tcp")
                for name, (outer, inner) in PORTS.items()}
    need(ports == expected, "Unexpected Compose network exposure")
    need(set(model.get("volumes", {})) ==
         {"postgres_data", "libretime_storage", "libretime_playout"},
         "Unexpected Compose volumes")
    need(set(model.get("networks", {})) == {"default"},
         "Unexpected Compose network")


def make_backup(original_override, original_config):
    need(BACKUP.is_dir() and not BACKUP.is_symlink()
         and BACKUP.stat().st_uid == 0
         and BACKUP.stat().st_mode & 0o077 == 0,
         "Root-only radio backup directory missing or unsafe")
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = BACKUP / ("lan-binding-before-" + timestamp)
    folder.mkdir(mode=0o700)
    for name, data in (("radio.override.yml", original_override),
                       ("config.yml", original_config)):
        path = folder / name
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    return folder


def restart_changed_services():
    # Recreate three containers only for host port changes. Never pull images,
    # restart Docker itself, remove Docker volumes or alter other projects.
    command(compose() + ["up", "-d", "--no-deps", "--no-build",
                         "--pull", "never", "--force-recreate", *RECREATE], 300)
    # Five existing radio services read the bind-mounted public URLs on start.
    command(compose() + ["restart", *RESTART], 240)


def inspect_bindings():
    ids = command(["docker", "ps", "-q", "--filter",
                   "label=com.docker.compose.project=" + PROJECT], 30).splitlines()
    need(len(ids) == 10, "Radio containers did not all restart")
    data = json.loads(command(["docker", "inspect", *ids], 60))
    by_name = {x["Config"]["Labels"].get("com.docker.compose.service"): x
               for x in data}
    need(set(by_name) == SERVICES, "Radio project changed unexpectedly")
    for name, (outer, inner) in PORTS.items():
        bindings = by_name[name]["HostConfig"]["PortBindings"]
        actual = bindings.get(str(inner) + "/tcp", [])
        need(len(actual) == 1 and actual[0]["HostIp"] == LAN
             and actual[0]["HostPort"] == str(outer),
             "Docker radio LAN binding did not apply")
    return all(x["State"]["Running"] for x in data)


def local_http(port, path):
    import urllib.request
    try:
        with urllib.request.urlopen(
            "http://" + LAN + ":" + str(port) + path, timeout=3
        ) as response:
            return 200 <= response.status < 400
    except Exception:
        return False


def listen_ready():
    for _ in range(20):
        try:
            with socket.create_connection((LAN, 8605), timeout=3):
                show_ok = True
        except OSError:
            show_ok = False
        if show_ok and local_http(8700, "/") and local_http(8600, "/status-json.xsl"):
            return True
        time.sleep(2)
    return False


def apply():
    need(os.geteuid() == 0, "Run as root on the RCAT Host")
    for directory in (RUNTIME, PRIVATE):
        need(directory.is_dir() and not directory.is_symlink(),
             "Radio runtime directory missing or symlinked")
    for p in (OVERRIDE, CONFIG, RUNTIME / "docker-compose.yml",
              PRIVATE / "compose.env"):
        file_check(p)
    need((PRIVATE / "compose.env").stat().st_mode & 0o077 == 0,
         "Radio private env file has unsafe permissions")
    host_lan_present()
    running_services()

    original_override = OVERRIDE.read_text(encoding="utf-8")
    original_config = CONFIG.read_text(encoding="utf-8")
    lan_ports = all((LAN + ":" + str(outer) + ":" + str(inner)) in original_override
                    for outer, inner in PORTS.values())
    lan_urls = all(x in original_config for x in (
        "http://" + LAN + ":8700", "http://" + LAN + ":8600/main.mp3",
        "http://" + LAN + ":8605/show"))
    if lan_ports and lan_urls:
        check_model(LAN)
        need(inspect_bindings(), "Existing LAN-bound radio stack is not running")
        print("RRN05_LAN_BINDINGS=ALREADY_APPLIED")
        return

    updated_override, updated_config = rewrite(original_override, original_config)
    check_model("127.0.0.1")  # validate existing model before any change
    folder = make_backup(original_override, original_config)
    print("RRN05_BACKUP_CONFIG_SAVED=" + str(folder), flush=True)
    changed = False
    try:
        changed = True
        write_in_place(OVERRIDE, updated_override)
        write_in_place(CONFIG, updated_config)
        check_model(LAN)
        print("RRN05_COMPOSE_VALIDATED=PASS", flush=True)
        restart_changed_services()
        need(inspect_bindings(), "Docker binding/readiness did not converge")
        need(listen_ready(), "LAN ports/HTTP did not become ready")
    except BaseException as exc:
        if changed:
            print("RRN05_APPLY=FAILED_ROLLBACK_ATTEMPT", flush=True)
            try:
                write_in_place(OVERRIDE, original_override)
                write_in_place(CONFIG, original_config)
                check_model("127.0.0.1")
                restart_changed_services()
                need(inspect_bindings() or False,
                     "Radio project failed to restart after rollback")
                print("RRN05_ROLLBACK=COMMANDS_SUCCEEDED", flush=True)
            except BaseException:
                print("RRN05_ROLLBACK=NEEDS_OPERATOR_ATTENTION", flush=True)
        raise Blocked("LAN binding change failed: radio-only rollback attempted") from exc
    print("RRN05_LAN_BINDINGS=PASS")
    print("icecast=http://" + LAN + ":8600/main.mp3")
    print("show_source=" + LAN + ":8605")
    print("libretime=http://" + LAN + ":8700")
    print("radio_services_running=10")
    print("lan_port_http_tcp=PASS")
    print("source_audio_after_recreate=NOT_TESTED")
    print("public_router_nat=UNCHANGED")
    print("WAN_EXPOSURE_WARNING=EXISTING_MIKROTIK_DST_NAT_MAY_FORWARD_ALL_THREE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", required=True)
    args = parser.parse_args()
    try:
        apply()
    except Blocked as exc:
        print("RRN05_STATUS=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(2)
