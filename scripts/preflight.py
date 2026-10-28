#!/usr/bin/env python3
"""Read-only host and published-port audit. Does not operate on containers."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

CANDIDATES = [8700, 8743] + list(range(8600, 8620))
PROTECTED = [80, 443, 8080, 8081, 8094]

def cmd(argv):
    if not shutil.which(argv[0]):
        return None
    try:
        p = subprocess.run(argv, text=True, capture_output=True,
                           timeout=12, stdin=subprocess.DEVNULL)
        return p.stdout if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None

def listening_ports(out):
    result = set()
    for line in (out or "").splitlines():
        fields = line.split()
        if len(fields) >= 5:
            match = re.search(r":(\d+)$", fields[4])
            if match:
                result.add(int(match.group(1)))
    return result

def published_ports(out):
    result = set()
    # Inspect actual host publications rather than image EXPOSE settings.
    expression = re.compile(r"(?:[0-9.]+|\[[a-fA-F0-9:]+\]):(\d+)(?:-(\d+))?->")
    for line in (out or "").splitlines():
        try:
            container = json.loads(line)
        except json.JSONDecodeError:
            continue
        for match in expression.finditer(container.get("Ports", "")):
            start = int(match.group(1))
            end = int(match.group(2) or start)
            if start <= end <= start + 2000:
                result.update(range(start, end+1))
    return result

def memory():
    info = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            name, _, value = line.partition(":")
            if name in {"MemTotal", "MemAvailable"}:
                info[name] = int(value.strip().split()[0]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return info

def audit():
    ss = cmd(["ss", "-H", "-lntu"])
    dock = cmd(["docker", "ps", "--format", "{{json .}}"])
    ports = listening_ports(ss) | published_ports(dock)
    try:
        free = shutil.disk_usage("/var").free
    except OSError:
        free = None
    report = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cpu_logical": os.cpu_count(),
        "ram_bytes": memory(),
        "disk_free_var_bytes": free,
        "ss_accessible": ss is not None,
        "docker_accessible": dock is not None,
        "candidate_ports": {str(p): "IN_USE" if p in ports else (
            "NOT_OBSERVED" if ss is not None and dock is not None else "UNKNOWN")
            for p in CANDIDATES},
        "protected_ports_observed": {str(p): p in ports for p in PROTECTED},
        "gate": "PENDING_MANUAL_APPROVAL",
    }
    blockers = []
    if ss is None or dock is None:
        blockers.append("Host/Docker listening port inventory incomplete")
    blockers += ["Candidate host port occupied: " + str(p) for p in CANDIDATES if p in ports]
    if report["ram_bytes"].get("MemTotal", 0) < 2 * 1024**3:
        blockers.append("RAM below 2 GiB minimum")
    if free is None:
        blockers.append("Free disk capacity unknown")
    report["blockers"] = blockers
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    path = Path(args.output_dir)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    result = audit()
    (path / "shareable-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Read-only audit written to", path)
    print("Gate: PENDING_MANUAL_APPROVAL; blockers:", len(result["blockers"]))
    return 2 if result["blockers"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
