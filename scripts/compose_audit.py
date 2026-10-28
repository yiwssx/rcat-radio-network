#!/usr/bin/env python3
"""Review rendered Docker Compose JSON from stdin; does not use Docker API."""
import json
import re
import sys

ALLOWED = {8700, 8743, *range(8600, 8620)}
PROTECTED = {80, 443, 8080, 8081, 8094}

def published(entry):
    if isinstance(entry, dict):
        value = entry.get("published")
        ip = entry.get("host_ip") or "0.0.0.0"
    else:
        parts = str(entry).split("/")[0].rsplit(":", 2)
        if len(parts) == 1:
            return None, None
        value = parts[-2] if len(parts) == 3 else parts[0]
        ip = parts[0] if len(parts) == 3 else "0.0.0.0"
    match = re.fullmatch(r"(\d+)(?:-(\d+))?", str(value))
    if not match:
        return ip, None
    start, end = int(match.group(1)), int(match.group(2) or match.group(1))
    return ip, set(range(start, end + 1)) if start <= end <= start + 2000 else None

def check(config):
    faults = []
    for name, service in config.get("services", {}).items():
        if service.get("privileged") or service.get("network_mode") == "host":
            faults.append(f"{name}: privileged or host-network deployment")
        if service.get("pid") == "host" or "ALL" in (service.get("cap_add") or []):
            faults.append(f"{name}: host PID or all Linux capabilities")
        for volume in service.get("volumes") or []:
            source = (volume.get("source", "") if isinstance(volume, dict)
                      else str(volume).split(":")[0])
            if source in ("/var/run/docker.sock", "/run/docker.sock"):
                faults.append(f"{name}: Docker socket mount")
        for entry in service.get("ports") or []:
            ip, ports = published(entry)
            if not ports:
                faults.append(f"{name}: dynamic or unrecognized published port")
                continue
            if ports & PROTECTED:
                faults.append(f"{name}: reuses protected host port")
            if ports - ALLOWED:
                faults.append(f"{name}: unapproved host port(s)")
            if ip in (None, "", "0.0.0.0", "::", "*"):
                faults.append(f"{name}: published port bound to all interfaces")
    if not config.get("services"):
        faults.append("No Compose services provided")
    return faults

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print("BLOCK: invalid Compose JSON")
        return 2
    faults = check(data)
    for fault in faults:
        print("BLOCK:", fault)
    if faults:
        return 2
    print("Static checks passed. MANUAL APPROVAL still required.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
