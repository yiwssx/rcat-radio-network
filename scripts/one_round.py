#!/usr/bin/env python3
"""One-session RCAT Radio LAN pilot with a fail-closed shared-host gate.

Only --deploy can start new *radio-project* containers. --check never starts,
pulls or stops anything. Reports and secrets stay local (gitignored).
"""
import argparse
import concurrent.futures
import datetime
import http.client
import ipaddress
import json
import math
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave

import compose_audit
import preflight

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "deployment" / "compose.pilot.yaml"
PROJECT = "rcat_radio_pilot"
BROADCAST_PORTS = {8600, 8605, 8606, 8700, 8750}
MIN_RAM_TOTAL = 4 * 1024**3
MIN_RAM_AVAILABLE = 2 * 1024**3
MIN_DISK_FREE = 40 * 1024**3


def command(argv, *, cwd=ROOT, input_text=None, timeout=180, env=None):
    return subprocess.run(argv, input=input_text, capture_output=True, text=True,
                          cwd=cwd, env=env, timeout=timeout, check=False)


def fail(message):
    print("BLOCK:", message, file=sys.stderr)
    raise RuntimeError(message)


def local_ipv4s():
    p = command(["ip", "-j", "-4", "address", "show"], timeout=10)
    if p.returncode != 0:
        return set()
    return {a.get("local") for interface in json.loads(p.stdout)
            for a in interface.get("addr_info", [])
            if a.get("family") == "inet" and a.get("local")}


