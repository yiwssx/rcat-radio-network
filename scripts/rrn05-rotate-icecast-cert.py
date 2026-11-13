#!/usr/bin/env python3
"""RRN-05: root-executed, radio-only Icecast certificate renewal receiver.

Expected private SSH staging file: /home/rcat_iot_admin/.rrn05-radio-cert-next.pem
On success, recreates ONLY Icecast so 2.4.4 loads the new certificate.
This is an operational certificate deployment step, not a music UAT.
"""
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

DOMAIN = "radio.rcat.ac.th"
LAN = "10.10.1.100"
STAGING = Path("/home/rcat_iot_admin/.rrn05-radio-cert-next.pem")
DEST = Path("/etc/rcat-radio-network/icecast-bundle.pem")
BACKUPS = Path("/var/backups/rcat-radio-network")
RUNTIME = Path("/opt/rcat-libretime-runtime")
ENV = Path("/etc/rcat-radio-network/compose.env")
OVERRIDE = RUNTIME / "radio.override.yml"
PROJECT = "rcat_radio_network"
CONTAINER = "rcat_radio_network-icecast-1"


class Blocked(Exception):
    pass


def must(ok, reason):
    if not ok:
        raise Blocked(reason)


def run(argv, timeout=120):
    try:
        result = subprocess.run(argv, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise Blocked("command failed or timed out: " + argv[0]) from None
    must(result.returncode == 0, "command failed: " + argv[0])
    return result.stdout.decode(errors="replace").strip()


def compose():
    run(["docker", "compose", "--project-directory", str(RUNTIME),
         "--env-file", str(ENV), "-p", PROJECT,
         "-f", str(RUNTIME / "docker-compose.yml"), "-f", str(OVERRIDE),
         "up", "-d", "--no-deps", "--no-build", "--pull", "never",
         "--force-recreate", "icecast"], 180)


def check_cert(p, require_future=True):
    san = run(["openssl", "x509", "-in", str(p), "-noout",
               "-ext", "subjectAltName"])
    must("DNS:" + DOMAIN in san, "certificate name mismatch")
    if require_future:
        run(["openssl", "x509", "-noout", "-checkend", "1209600", "-in", str(p)])
    a = run(["openssl", "x509", "-noout", "-pubkey", "-in", str(p)])
    b = run(["openssl", "pkey", "-pubout", "-in", str(p)])
    must(a == b, "certificate/private key mismatch")
    return run(["openssl", "x509", "-noout", "-fingerprint", "-sha256",
                "-in", str(p)])


def handshake():
    ready = False
    for _ in range(5):
        try:
            p = subprocess.run(["curl", "--noproxy", "*", "-sS",
                                "--connect-timeout", "3", "--max-time", "5",
                                "--resolve", DOMAIN + ":8443:" + LAN,
                                "-o", "/dev/null",
                                "-w", "%{ssl_verify_result} %{http_code}",
                                "https://" + DOMAIN + ":8443/"],
                               capture_output=True, timeout=7)
            parts = p.stdout.decode(errors="replace").split()
            if (p.returncode == 0 and len(parts) == 2 and
                    parts[0] == "0" and parts[1] in ("200", "302", "403")):
                ready = True
                break
        except subprocess.TimeoutExpired:
            pass
        time.sleep(2)
    must(ready, "recreated native TLS endpoint did not verify")

def atomic_replace(data, uid):
    fd, tmp = tempfile.mkstemp(prefix=".rrn05-cert-", dir=str(DEST.parent))
    try:
        with os.fdopen(fd, "wb") as fp:
            fp.write(data)
            fp.flush()
            os.fsync(fp.fileno())
        os.chown(tmp, uid, 0)
        os.chmod(tmp, 0o600)
        os.replace(tmp, DEST)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    os.umask(0o077)
    must(os.geteuid() == 0 and sys.argv[1:] == ["--apply"],
         "root invocation requires --apply")
    must(STAGING.is_file() and not STAGING.is_symlink(),
         "no staged certificate input")
    must(DEST.is_file() and not DEST.is_symlink(),
         "no deployed Icecast certificate")
    must(BACKUPS.is_dir() and (BACKUPS.stat().st_mode & 0o077) == 0,
         "radio backup dir not private")
    must(STAGING.stat().st_mode & 0o077 == 0,
         "staging certificate file must be mode 0600")
    must(STAGING.stat().st_size < 32768,
         "unexpected certificate input size")
    must((DEST.parent.stat().st_mode & 0o077) == 0,
         "radio private config dir not private")
    import json
    icecast = json.loads(run(["docker", "inspect", CONTAINER]))[0]
    must(icecast["Config"]["Labels"].get("com.docker.compose.project") == PROJECT
         and icecast["Config"]["Labels"].get("com.docker.compose.service") == "icecast"
         and icecast["State"]["Running"], "wrong or stopped Icecast container")
    must(icecast["HostConfig"]["PortBindings"].get("8443/tcp") ==
         [{"HostIp": LAN, "HostPort": "8443"}], "Icecast TLS binding missing")
    uid = int(run(["docker", "exec", CONTAINER, "id", "-u"]))
    prior_fp = check_cert(DEST, require_future=False)
    next_fp = check_cert(STAGING)
    if prior_fp == next_fp:
        STAGING.unlink()
        print("RRN05_CERT_REFRESH=UNCHANGED")
        return
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUPS / ("rrn05-cert-before-" + stamp + ".pem")
    must(not backup.exists(), "backup collision")
    with backup.open("xb") as fp:
        fp.write(DEST.read_bytes())
    os.chmod(backup, 0o600)
    replaced = False
    try:
        atomic_replace(STAGING.read_bytes(), uid)
        replaced = True
        compose()
        handshake()
    except Exception:
        if replaced:
            try:
                atomic_replace(backup.read_bytes(), uid)
                compose()
                handshake()
                print("RRN05_CERT_ROLLBACK=TLS_ACCEPTED")
            except Exception:
                print("RRN05_CERT_ROLLBACK=MANUAL_ATTENTION", file=sys.stderr)
        raise
    finally:
        STAGING.unlink(missing_ok=True)
    print("RRN05_CERT_REFRESH=PASS")
    print("RRN05_CERT_BACKUP=" + str(backup))
    print("RRN05_SCOPE=ICECAST_ONLY")


if __name__ == "__main__":
    try:
        main()
    except (Blocked, OSError, ValueError, IndexError) as exc:
        print("RRN05_CERT_REFRESH=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(2)
