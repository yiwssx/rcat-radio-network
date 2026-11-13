#!/usr/bin/env python3
"""RRN-05: guarded LAN bindings for exactly three existing radio services.

Purposefully changes ONLY the existing radio.override.yml port mappings.
Does NOT change LibreTime config.yml, databases, images, named volumes,
host Docker, MikroTik, DNS, firewall or any other RCAT project.

NOTE: Existing MikroTik public DST-NAT rules may also expose these LAN-bound
ports to WAN! This script does not make 8605/8700 secure from outside.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from urllib.request import build_opener, ProxyHandler

PROJECT = "rcat_radio_network"
LAN = "10.10.1.100"
RUNTIME = Path("/opt/rcat-libretime-runtime")
PRIVATE = Path("/etc/rcat-radio-network")
BACKUPS = Path("/var/backups/rcat-radio-network")
OVERRIDE = RUNTIME / "radio.override.yml"
RADIO = ("icecast", "liquidsoap", "nginx")
EXPECTED_SERVICES = {
    "postgres", "rabbitmq", "playout", "liquidsoap", "analyzer",
    "worker", "api", "legacy", "nginx", "icecast",
}
PORTS = {"icecast": (8600, 8000), "liquidsoap": (8605, 8002),
         "nginx": (8700, 8080)}
# Skip proxy settings for local connections; allow no public requests.
OPENER = build_opener(ProxyHandler({}))


class Blocked(Exception):
    pass


def require(test, message):
    if not test:
        raise Blocked(message)


def run(args, stage, timeout=120):
    env = {"PATH": os.environ.get(
        "PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    ), "HOME": "/root", "DOCKER_CONTEXT": "default"}
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=timeout, env=env, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise Blocked(stage + ": command unavailable/timeout") from None
    # No Docker stderr/stdout on failures: may contain substituted credentials.
    require(result.returncode == 0, stage + ": command exit=" +
            str(result.returncode))
    return result.stdout.strip()


def compose():
    return ["docker", "compose", "--project-directory", str(RUNTIME),
            "--env-file", str(PRIVATE / "compose.env"), "-p", PROJECT,
            "-f", str(RUNTIME / "docker-compose.yml"),
            "-f", str(OVERRIDE)]


def container_map():
    ids = run(["docker", "ps", "-aq", "--filter",
               "label=com.docker.compose.project=" + PROJECT],
              "project_container_inventory", 45).splitlines()
    require(len(ids) == 10, "expected exactly ten existing radio containers")
    data = json.loads(run(["docker", "inspect", *ids],
                          "project_container_inspect", 60))
    indexed = {x["Config"]["Labels"].get("com.docker.compose.service"): x
               for x in data}
    require(set(indexed) == EXPECTED_SERVICES and len(data) == 10,
            "unexpected radio project container ownership")
    return indexed


def all_running():
    return all(obj["State"]["Running"] for obj in container_map().values())


def check_model(host):
    model = json.loads(run(compose() + ["config", "--format", "json"],
                           "render_compose", 90))
    require(model.get("name") == PROJECT, "unexpected radio Compose project")
    services = model.get("services", {})
    require(set(services) == EXPECTED_SERVICES,
            "unexpected radio Compose services")
    published = {
        (svc, str(p.get("host_ip", "")), int(p.get("published", -1)),
         int(p.get("target", -1)), p.get("protocol", "tcp"))
        for svc, obj in services.items() for p in obj.get("ports", [])
    }
    require(published == {(svc, host, public, private, "tcp")
                          for svc, (public, private) in PORTS.items()},
            "unexpected radio Compose port bindings")
    require(set(model.get("volumes", {})) ==
            {"postgres_data", "libretime_storage", "libretime_playout"},
            "unexpected radio Compose data volumes")
    require(set(model.get("networks", {})) == {"default"},
            "unexpected radio Compose networks")


def inspect_ports(host):
    containers = container_map()
    if not all(x["State"]["Running"] for x in containers.values()):
        return False
    for svc, (public, private) in PORTS.items():
        bindings = containers[svc]["HostConfig"]["PortBindings"]
        entry = bindings.get(str(private) + "/tcp", [])
        if not (len(entry) == 1 and
                entry[0].get("HostIp") == host and
                entry[0].get("HostPort") == str(public)):
            return False
    return True


def tcp_ready(host, port):
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def http_ready(host, port, path):
    try:
        result = OPENER.open("http://" + host + ":" + str(port) + path,
                             timeout=3)
        with result as response:
            return 200 <= response.status < 400
    except Exception:
        return False


def ready(host, timeout=90):
    # Current observed failure is an exited Liquidsoap container and HTTP 502.
    # Check actual process and endpoints, not simply Docker command exit 0.
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if (inspect_ports(host) and tcp_ready(host, 8605) and
                http_ready(host, 8700, "/") and
                http_ready(host, 8600, "/status-json.xsl")):
            return True
        time.sleep(3)
    return False


def write_same_inode(content):
    # Vendor bind-mounts an existing runtime file. Atomic path replacement
    # would leave a running container reading a stale inode.
    with open(OVERRIDE, "r+", encoding="utf-8") as file:
        file.seek(0)
        file.write(content)
        file.truncate()
        file.flush()
        os.fsync(file.fileno())


def await_readiness(check, seconds=60):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(2)
    return False


def restart_only_radio_ports(stage, host):
    # Start the output first, then DJ Show Source, then UI. This avoids
    # starting Liquidsoap while its destination Icecast is still unavailable.
    for service in RADIO:
        run(compose() + ["up", "-d", "--no-deps", "--no-build",
                         "--pull", "never", "--force-recreate", service],
            stage + "_" + service, 240)
        if service == "icecast":
            require(await_readiness(
                lambda: http_ready(host, 8600, "/status-json.xsl")),
                stage + "_icecast: HTTP did not become ready")
        if service == "liquidsoap":
            require(await_readiness(lambda: tcp_ready(host, 8605)),
                    stage + "_liquidsoap: Show Source did not become ready")


def recover_loopback(original):
    write_same_inode(original)
    check_model("127.0.0.1")
    try:
        restart_only_radio_ports("rollback_recreate", "127.0.0.1")
    except Blocked as exc:
        print("RRN05_ROLLBACK_RECREATE=" + str(exc), flush=True)
    # If the original script's bug recurs, revive only the already-existing
    # radio Liquidsoap, as accepted once in the owner-provided recovery.
    containers = container_map()
    if not containers["liquidsoap"]["State"]["Running"]:
        run(["docker", "start", containers["liquidsoap"]["Id"]],
            "rollback_start_liquidsoap", 45)
    if not http_ready("127.0.0.1", 8700, "/"):
        run(["docker", "restart", "-t", "15",
             containers["legacy"]["Id"], containers["nginx"]["Id"]],
            "rollback_restart_radio_ui", 90)
    require(ready("127.0.0.1", 75),
            "rollback did not restore all ten radio containers and HTTP/TCP")
    print("RRN05_ROLLBACK=HEALTH_CONFIRMED", flush=True)


def apply():
    require(os.geteuid() == 0, "Run as root on the already approved radio Host")
    require(RUNTIME.is_dir() and not RUNTIME.is_symlink(),
            "radio runtime directory unavailable or symlinked")
    require(PRIVATE.is_dir() and not PRIVATE.is_symlink(),
            "radio private config directory unavailable or symlinked")
    for file in (OVERRIDE, RUNTIME / "docker-compose.yml",
                 PRIVATE / "compose.env", PRIVATE / "config.yml"):
        require(file.is_file() and not file.is_symlink(),
                "required radio file unavailable/symlinked")
    require((PRIVATE / "compose.env").stat().st_mode & 0o077 == 0,
            "private radio .env has unsafe permissions")
    require(BACKUPS.is_dir() and not BACKUPS.is_symlink() and
            BACKUPS.stat().st_uid == 0 and
            BACKUPS.stat().st_mode & 0o077 == 0,
            "root-only radio backup directory unavailable/unsafe")
    ip_addrs = json.loads(run(["ip", "-j", "-4", "addr", "show"],
                             "check_host_lan_ip", 30))
    require(any(item.get("local") == LAN
                for interface in ip_addrs
                for item in interface.get("addr_info", [])),
            "host does not own requested radio LAN IP")
    original = OVERRIDE.read_text(encoding="utf-8")
    replacements = {
        "127.0.0.1:8600:8000": LAN + ":8600:8000",
        "127.0.0.1:8605:8002": LAN + ":8605:8002",
        "127.0.0.1:8700:8080": LAN + ":8700:8080",
    }
    if all(new in original for new in replacements.values()):
        check_model(LAN)
        require(ready(LAN, 15),
                "LAN mappings already present but radio endpoints not healthy")
        print("RRN05_LAN_BINDINGS=ALREADY_APPLIED")
        return
    require(all(original.count(old) == 1 and new not in original
                for old, new in replacements.items()),
            "radio config differs from expected loopback state")
    check_model("127.0.0.1")
    require(ready("127.0.0.1", 15),
            "existing radio baseline not healthy; refusing new outage")
    updated = original
    for old, new in replacements.items():
        updated = updated.replace(old, new, 1)

    # Verify desired address isn't already occupied before touching files.
    listeners = run(["ss", "-H", "-ltn"], "check_lan_port_conflicts", 30)
    for p in PORTS.values():
        outer = p[0]
        for row in listeners.splitlines():
            columns = row.split()
            if len(columns) < 4:
                continue
            addr = columns[3]
            if any(addr.endswith(":" + str(outer)) and
                   addr.startswith(prefix)
                   for prefix in (LAN + ":", "0.0.0.0:", "*:", "[::]:")):
                raise Blocked("radio LAN destination port occupied: " +
                              str(outer))
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUPS / ("lan-port-bindings-" + now + ".original.yml")
    fd = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(original)
        file.flush()
        os.fsync(file.fileno())
    print("RRN05_ORIGINAL_OVERRIDE_BACKUP=" + str(backup), flush=True)

    stage = "write_override"
    try:
        write_same_inode(updated)
        stage = "validate_new_compose"
        check_model(LAN)
        print("RRN05_COMPOSE_VALIDATED=PASS", flush=True)
        stage = "recreate_radio_port_services"
        restart_only_radio_ports(stage, LAN)
        stage = "confirm_lan_radio_runtime"
        require(ready(LAN, 90), "radio LAN services did not become healthy")
    except Exception as err:
        print("RRN05_FAILED_STAGE=" + stage, flush=True)
        print("RRN05_ORIGINAL_ERROR=" + str(err), flush=True)
        try:
            recover_loopback(original)
        except Exception as rollback_err:
            print("RRN05_ROLLBACK=NEEDS_OPERATOR_ATTENTION", flush=True)
            print("RRN05_ROLLBACK_ERROR=" + str(rollback_err), flush=True)
        raise Blocked("LAN change failed; see stage and rollback status") from None

    print("RRN05_LAN_BINDINGS=PASS")
    print("radio_containers_running=10")
    print("icecast_listener=http://" + LAN + ":8600/main.mp3")
    print("show_source=" + LAN + ":8605/show")
    print("libretime_ui=http://" + LAN + ":8700")
    print("public_urls_in_private_config=UNCHANGED")
    print("libretime_audio=NOT_RETESTED")
    print("mikrotik_dstnat=UNCHANGED_POSSIBLE_WAN_EXPOSURE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", required=True)
    parser.parse_args()
    try:
        apply()
    except Blocked as exc:
        print("RRN05_STATUS=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(2)