def valid_bind(ip):
    try:
        obj = ipaddress.ip_address(ip)
        return obj.version == 4 and (obj.is_loopback or any(obj in ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")))
    except ValueError:
        return False


def probe(url, timeout=6):
    # Do not forward credentials, cookies or redirects to arbitrary sites.
    class LocalRedirectBlocker(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(LocalRedirectBlocker())
    try:
        with opener.open(urllib.request.Request(url, headers={
            "User-Agent": "RCAT-Radio-Pilot/1.0"}), timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def baseline(ip):
    # Only local, previously documented ports; no public internet requests.
    return {
        "pdf_hub": probe(f"http://{ip}:8081/"),
        "anyflip": probe(f"http://{ip}:8094/healthz"),
    }


def compare_baseline(before, after, protected_observed):
    faults = []
    for name, port in (("pdf_hub", 8081), ("anyflip", 8094)):
        previous, current = before.get(name), after.get(name)
        if protected_observed.get(str(port), False) and previous is None:
            faults.append(f"{name}: existing port observed but HTTP baseline unreachable")
        if previous != current:
            faults.append(f"{name}: HTTP status changed from {previous} to {current}")
    return faults


def environment(ip):
    return {
        "COMPOSE_PROJECT_NAME": PROJECT,
        "RRN_BIND_IP": ip,
        "AZURACAST_VERSION": "stable",
        "AZURACAST_HTTP_PORT": "8700",
        "AZURACAST_HTTPS_PORT": "8743",
        "AZURACAST_SFTP_PORT": "2022",
        "AZURACAST_PUID": str(os.getuid()),
        "AZURACAST_PGID": str(os.getgid()),
    }


def write_private(path, data):
    if path.exists():
        return False
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        out.write(data)
    return True


def setup_private_environment(ip):
    dest = ROOT / "deployment" / ".env"
    app = ROOT / "deployment" / "azuracast.env"
    # Refuse stale/broken half-installation; do not overwrite DB passwords.
    if dest.exists() != app.exists():
        fail("Only one environment file exists; inspect manually, do not overwrite secrets.")
    if not dest.exists():
        v = command(["docker", "volume", "ls", "--format", "{{.Name}}"], timeout=20)
        if v.returncode != 0:
            fail("Unable to inspect Docker volumes before creating database credentials")
        if any(name.startswith(PROJECT + "_") for name in v.stdout.splitlines()):
            fail("Existing radio volumes detected without credentials; restore original secrets")
    if dest.exists():
        recorded = {}
        for line in dest.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, value = line.split("=", 1)
                recorded[k] = value
        if recorded.get("RRN_BIND_IP") != ip or recorded.get("COMPOSE_PROJECT_NAME") != PROJECT:
            fail("Existing pilot settings target a different network or Compose project.")
        return
    env = environment(ip)
    write_private(dest, "".join(f"{k}={v}\n" for k, v in env.items()))
    secret = secrets.token_urlsafe(36)
    write_private(app,
                  "APPLICATION_ENV=production\n"
                  "LOG_LEVEL=notice\n"
                  "AUTO_ASSIGN_PORT_MIN=8600\n"
                  "AUTO_ASSIGN_PORT_MAX=8609\n"
                  "MYSQL_PASSWORD=" + secret + "\n"
                  "MYSQL_RANDOM_ROOT_PASSWORD=yes\n"
                  "SHOW_DETAILED_ERRORS=false\n")
    print("Created protected local environment files (no passwords printed).")


def compose_cmd(*args):
    return ["docker", "compose", "-p", PROJECT, "-f", str(COMPOSE), *args]


def static_compose_review(ip):
    os.environ["RRN_ALLOWED_BIND_IPS"] = ip
    compose_audit.APPROVED_IPS.add(ip)
    p = command(compose_cmd("config", "--format", "json"), timeout=30)
    if p.returncode:
        fail("docker compose config rejected pilot Compose (review locally).")
    try:
        parsed = json.loads(p.stdout)
    except json.JSONDecodeError:
        fail("Rendered Compose is not valid JSON")
    errors = compose_audit.check(parsed)
    if set(parsed.get("services", {})) != {"web", "portal"}:
        errors.append("Unexpected service in the radio Compose stack")
    if parsed.get("name") != PROJECT:
        errors.append("Unexpected Compose project name")
    if errors:
        fail("Rendered Compose rejected: " + "; ".join(errors))
    return True


def project_exists():
    p = command(["docker", "ps", "-a", "--format", "{{.Label \"com.docker.compose.project\"}}"], timeout=20)
    if p.returncode:
        fail("Cannot inspect Docker containers: verify Docker group permissions")
    return PROJECT in p.stdout.splitlines()


def preflight_gate(ip):
    if not valid_bind(ip) or ip not in local_ipv4s():
        fail("Chosen IPv4 address is not a private IPv4 address configured on this host.")
    pre = preflight.audit()
    if not pre["docker_accessible"] or not pre["ss_accessible"]:
        fail("Docker and listening-port inventory must both be accessible")
    if pre["ram_bytes"].get("MemTotal", 0) < MIN_RAM_TOTAL:
        fail("Shared host has under 4 GiB total RAM")
    if pre["ram_bytes"].get("MemAvailable", 0) < MIN_RAM_AVAILABLE:
        fail("Shared host has less than 2 GiB currently available RAM")
    if (pre["disk_free_var_bytes"] or 0) < MIN_DISK_FREE:
        fail("Shared host has less than 40 GiB free on /var")
    if (pre["cpu_logical"] or 0) < 4:
        fail("Shared host has fewer than 4 logical CPUs")
    occupied = sorted(p for p in BROADCAST_PORTS if pre["candidate_ports"].get(str(p)) == "IN_USE")
    # 8750 is outside initial legacy preflight candidate pool; inspect it separately.
    if 8750 not in pre["candidate_ports"]:
        ss = preflight.cmd(["ss", "-H", "-lntu"])
        dp = preflight.cmd(["docker", "ps", "--format", "{{json .}}"])
        if 8750 in (preflight.listening_ports(ss) | preflight.published_ports(dp)):
            occupied.append(8750)
    if occupied:
        fail("Pilot port collision: " + ", ".join(map(str, sorted(set(occupied)))))
    if project_exists():
        fail("Pilot project already exists; run --verify instead to protect previous data")
    return pre


def create_test_audio(path):
    """Original, low-volume synthetic test sound; no third-party music."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(22050)
        frames = bytearray()
        rate = 22050
        for i in range(12 * rate):
            t = i / rate
            phase = int(t // 3) % 3
            freq = (440, 523.25, 659.25)[phase]
            envelope = min(1, (t % 3) / .08, (3 - (t % 3)) / .12)
            amplitude = .09 * max(0, envelope)
            value = int(32767 * amplitude * math.sin(2 * math.pi * freq * t))
            frames += value.to_bytes(2, "little", signed=True)
        audio.writeframes(frames)


def wait_http(url, timeout=180):
    end = time.monotonic() + timeout
    last = None
    while time.monotonic() < end:
        last = probe(url, timeout=5)
        if last is not None and last < 500:
            return last
        time.sleep(3)
    return last


def raw_json(url, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            raw = response.read(512 * 1024)
            return json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return None


def extract_station(obj):
    rows = obj if isinstance(obj, list) else [obj]
    return next((x for x in rows if isinstance(x, dict)
                 and isinstance(x.get("station"), dict)
                 and x["station"].get("shortcode") == "rcat_radio"), None)


def stream_probe(ip, port=8600):
    try:
        con = http.client.HTTPConnection(ip, port, timeout=8)
        con.request("GET", "/radio.mp3", headers={"User-Agent": "RRN-Smoke-Test"})
        res = con.getresponse()
        data = res.read(2048) if res.status == 200 else b""
        con.close()
        return res.status == 200 and len(data) >= 512
    except (OSError, TimeoutError, http.client.HTTPException):
        return False


def report_save(folder, results):
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    file = folder / "result.json"
    write_private(file, json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print("Report:", file)
    return file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("check", "deploy", "verify"), default="check")
    parser.add_argument("--bind-ip", required=True,
                        help="Existing private IPv4 on server; never use a public IP")
    parser.add_argument("--ack-shared-host", action="store_true",
                        help="Required to authorize a new, isolated Docker radio stack")
    parser.add_argument("--no-prompt", action="store_true",
                        help="Do not prompt for the manual station setup checkpoint")
    args = parser.parse_args()
    # Legacy single-session runner cannot enforce the operator's signed RRN-00/01/02
    # approval record. Keep read-only check/verify available, but route ALL new
    # deployments through the maintained, approval-gated Docker-only controller.
    if args.mode == "deploy":
        fail("Legacy deploy is disabled. Run scripts/radioctl.sh after approved RRN-00/01/02 gates.")
    ip = args.bind_ip
    if not valid_bind(ip) or ip not in local_ipv4s():
        fail("Bind IP is not a local private IPv4 address on this machine")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = ROOT / "reports" / ("pilot-" + stamp)
    folder.mkdir(parents=True, exist_ok=False, mode=0o700)
    results = {
        "mode": args.mode, "time_utc": stamp, "project": PROJECT,
        "status": "BLOCKED", "automatic": {}, "manual": {},
        "warning": "LAN proof of concept only; no public production readiness asserted",
    }
    started_new = False
    try:
        before = baseline(ip)
        results["automatic"]["existing_services_before"] = before
        pre = None
        if args.mode == "deploy":
            if not args.ack_shared_host:
                fail("Use --ack-shared-host to authorize Docker changes to the radio project")
            pre = preflight_gate(ip)
            bad_start = compare_baseline(before, before, pre["protected_ports_observed"])
            if bad_start:
                fail("Unhealthy pre-deployment baseline: " + "; ".join(bad_start))
            setup_private_environment(ip)
            static_compose_review(ip)
            results["automatic"]["static_compose"] = "PASS"
            print("Preflight and static Compose review passed; starting radio-only pilot.")
            for task in [compose_cmd("pull", "web", "portal"),
                         compose_cmd("run", "--rm", "--no-deps", "web", "--", "azuracast_install"),
                         compose_cmd("up", "-d", "web", "portal")]:
                print("Running approved radio project command:", task[-1])
                if "up" in task:
                    started_new = True  # compose up may partially start before failure
                p = command(task, timeout=1200)
                if p.returncode:
                    fail("Radio-only Compose step failed. Exit code: " + str(p.returncode)
                         + ". Inspect Docker logs locally; no global cleanup attempted.")
            started_new = True
            results["automatic"]["radio_stack_started"] = "PASS"
            local_admin=wait_http("http://127.0.0.1:8700/")
            portal=wait_http(f"http://{ip}:8750/")
            results["automatic"]["admin_http_status"] = local_admin
            results["automatic"]["portal_http_status"] = portal
            if local_admin is None or portal != 200:
                fail("Radio UI failed its initial web smoke test")
            immediate = baseline(ip)
            results["automatic"]["existing_services_after"] = immediate
            changes = compare_baseline(before, immediate, pre["protected_ports_observed"])
            if changes:
                fail("Existing services regression: " + "; ".join(changes)
                     + ". Radio-only containers stopped; radio volumes preserved.")
            create_test_audio(folder / "rrn-original-test-tone.wav")
            print("\nPilot started (not yet an on-air station).")
            print(f"Listener portal: http://{ip}:8750")
            print("Admin is loopback-only: use SSH tunnel -L 8700:127.0.0.1:8700")
            print("Open http://127.0.0.1:8700 on your local computer via SSH tunnel.")
            print("Set up the admin account, create station shortcode rcat_radio")
            print("with Icecast port 8600, then upload reports/.../rrn-original-test-tone.wav")
            print("as an AutoDJ playlist and start broadcasting.")
            print("Live DJ / fallback need a separate source (BUTT or Mixxx) to validate.")
            results["manual"]["admin_station_playlist_live_dj"] = "PENDING_OPERATOR_SETUP"
            if not args.no_prompt and sys.stdin.isatty():
                input("\nPress Enter AFTER station + test playlist + live DJ tests to verify (or Ctrl+C to exit)...")
        elif args.mode == "check":
            pre=preflight_gate(ip)
            results["automatic"]["preflight"] = "PASS"
            results["automatic"]["static_compose"] = "NOT_RUN_ENV_PENDING"
            results["status"] = "READY_FOR_DEPLOYMENT_REVIEW"
            return 0
        else:
            if not project_exists():
                fail("Radio project has not been deployed; use --mode deploy")
        results["automatic"]["portal_http_status_final"] = probe(f"http://{ip}:8750/")
        data = raw_json(f"http://{ip}:8750/api/nowplaying")
        station = extract_station(data)
        results["automatic"]["nowplaying_api"] = "PASS" if isinstance(data, list) else "NOT_READY"
        results["automatic"]["station_configured"] = "PASS" if station else "PENDING"
        results["automatic"]["station_on_air"] = bool(station and station.get("is_online"))
        if station and station.get("is_online"):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                streams = list(executor.map(lambda _ : stream_probe(ip), range(5)))
            results["automatic"]["stream_smoke_5_clients"] = "PASS" if all(streams) else "FAIL"
        else:
            results["automatic"]["stream_smoke_5_clients"] = "PENDING_STATION_SETUP"
        results["automatic"]["existing_services_final"] = baseline(ip)
        before_service=results["automatic"]["existing_services_before"]
        regression=compare_baseline(before_service, results["automatic"]["existing_services_final"],
                                    pre["protected_ports_observed"] if pre else {})
        results["automatic"]["existing_services_regression"] = "FAIL" if regression else "UNCHANGED_HTTP_STATUSES"
        # All operational/advanced tests stay pending until real audio / live source
        # and endurance, restore and security checks produce independent evidence.
        results["manual"].update({
            "live_dj_switch": "NOT_AUTOMATICALLY_VERIFIED",
            "auto_dj_fallback": "NOT_AUTOMATICALLY_VERIFIED",
            "audio_silence_and_quality": "NOT_AUTOMATICALLY_VERIFIED",
            "24h_soak": "NOT_RUN",
            "off_host_restore": "NOT_RUN",
            "internet_and_vlan_firewall": "NOT_VERIFIED",
            "pdf_conversion_and_anyflip_workflow": "MANUAL_REGRESSION_REQUIRED",
        })
        if regression:
            results["status"] = "FAIL_REGRESSION_REVIEW"
            return 2
        results["status"] = ("SMOKE_PASS_MANUAL_TESTS_PENDING"
                             if results["automatic"]["stream_smoke_5_clients"] == "PASS"
                             else "DEPLOYED_STATION_SETUP_OR_STREAM_PENDING")
        return 0 if results["automatic"]["stream_smoke_5_clients"] == "PASS" else 3
    except (RuntimeError, subprocess.TimeoutExpired, KeyboardInterrupt) as e:
        if started_new:
            print("Stopping ONLY this radio pilot stack; preserving its volumes.", file=sys.stderr)
            try:
                command(compose_cmd("stop", "portal", "web"), timeout=90)
                results["automatic"]["radio_only_stop_on_failure"] = "ATTEMPTED"
            except (OSError, subprocess.TimeoutExpired):
                results["automatic"]["radio_only_stop_on_failure"] = "FAILED_REQUIRES_OPERATOR"
        results["status"] = "BLOCKED_OR_INCOMPLETE"
        results["error_class"] = type(e).__name__
        results["error"] = str(e)[:280] if not isinstance(e, KeyboardInterrupt) else "Interrupted by operator"
        print("Pilot gate stopped:", results["error"], file=sys.stderr)
        return 2
    finally:
        report_save(folder, results)
        print("Result status:", results["status"])
        print("Existing projects have not been restarted or pruned by this script.")


if __name__ == "__main__":
    raise SystemExit(main())
