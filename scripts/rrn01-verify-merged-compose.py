#!/usr/bin/env python3
"""RRN-01: non-starting Compose merge validation for the approved RCAT radio stack.

Does not connect to the Docker daemon, start/pull containers, use sudo, read
production credentials, or modify any existing RCAT application directory.
Downloads two immutable public GitHub source files into a disposable temp dir
and validates Git blob identities before parsing with the installed Compose CLI.
All credentials supplied to Docker Compose are synthetic, for validation only.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request

BASE_URL = (
    "https://raw.githubusercontent.com/libretime/libretime/"
    "f429339bfc6ef13e125f1251bddf9e32bb822231/docker-compose.yml"
)
BASE_BLOB = "d23fb059fc9097a825dd458f6ab2ff814e9b6de7"
OVERRIDE_URL = (
    "https://raw.githubusercontent.com/yiwssx/rcat-radio-network/"
    "e449c918e95715d64fd159025850634aeb3793ba/"
    "testing/compose.feasibility.override.yml"
)
OVERRIDE_BLOB = "b267f0efb799855bc07d16a9e7c46238121c61c2"
PROJECT = "rcat_radio_network"

EXPECTED_IMAGES = {
    "postgres": "postgres:15",
    "rabbitmq": "rabbitmq:3.13-alpine",
    "playout": "ghcr.io/libretime/libretime-playout:4.5.0",
    "liquidsoap": "ghcr.io/libretime/libretime-playout:4.5.0",
    "analyzer": "ghcr.io/libretime/libretime-analyzer:4.5.0",
    "worker": "ghcr.io/libretime/libretime-worker:4.5.0",
    "api": "ghcr.io/libretime/libretime-api:4.5.0",
    "legacy": "ghcr.io/libretime/libretime-legacy:4.5.0",
    "nginx": "ghcr.io/libretime/libretime-nginx:4.5.0",
    "icecast": "ghcr.io/libretime/icecast:2.4.4",
}
EXPECTED_PORTS = {
    ("nginx", "127.0.0.1", "8700", 8080, "tcp"),
    ("liquidsoap", "127.0.0.1", "8605", 8002, "tcp"),
    ("icecast", "127.0.0.1", "8600", 8000, "tcp"),
}
EXPECTED_VOLUMES = {"postgres_data", "libretime_storage", "libretime_playout"}
DUMMY = "RRN01_VALIDATION_ONLY_NOT_A_REAL_SECRET"


class PreflightFailure(Exception):
    pass


def require(condition, description):
    if not condition:
        raise PreflightFailure(description)


def fetch_pinned(url, expected_blob, dest):
    request = urllib.request.Request(url, headers={"User-Agent": "rcat-rrn01-preflight/1"})
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read(100_000)
        require(len(raw) < 100_000, "Fetched YAML exceeds maximum expected size")
    header = f"blob {len(raw)}\0".encode("ascii")
    actual_blob = hashlib.sha1(header + raw).hexdigest()
    require(actual_blob == expected_blob, "Pinned source file integrity mismatch")
    dest.write_bytes(raw)


def validate(data):
    require(data.get("name") == PROJECT, "Compose project name differs from radio-only project")
    services = data.get("services", {})
    require(set(services) == set(EXPECTED_IMAGES), "Unexpected or missing Compose service")
    for name, image in EXPECTED_IMAGES.items():
        require(services[name].get("image") == image, f"Unexpected image in {name}")
    ports = set()
    for name, svc in services.items():
        for p in svc.get("ports", []):
            require(isinstance(p, dict), f"Unexpected port format in {name}")
            ports.add((
                name, str(p.get("host_ip", "")), str(p.get("published", "")),
                int(p.get("target", -1)), str(p.get("protocol", "tcp"))
            ))
        # Any additional network attachment must be explicitly reviewed.
        attachments = svc.get("networks", {})
        require(
            isinstance(attachments, (dict, list)) and set(attachments) == {"default"},
            f"Unexpected network attached to {name}"
        )
        for mount in svc.get("volumes", []):
            require(
                mount.get("type") in {"bind", "volume"},
                f"Unexpected mount type in {name}"
            )
            if mount.get("type") == "bind":
                require(
                    mount.get("target") == "/etc/libretime/config.yml",
                    f"Unexpected host bind mount in {name}"
                )
    require(ports == EXPECTED_PORTS, "Host port mapping differs from three loopback-only bindings")
    networks = data.get("networks", {})
    require(set(networks) == {"default"}, "Unexpected external/shared network")
    require(
        networks["default"].get("name") == PROJECT + "_default"
        and not networks["default"].get("external", False),
        "Radio network is not isolated by project name"
    )
    volumes = data.get("volumes", {})
    require(set(volumes) == EXPECTED_VOLUMES, "Unexpected or missing radio data volumes")
    for name in EXPECTED_VOLUMES:
        require(
            volumes[name].get("name") == PROJECT + "_" + name
            and not volumes[name].get("external", False),
            f"Radio data volume {name} is not project-scoped"
        )


def main():
    require(sys.version_info >= (3, 10), "Python 3.10+ required")
    with tempfile.TemporaryDirectory(prefix="rrn01-compose-") as folder:
        tmp = Path(folder)
        base, override = tmp / "upstream.yml", tmp / "radio.override.yml"
        fetch_pinned(BASE_URL, BASE_BLOB, base)
        fetch_pinned(OVERRIDE_URL, OVERRIDE_BLOB, override)
        # Not the real config. It exists only so Compose can resolve the bind path.
        (tmp / "config.yml").write_text("# Synthetic bind target for a read-only Compose render\n")
        env = {
            "HOME": os.environ.get("HOME", str(tmp)),
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "LIBRETIME_CONFIG_FILEPATH": str(tmp / "config.yml"),
            "LIBRETIME_VERSION": "4.5.0",
            "POSTGRES_PASSWORD": DUMMY,
            "RABBITMQ_DEFAULT_PASS": DUMMY,
            "ICECAST_SOURCE_PASSWORD": DUMMY,
            "ICECAST_ADMIN_PASSWORD": DUMMY,
            "ICECAST_RELAY_PASSWORD": DUMMY,
        }
        command = [
            "docker", "compose", "--project-directory", str(tmp),
            "-p", PROJECT, "-f", str(base), "-f", str(override),
            "config", "--format", "json"
        ]
        try:
            output = subprocess.run(
                command, cwd=tmp, env=env, capture_output=True,
                text=True, timeout=45, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PreflightFailure("Docker Compose CLI unavailable or unresponsive") from exc
        require(
            output.returncode == 0,
            "Docker Compose failed to render the pinned synthetic configuration"
            + (": " + output.stderr.strip()[:350] if output.stderr.strip() else "")
        )
        try:
            parsed = json.loads(output.stdout)
        except json.JSONDecodeError as exc:
            raise PreflightFailure("Docker Compose did not return JSON") from exc
        validate(parsed)
    print("RRN01_COMPOSE_STATUS=PASS")
    print("project=rcat_radio_network")
    print("upstream_libretime=4.5.0 pinned_verified")
    print("icecast=2.4.4 image_pinned")
    print("services=10 networks=1 data_volumes=3")
    print("ports=127.0.0.1:8600->8000,127.0.0.1:8605->8002,127.0.0.1:8700->8080")
    print("secrets=synthetic_only")
    print("containers_started=false")
    print("scope=structural_merge_only; real_secret_config_and_audio_untested")


if __name__ == "__main__":
    try:
        main()
    except (PreflightFailure, OSError, ValueError) as exc:
        print(f"RRN01_COMPOSE_STATUS=BLOCKED: {exc}", file=sys.stderr)
        sys.exit(2)
