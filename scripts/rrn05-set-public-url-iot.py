#!/usr/bin/env python3
"""RRN05: apply only LibreTime general.public_url to the already-installed IOT runtime.

Scope: existing /etc/rcat-radio-network/config.yml and three existing
web/UI containers. No Icecast/Liquidsoap/DB/MQ/other project changes.
"""
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

CONF = Path("/etc/rcat-radio-network/config.yml")
BACKUPS = Path("/var/backups/rcat-radio-network")
TARGET = "https://radio.rcat.ac.th:8700"
OLD_VALUES = {"http://10.10.1.100:8700", "http://127.0.0.1:8700"}
RESTART = ["rcat_radio_network-api-1", "rcat_radio_network-legacy-1",
           "rcat_radio_network-nginx-1"]

class Blocked(Exception):
    pass

def require(cond, msg):
    if not cond:
        raise Blocked(msg)

def run(args, timeout=90):
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, timeout=timeout, check=False)
    require(r.returncode == 0, "command failed: " + args[0] + " exit=" + str(r.returncode))
    return r.stdout.strip()

def change_only_general_public_url(text):
    lines = text.splitlines(keepends=True)
    tops = [i for i, line in enumerate(lines)
            if re.fullmatch(r"general:[ \t]*(?:#.*)?[\r\n]*", line)]
    require(len(tops) == 1, "one top-level general section required")
    start = tops[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if re.match(r"^[A-Za-z_.][\w.]*:[ \t]*(?:.*)", lines[i]):
            end = i
            break
    found = []
    for i in range(start + 1, end):
        m = re.match(r"^([ ]{2}public_url:[ \t]*)([^#\r\n]*?)([ \t]*(?:#.*)?)(\r?\n?)$", lines[i])
        if m:
            found.append((i, m))
    require(len(found) == 1, "one general.public_url required")
    idx, m = found[0]
    current = m.group(2).strip().strip('"').strip("'")
    if current == TARGET:
        return text, "ALREADY_APPLIED", current
    require(current in OLD_VALUES, "unexpected canonical URL (not overwritten)")
    lines[idx] = m.group(1) + '"' + TARGET + '"' + m.group(3) + m.group(4)
    return "".join(lines), "CHANGED", current

def restart_web():
    run(["docker", "restart", "--time", "10", *RESTART], timeout=100)

def ready():
    # HTTPS terminates at RMS; route directly to its LAN IP but validate domain cert.
    result = run(["curl", "--noproxy", "*", "-sS", "--connect-timeout", "4",
                  "--max-time", "12", "--resolve",
                  "radio.rcat.ac.th:8700:10.10.2.100",
                  "-o", "/dev/null", "-w", "%{http_code} %{ssl_verify_result}",
                  TARGET + "/login"], timeout=18)
    p = result.split()
    require(len(p) == 2 and p[1] == "0" and p[0] in
            {"200", "301", "302", "303"}, "proxy/public URL not ready: HTTP/TLS=" + result)

def main():
    require(sys.argv[1:] == ["--apply"], "usage: sudo python3 rrn05-set-public-url-iot.py --apply")
    require(os.geteuid() == 0, "root required on IOT")
    require(CONF.is_file() and not CONF.is_symlink(), "private config missing/symlinked")
    require(BACKUPS.is_dir() and not BACKUPS.is_symlink() and
            BACKUPS.stat().st_uid == 0 and
            (BACKUPS.stat().st_mode & 0o077) == 0,
            "existing root-only backup directory required")
    text = CONF.read_text(encoding="utf-8")
    replacement, status, old = change_only_general_public_url(text)
    if status == "ALREADY_APPLIED":
        print("RRN05_IOT_PUBLIC_URL=ALREADY_APPLIED")
        return
    # Only the existing radio project's named containers may be restarted.
    records = json.loads(run(["docker", "inspect", *RESTART], timeout=60))
    require(len(records) == 3 and
            {r["Config"]["Labels"].get("com.docker.compose.service") for r in records}
            == {"api", "legacy", "nginx"} and
            all(r["Config"]["Labels"].get("com.docker.compose.project")
                == "rcat_radio_network" and r["State"]["Running"]
                for r in records), "unexpected radio web containers")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUPS / ("rrn05-public-url-before-" + stamp + ".yml")
    with backup.open("xb") as f:
        os.chmod(backup, 0o600)
        f.write(text.encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
    require(backup.stat().st_size > 0, "backup empty")
    print("RRN05_URL_BACKUP=" + str(backup), flush=True)
    touched = False
    try:
        # Preserve inode because Docker bind mounts a host file.
        touched = True
        with CONF.open("r+", encoding="utf-8") as f:
            f.seek(0)
            f.write(replacement)
            f.truncate()
            f.flush()
            os.fsync(f.fileno())
        restart_web()
        ready()
    except Exception:
        if touched:
            try:
                with CONF.open("r+", encoding="utf-8") as f:
                    f.seek(0)
                    f.write(text)
                    f.truncate()
                    f.flush()
                    os.fsync(f.fileno())
                restart_web()
                print("RRN05_IOT_URL_ROLLBACK=RESTORED", flush=True)
            except Exception:
                print("RRN05_IOT_URL_ROLLBACK=MANUAL_ATTENTION", file=sys.stderr)
        raise
    print("RRN05_IOT_PUBLIC_URL=APPLIED")
    print("RRN05_LOGIN_HTTPS=" + TARGET + "/login")
    print("RRN05_ICECAST_DJ_RESTARTED=NO")
    print("RRN05_MIKROTIK=NOT_CHANGED")

if __name__ == "__main__":
    try:
        main()
    except (Blocked, OSError, subprocess.TimeoutExpired, ValueError, KeyError) as e:
        print("RRN05_STATUS=BLOCKED: " + str(e), file=sys.stderr)
        sys.exit(2)
