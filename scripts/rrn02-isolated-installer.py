#!/usr/bin/env python3
"""RRN-02: isolated, pinned LibreTime 4.5.0 + bundled Icecast 2.4.4.
--prepare stages new runtime/config only; --apply migrates DB and starts radio
services only. Do not use for public launch, DNS or shared-host changes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import urllib.request

PROJECT = "rcat_radio_network"
RUNTIME = Path("/opt/rcat-libretime-runtime")
PRIVATE = Path("/etc/rcat-radio-network")
LEGACY = Path("/opt/rcat-radio-network")
SOURCES = {
    "docker-compose.yml": (
        "https://raw.githubusercontent.com/libretime/libretime/f429339bfc6ef13e125f1251bddf9e32bb822231/docker-compose.yml",
        "d23fb059fc9097a825dd458f6ab2ff814e9b6de7"
    ),
    "config.template.yml": (
        "https://raw.githubusercontent.com/libretime/libretime/f429339bfc6ef13e125f1251bddf9e32bb822231/docker/config.template.yml",
        "0551fc6739b18116efdd53468ae64bb00e3b07da"
    ),
    "radio.override.yml": (
        "https://raw.githubusercontent.com/yiwssx/rcat-radio-network/e449c918e95715d64fd159025850634aeb3793ba/testing/compose.feasibility.override.yml",
        "b267f0efb799855bc07d16a9e7c46238121c61c2"
    ),
}
PASSWORDS = ("POSTGRES_PASSWORD", "RABBITMQ_DEFAULT_PASS",
             "ICECAST_SOURCE_PASSWORD", "ICECAST_ADMIN_PASSWORD",
             "ICECAST_RELAY_PASSWORD")
IMAGES = {
    "postgres": "postgres:15", "rabbitmq": "rabbitmq:3.13-alpine",
    "playout": "ghcr.io/libretime/libretime-playout:4.5.0",
    "liquidsoap": "ghcr.io/libretime/libretime-playout:4.5.0",
    "analyzer": "ghcr.io/libretime/libretime-analyzer:4.5.0",
    "worker": "ghcr.io/libretime/libretime-worker:4.5.0",
    "api": "ghcr.io/libretime/libretime-api:4.5.0",
    "legacy": "ghcr.io/libretime/libretime-legacy:4.5.0",
    "nginx": "ghcr.io/libretime/libretime-nginx:4.5.0",
    "icecast": "ghcr.io/libretime/icecast:2.4.4",
}
PORTS = {("icecast", "127.0.0.1", "8600", 8000, "tcp"),
         ("liquidsoap", "127.0.0.1", "8605", 8002, "tcp"),
         ("nginx", "127.0.0.1", "8700", 8080, "tcp")}
DATA = {"postgres_data", "libretime_storage", "libretime_playout"}


class Blocked(Exception):
    pass


def check(ok, message):
    if not ok:
        raise Blocked(message)


def command(args, timeout=180, cwd=None):
    # Do not inherit shell COMPOSE_*, POSTGRES_*, RABBITMQ_*, ICECAST_*,
    # or LIBRETIME_* variables: they can override our private env-file.
    # Restrict Docker to the host-local default context (never a remote engine).
    safe_env = {
        "PATH": os.environ.get(
            "PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ),
        "HOME": "/root",
        "DOCKER_CONTEXT": "default",
    }
    try:
        x = subprocess.run(
            args, cwd=cwd, text=True, capture_output=True,
            timeout=timeout, env=safe_env,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Blocked("Radio-only command unavailable or timed out") from e
    # Compose output can contain resolved secrets. Never print its stdout/stderr.
    check(x.returncode == 0, "Radio-only command failed: " + args[0] + " " + args[1])
    return x.stdout


def download(url, blob):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "rcat-rrn02/1"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(100001)
    except OSError as e:
        raise Blocked("Pinned source download failed") from e
    check(len(data) <= 100000, "Pinned source too large")
    check(hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() == blob,
          "Pinned Git blob SHA mismatch")
    return data.decode("utf-8")


def base():
    check(os.geteuid() == 0, "Run with sudo on approved RCAT server")
    check(LEGACY.is_dir() and not LEGACY.is_symlink(), "Legacy checkout not as expected")
    check(not RUNTIME.is_symlink() and not PRIVATE.is_symlink(),
          "Unexpected symlink in radio runtime paths")
    version = command(["docker", "compose", "version", "--short"], 20)
    check(version.strip() == "5.7.0" or version.strip().startswith("v5."),
          "Compose version differs from approved v5 preflight; review before proceeding")


def radio_absent():
    filt = "label=com.docker.compose.project=" + PROJECT
    for args in (["docker", "ps", "-aq", "--filter", filt],
                 ["docker", "volume", "ls", "-q", "--filter", filt],
                 ["docker", "network", "ls", "-q", "--filter", filt]):
        check(not command(args, 30).strip(), "Radio Compose resources already exist")


def ports_free():
    listeners = command(["ss", "-H", "-ltn"], 20)
    for line in listeners.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            check(not any(parts[3].endswith(":" + p) for p in ("8600", "8605", "8700")),
                  "A proposed radio-only port is now occupied")


def replace_once(content, old, new):
    check(content.count(old) == 1, "Pinned config template differs from expected structure")
    return content.replace(old, new)


def make_config(template, env):
    result = template
    for name in PASSWORDS[:4]:
        token = "${" + name + "}"
        check(token in result, "Required LibreTime variable not found")
        result = result.replace(token, env[name])
    check("${" not in result, "Unexpanded LibreTime secret")
    result = replace_once(result,
        "  public_url:\n  # The internal API authentication key.",
        '  public_url: "http://127.0.0.1:8700"\n  # The internal API authentication key.')
    result = replace_once(result,
        "  api_key:\n  # The Django API secret key.",
        '  api_key: "' + secrets.token_hex(32) + '"\n  # The Django API secret key.')
    result = replace_once(result,
        "  secret_key:\n\n  # List of origins",
        '  secret_key: "' + secrets.token_hex(32) + '"\n\n  # List of origins')
    result = replace_once(result, "  timezone: UTC", "  timezone: Asia/Bangkok")
    result = replace_once(result,
        "      # The default Icecast output stream\n      - <<: *default_icecast_output\n"
        "        enabled: true\n        public_url:\n        mount: main\n"
        "        audio:\n          format: ogg\n          bitrate: 256",
        '      # The default Icecast output stream\n      - <<: *default_icecast_output\n'
        '        enabled: true\n        public_url: "http://127.0.0.1:8600/main.mp3"\n'
        '        mount: main.mp3\n        audio:\n          format: mp3\n          bitrate: 128')
    check("main.mp3" in result and "format: mp3\n          bitrate: 128" in result,
          "Expected MP3/128 output not configured")
    return result


def compose():
    return ["docker", "compose", "--env-file", str(PRIVATE / "compose.env"),
            "-p", PROJECT, "-f", str(RUNTIME / "docker-compose.yml"),
            "-f", str(RUNTIME / "radio.override.yml")]


def validate():
    raw = command(compose() + ["config", "--format", "json"], 60, RUNTIME)
    try:
        data = json.loads(raw)
    except ValueError as e:
        raise Blocked("Merged Compose is not JSON") from e
    check(data.get("name") == PROJECT, "Wrong Compose project")
    services = data.get("services", {})
    check(set(services) == set(IMAGES), "Unexpected service names")
    ports = set()
    for name, image in IMAGES.items():
        obj = services[name]
        check(obj.get("image") == image, "Unexpected image: " + name)
        check(set(obj.get("networks", {})) == {"default"}, "Non-radio network: " + name)
        for port in obj.get("ports", []):
            ports.add((name, str(port.get("host_ip", "")),
                       str(port.get("published", "")), int(port.get("target", -1)),
                       str(port.get("protocol", "tcp"))))
        for volume in obj.get("volumes", []):
            if volume.get("type") == "bind":
                check(volume.get("source") == str(PRIVATE / "config.yml")
                      and volume.get("target") == "/etc/libretime/config.yml"
                      and volume.get("read_only") is True,
                      "Unsafe or unexpected bind mount")
    check(ports == PORTS, "Unexpected published Docker host ports")
    nets = data.get("networks", {})
    check(set(nets) == {"default"}
          and nets["default"].get("name") == PROJECT + "_default"
          and not nets["default"].get("external", False), "Unexpected Docker network")
    vols = data.get("volumes", {})
    check(set(vols) == DATA, "Unexpected named volumes")
    for name in DATA:
        check(vols[name].get("name") == PROJECT + "_" + name
              and not vols[name].get("external", False),
              "Non-radio volume found")


def write_file(path, content, mode):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(path, mode)


def prepare():
    base()
    check(not RUNTIME.exists() and not PRIVATE.exists(),
          "Separate radio paths already exist; refusing overwrite")
    radio_absent()
    ports_free()
    sources = {name: download(url, blob) for name, (url, blob) in SOURCES.items()}
    env = {"LIBRETIME_VERSION": "4.5.0",
           "LIBRETIME_CONFIG_FILEPATH": str(PRIVATE / "config.yml")}
    env.update({name: secrets.token_hex(32) for name in PASSWORDS})
    config = make_config(sources["config.template.yml"], env)
    # The existing /opt/rcat-radio-network (with legacy AzuraCast .env) is untouched.
    RUNTIME.mkdir(mode=0o755)
    PRIVATE.mkdir(mode=0o700)
    for name in ("docker-compose.yml", "radio.override.yml"):
        write_file(RUNTIME / name, sources[name], 0o644)
    write_file(PRIVATE / "compose.env",
               "".join(f"{k}={v}\n" for k, v in env.items()), 0o600)
    # Private parent directory is root-only. Container bind needs readable config.
    write_file(PRIVATE / "config.yml", config, 0o644)
    validate()
    print("RRN02_STAGE=PASS")
    print("runtime=/opt/rcat-libretime-runtime")
    print("secrets_dir=/etc/rcat-radio-network")
    print("project=rcat_radio_network services=10")
    print("mount=main.mp3 format=mp3 bitrate=128")
    print("ports=127.0.0.1:8600/8605/8700")
    print("legacy_checkout_untouched=true")
    print("containers_started=false")


def apply():
    base()
    check(RUNTIME.is_dir() and PRIVATE.is_dir(), "Radio runtime has not been prepared")
    check(PRIVATE.stat().st_mode & 0o777 == 0o700,
          "Private secrets directory does not have mode 0700")
    check((PRIVATE / "compose.env").is_file()
          and (PRIVATE / "compose.env").stat().st_mode & 0o077 == 0,
          "Private compose.env missing or too permissive")
    ports_free()
    radio_absent()
    validate()
    args = compose()
    print("RRN02_PHASE=postgres_rabbitmq")
    command(args + ["up", "-d", "--wait", "postgres", "rabbitmq"], 450, RUNTIME)
    print("RRN02_PHASE=database_migration")
    command(args + ["run", "--rm", "api", "libretime-api", "migrate"], 450, RUNTIME)
    print("RRN02_PHASE=start_radio_only_stack")
    command(args + ["up", "-d"], 600, RUNTIME)
    print("RRN02_DEPLOY=STARTED")
    print("ui=http://127.0.0.1:8700")
    print("stream=http://127.0.0.1:8600/main.mp3")
    print("admin_default_password=MUST_CHANGE_BEFORE_EXPOSURE")
    print("public_dns_proxy_firewall=UNCHANGED")
    print("audio_acceptance=NOT_TESTED")


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--install", action="store_true")
    args = p.parse_args()
    if args.prepare or args.install:
        prepare()
    if args.apply or args.install:
        apply()


if __name__ == "__main__":
    try:
        main()
    except (Blocked, OSError, ValueError) as error:
        print("RRN02_STATUS=BLOCKED: " + str(error), file=sys.stderr)
        print("Do not remove existing data or run host-wide Docker cleanup.", file=sys.stderr)
        sys.exit(2)
