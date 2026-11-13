#!/usr/bin/env python3
"""RRN-06: radio-only cold backup with an explicit short-outage gate.

--plan: inspect the 10 radio containers and 3 radio volumes, without changes.
--backup --approve-radio-outage: stop ONLY the radio Compose project, archive
its three local volumes plus private config/Compose files, then start the project.
Neither mode touches other RCAT projects, host Docker Engine, DNS, or proxy.
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile

PROJECT = "rcat_radio_network"
RUNTIME = Path("/opt/rcat-libretime-runtime")
PRIVATE = Path("/etc/rcat-radio-network")
BACKUPS = Path("/var/backups/rcat-radio-network")
SERVICES = {
    "postgres", "rabbitmq", "playout", "liquidsoap", "analyzer",
    "worker", "api", "legacy", "nginx", "icecast",
}
VOLUMES = ("postgres_data", "libretime_storage", "libretime_playout")


class Stop(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Stop(message)


def local_command(args, timeout=90):
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": "/root",
        "DOCKER_CONTEXT": "default",
    }
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=timeout, env=env, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Stop("Radio-only command failed to launch or timed out") from exc
    # Do not print stdout/stderr from Docker: it can contain credentials.
    require(result.returncode == 0, "Radio-only command failed: " + args[0])
    return result.stdout.strip()


def compose():
    return [
        "docker", "compose", "--project-directory", str(RUNTIME),
        "--env-file", str(PRIVATE / "compose.env"), "-p", PROJECT,
        "-f", str(RUNTIME / "docker-compose.yml"),
        "-f", str(RUNTIME / "radio.override.yml"),
    ]


def check_private_sources():
    require(os.geteuid() == 0, "Root access is required to inspect radio volumes")
    for p in (RUNTIME, PRIVATE):
        require(p.is_dir() and not p.is_symlink(), "Radio runtime/private dir is missing or a symlink")
        require(p.resolve() not in (Path("/opt/rcat-radio-network"),),
                "Refusing legacy radio checkout")
    require((PRIVATE.stat().st_mode & 0o077) == 0,
            "Private radio config directory has unsafe permissions")
    for p in (PRIVATE / "compose.env", PRIVATE / "config.yml",
              RUNTIME / "docker-compose.yml", RUNTIME / "radio.override.yml"):
        require(p.is_file() and not p.is_symlink(), "Expected radio file unavailable or symlink")
    require((PRIVATE / "compose.env").stat().st_mode & 0o077 == 0,
            "Radio env file has unsafe permissions")


def inspect_radio():
    check_private_sources()
    # The live station must have exactly the previously accepted 10 containers,
    # all running; fail closed rather than restart an unknown partial project.
    ids = local_command([
        "docker", "ps", "-aq",
        "--filter", "label=com.docker.compose.project=" + PROJECT,
    ], 30).splitlines()
    require(len(ids) == len(SERVICES), "Expected exactly 10 radio project containers")
    containers = json.loads(local_command(["docker", "inspect", *ids], 45))
    observed = set()
    for item in containers:
        labels = item["Config"]["Labels"]
        require(labels.get("com.docker.compose.project") == PROJECT,
                "Container label mismatch")
        service = labels.get("com.docker.compose.service")
        require(service in SERVICES and service not in observed,
                "Unexpected or duplicate radio service")
        require(item["State"]["Running"], "A radio service was already stopped")
        observed.add(service)
    require(observed == SERVICES, "Not all expected radio services are running")

    # Restrict the backup to the exact Compose-owned Docker local volumes.
    # Do not traverse host Docker storage or other projects.
    docker_root = Path(local_command(
        ["docker", "info", "--format", "{{.DockerRootDir}}"], 30
    )).resolve()
    paths = {}
    for name in VOLUMES:
        full = PROJECT + "_" + name
        record = json.loads(local_command(
            ["docker", "volume", "inspect", full], 30
        ))[0]
        require(record.get("Name") == full and record.get("Driver") == "local",
                "Unexpected radio volume driver/name")
        labels = record.get("Labels") or {}
        require(labels.get("com.docker.compose.project") == PROJECT,
                "Radio volume not labeled as project-owned")
        raw = Path(record.get("Mountpoint", ""))
        require(raw.is_dir() and not raw.is_symlink(), "Radio volume mount is missing/symlink")
        expected = docker_root / "volumes" / full / "_data"
        require(raw.resolve() == expected.resolve(),
                "Radio volume outside expected local Docker storage")
        paths[name] = raw
    return paths



def backup_capacity(paths):
    # Check capacity before stopping live radio, using conservative logical
    # bytes (uncompressed), plus a 10% cushion and one extra GiB.
    parent = BACKUPS.parent
    require(parent.is_dir() and not parent.is_symlink(),
            "Expected root-owned /var/backups parent directory not available")
    sources = [str(PRIVATE), str(RUNTIME)] + [str(paths[n]) for n in VOLUMES]
    report = local_command(["du", "-sb", *sources], 180)
    lines = report.splitlines()
    require(len(lines) == len(sources), "Cannot estimate radio backup source sizes")
    try:
        bytes_needed = sum(int(line.split()[0]) for line in lines)
    except (IndexError, ValueError) as exc:
        raise Stop("Unable to parse radio-only backup source sizes") from exc
    filesystem = os.statvfs(parent)
    bytes_free = filesystem.f_bavail * filesystem.f_frsize
    margin = bytes_needed // 10 + 1024 ** 3
    require(bytes_free >= bytes_needed + margin,
            "Not enough free space for conservative local radio backup")
    return bytes_needed, bytes_free

def ensure_backup_directory():
    require(not BACKUPS.is_symlink(), "Backup directory is a symlink")
    if not BACKUPS.exists():
        BACKUPS.mkdir(mode=0o700, parents=False)
    require(BACKUPS.is_dir() and BACKUPS.stat().st_uid == 0,
            "Backup directory must be root-owned")
    require((BACKUPS.stat().st_mode & 0o077) == 0,
            "Backup directory must be owner-only (0700)")


def create_archive(paths):
    ensure_backup_directory()
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = "rcat_radio_network-" + now + ".tar.gz"
    archive = BACKUPS / filename
    partial = BACKUPS / (filename + ".partial")
    require(not archive.exists() and not partial.exists(),
            "Radio backup filename already exists; refusing overwrite")
    try:
        fd = os.open(partial, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            with tarfile.open(fileobj=stream, mode="w:gz", dereference=False) as tar:
                manifest = {
                    "schema": 1, "project": PROJECT, "created_utc": now,
                    "mode": "cold_backup", "volumes": list(VOLUMES),
                    "includes": ["private_config", "runtime_compose", "three_volumes"],
                }
                data = (json.dumps(manifest, sort_keys=True) + "\n").encode()
                info = tarfile.TarInfo("manifest.json")
                info.size = len(data)
                info.mode = 0o600
                tar.addfile(info, io.BytesIO(data))
                tar.add(PRIVATE, arcname="private/rcat-radio-network")
                tar.add(RUNTIME / "docker-compose.yml", arcname="runtime/docker-compose.yml")
                tar.add(RUNTIME / "radio.override.yml", arcname="runtime/radio.override.yml")
                for name in VOLUMES:
                    tar.add(paths[name], arcname="volumes/" + name)
            stream.flush()
            os.fsync(stream.fileno())
        digest = hashlib.sha256()
        with open(partial, "rb") as stream:
            for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                digest.update(block)
        checksum = digest.hexdigest()
        os.replace(partial, archive)
        sidecar = BACKUPS / (filename + ".sha256")
        with os.fdopen(os.open(sidecar, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600),
                       "w", encoding="utf-8") as stream:
            stream.write(checksum + "  " + filename + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return archive
    finally:
        if partial.exists():
            partial.unlink()


def cold_backup(paths):
    # This is an intentional radio-only outage. The caller MUST explicitly
    # authorize it; --plan never reaches this function.
    stopped_attempted = False
    archived = None
    restore_error = None
    try:
        stopped_attempted = True
        local_command(compose() + ["stop", "-t", "45"], 180)
        remaining = local_command([
            "docker", "ps", "-q",
            "--filter", "label=com.docker.compose.project=" + PROJECT,
        ], 30)
        require(not remaining, "Radio project did not fully stop; backup aborted")
        archived = create_archive(paths)
    finally:
        if stopped_attempted:
            try:
                # All ten services were running at entry; start only the
                # already-created containers, never up/pull/create new ones.
                local_command(compose() + ["start"], 240)
            except Stop:
                restore_error = True
    require(not restore_error, "RADIO RESTART NEEDS MANUAL ATTENTION; backup may exist")
    require(archived is not None, "No complete backup archive created")
    print("RRN06_BACKUP=PASS")
    print("archive=" + str(archived))
    print("sha256_sidecar=" + str(archived) + ".sha256")
    print("scope=three_radio_volumes+private_config+radio_compose")
    print("radio_compose_start=COMMAND_SUCCEEDED")
    print("live_audio_after_restart=NOT_RETESTED")
    print("offsite_copy=NOT_CONFIGURED")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--backup", action="store_true")
    parser.add_argument("--approve-radio-outage", action="store_true")
    args = parser.parse_args()
    if args.backup:
        require(args.approve_radio_outage,
                "Backup stops only the radio project; explicit radio-outage approval required")
    else:
        require(not args.approve_radio_outage, "Outage approval only applies to --backup")
    paths = inspect_radio()
    estimated_bytes, free_bytes = backup_capacity(paths)
    if args.plan:
        print("RRN06_PLAN=PASS")
        print("estimated_uncompressed_bytes=" + str(estimated_bytes))
        print("backup_filesystem_available_bytes=" + str(free_bytes))
        print("project=" + PROJECT + " running_containers=10")
        print("radio_local_volumes=3")
        print("private_sources=present")
        print("backup_destination=" + str(BACKUPS))
        print("radio_outage_required_for_consistent_backup=true")
        print("docker_operations=READ_ONLY")
    else:
        cold_backup(paths)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        main()
    except (Stop, OSError, ValueError, KeyError, IndexError,
            json.JSONDecodeError) as exc:
        print("RRN06_STATUS=BLOCKED: " + str(exc), file=sys.stderr)
        print("No other RCAT projects, Docker networks or volumes were intentionally changed.",
              file=sys.stderr)
        sys.exit(2)
