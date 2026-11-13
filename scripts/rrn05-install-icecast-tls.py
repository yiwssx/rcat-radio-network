#!/usr/bin/env python3
"""RRN-05: one-pass, radio-only Icecast 2.4.4 native TLS installation.

Use ONLY on the IOT host after a trusted radio.rcat.ac.th combined PEM bundle
has been provisioned securely at /etc/rcat-radio-network/icecast-bundle.pem.
Does not publish WAN access, change MikroTik, manipulate RMS, change LibreTime
URLs, create cert-renewal credentials or re-run accepted AutoDJ/Live-DJ UAT.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PROJECT = "rcat_radio_network"
LAN = "10.10.1.100"
DOMAIN = "radio.rcat.ac.th"
CONTAINER = "rcat_radio_network-icecast-1"
RUNTIME = Path("/opt/rcat-libretime-runtime")
PRIVATE = Path("/etc/rcat-radio-network")
BACKUPS = Path("/var/backups/rcat-radio-network")
OVERRIDE = RUNTIME / "radio.override.yml"
BUNDLE = PRIVATE / "icecast-bundle.pem"
XML = PRIVATE / "icecast-tls.xml"
COMPOSE = RUNTIME / "docker-compose.yml"
ENV = PRIVATE / "compose.env"
IN_CONTAINER_CERT = "/etc/icecast-bundle.pem"
REQUIRED = {"postgres", "rabbitmq", "playout", "liquidsoap",
            "analyzer", "worker", "api", "legacy", "nginx", "icecast"}


class Blocked(Exception):
    pass


def require(test, reason):
    if not test:
        raise Blocked(reason)


def command(argv, *, timeout=80, binary=False):
    try:
        p = subprocess.run(argv, capture_output=True, timeout=timeout,
                           check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise Blocked("command unavailable or timed out: " + argv[0]) from None
    # Docker/Compose output may contain secrets. Never expose it on error.
    require(p.returncode == 0, "command failed: " + argv[0] +
            " (exit " + str(p.returncode) + ")")
    return p.stdout if binary else p.stdout.decode(errors="replace").strip()


def compose(args):
    return command(["docker", "compose", "--project-directory", str(RUNTIME),
                    "--env-file", str(ENV), "-p", PROJECT,
                    "-f", str(COMPOSE), "-f", str(OVERRIDE), *args],
                   timeout=150)


def model():
    return json.loads(compose(["config", "--format", "json"]))


def file_guard(p):
    require(p.is_file() and not p.is_symlink(), str(p) + " must be a real file")


def preflight():
    require(os.geteuid() == 0, "run as root on IOT")
    require(PRIVATE.is_dir() and not PRIVATE.is_symlink() and
            PRIVATE.stat().st_uid == 0 and
            (PRIVATE.stat().st_mode & 0o077) == 0,
            "private radio config directory must be root-owned and 0700")
    require(BACKUPS.is_dir() and not BACKUPS.is_symlink() and
            BACKUPS.stat().st_uid == 0 and
            (BACKUPS.stat().st_mode & 0o077) == 0,
            "existing private radio backup directory required")
    for p in (COMPOSE, ENV, OVERRIDE, BUNDLE):
        file_guard(p)
    require(BUNDLE.stat().st_uid == 0 and
            (BUNDLE.stat().st_mode & 0o077) == 0,
            "certificate bundle input must be root-owned, 0600")
    for cert_mark in (b"-----BEGIN CERTIFICATE-----",
                      b"-----BEGIN PRIVATE KEY-----"):
        require(cert_mark in BUNDLE.read_bytes(),
                "Icecast bundle must contain chain and private key")
    san = command(["openssl", "x509", "-in", str(BUNDLE),
                   "-noout", "-ext", "subjectAltName"])
    require("DNS:" + DOMAIN in san, "bundle does not cover radio domain")
    command(["openssl", "x509", "-checkend", "1209600",
             "-noout", "-in", str(BUNDLE)])
    cert_pub = command(["openssl", "x509", "-pubkey", "-noout", "-in", str(BUNDLE)])
    key_pub = command(["openssl", "pkey", "-pubout", "-in", str(BUNDLE)])
    require(cert_pub == key_pub, "bundle certificate/private key mismatch")
    require(not XML.exists(), "Icecast TLS config already exists; no overwrite")
    require(not any(s.get("port") == 8443 for s in
                    [a for a in []]), "invalid port state")
    # 8443 must not be held by any host process or other project.
    s = socket.socket()
    try:
        require(s.connect_ex((LAN, 8443)) != 0,
                "LAN TCP 8443 is already serving another process")
    finally:
        s.close()
    index = json.loads(command(["docker", "inspect", CONTAINER]))[0]
    require(index["Config"]["Labels"].get("com.docker.compose.project") == PROJECT
            and index["Config"]["Labels"].get("com.docker.compose.service") == "icecast"
            and index["State"]["Running"],
            "unexpected or stopped Icecast container")
    require(index["Config"]["Image"] == "ghcr.io/libretime/icecast:2.4.4",
            "unexpected Icecast image")
    require(not index.get("Mounts"), "existing Icecast mounts require manual review")
    ids = command(["docker", "ps", "-aq", "--filter",
                   "label=com.docker.compose.project=" + PROJECT]).splitlines()
    require(len(ids) == 10, "expected ten isolated radio containers")
    records = json.loads(command(["docker", "inspect", *ids]))
    require({item["Config"]["Labels"].get("com.docker.compose.service")
             for item in records} == REQUIRED and
            all(item["State"]["Running"] for item in records),
            "radio stack is not in the accepted ten-service running state")
    require(index["HostConfig"]["PortBindings"]["8000/tcp"] ==
            [{"HostIp": LAN, "HostPort": "8600"}],
            "existing HTTP listener binding does not match accepted state")
    require(command(["docker", "exec", CONTAINER, "id", "-u"]).isdigit(),
            "cannot resolve Icecast service UID")
    baseline = model()
    require(baseline.get("name") == PROJECT and
            set(baseline.get("services", {})) == REQUIRED,
            "unexpected Compose project structure")
    exposed = {(sname, p.get("host_ip"), str(p.get("published")),
                int(p.get("target")))
               for sname, config in baseline["services"].items()
               for p in config.get("ports", [])}
    require(exposed == {("icecast", LAN, "8600", 8000),
                        ("liquidsoap", LAN, "8605", 8002),
                        ("nginx", LAN, "8700", 8080)},
            "unexpected public ports in existing Compose model")
    require(not any(p.exists() for p in (XML,)),
            "refusing to replace existing TLS config")
    return baseline, int(command(["docker", "exec", CONTAINER, "id", "-u"]))


def render_xml(source):
    root = ET.fromstring(source)
    require(root.tag == "icecast", "unexpected Icecast XML root")
    current = [(x.findtext("port"), x.findtext("ssl", "0"))
               for x in root.findall("listen-socket")]
    require(current == [("8000", "0")], "unexpected existing Icecast listener(s)")
    paths = root.find("paths")
    require(paths is not None and
            paths.find("ssl-certificate") is None and
            paths.find("tls-certificate") is None,
            "unexpected Icecast certificate config")
    secure = ET.SubElement(root, "listen-socket")
    ET.SubElement(secure, "port").text = "8443"
    ET.SubElement(secure, "ssl").text = "1"
    ET.SubElement(paths, "ssl-certificate").text = IN_CONTAINER_CERT
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def render_override(text):
    pattern = re.compile(r"(?ms)^(  icecast:\n)(.*?)(?=^  [A-Za-z_][\w-]*:\n|\Z)")
    sections = list(pattern.finditer(text))
    require(len(sections) == 1, "expected exactly one icecast service override")
    match = sections[0]
    body = match.group(2)
    require("volumes:" not in body and "8443" not in body,
            "existing Icecast volumes/TLS need explicit review")
    port_re = re.compile(r'(?m)^(    ports:\s*!override\n)(      - ["\x27]?'
                         + re.escape(LAN) + r':8600:8000["\x27]?\n)')
    require(len(port_re.findall(body)) == 1,
            "expected exact existing Icecast HTTP port mapping")
    updated = port_re.sub(lambda m: m.group(1) + m.group(2) +
                          '      - "' + LAN + ':8443:8443"\n', body)
    updated = updated.rstrip("\n") + (
        "\n    volumes:\n"
        '      - "' + XML.as_posix() + ':/etc/icecast.xml:rw"\n'
        '      - "' + BUNDLE.as_posix() + ':' + IN_CONTAINER_CERT + ':ro"\n')
    return text[:match.start()] + match.group(1) + updated + text[match.end():]


def check_delta(before, after):
    require(before["name"] == after["name"] and
            set(before["services"]) == set(after["services"]),
            "Compose services/project unexpectedly changed")
    for name in REQUIRED - {"icecast"}:
        require(before["services"][name] == after["services"][name],
                "unexpected non-Icecast service change: " + name)
    old = before["services"]["icecast"]
    new = after["services"]["icecast"]
    require(set(old) | {"volumes"} == set(new),
            "unexpected Icecast Compose fields")
    for key in set(old) - {"ports"}:
        require(old[key] == new[key], "unexpected Icecast field change " + key)
    oldports = old["ports"]
    newports = new["ports"]
    require(len(newports) == len(oldports) + 1 and
            all(x in newports for x in oldports) and
            any(p.get("host_ip") == LAN and p.get("published") == "8443"
                and p.get("target") == 8443 for p in newports),
            "unexpected Icecast listener mapping")
    bindings = new.get("volumes", [])
    require(len(bindings) == 2 and
            {str(x.get("target")) for x in bindings} ==
            {"/etc/icecast.xml", IN_CONTAINER_CERT},
            "unexpected Icecast config/cert mounts")


def secure_write(path, content, uid, mode=0o600):
    fd, name = tempfile.mkstemp(prefix=".rrn05-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chown(name, uid, 0)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def radio_recreate():
    compose(["up", "-d", "--no-deps", "--no-build",
             "--pull", "never", "--force-recreate", "icecast"])


def tls_acceptance():
    # Deployment socket check only, NOT an AutoDJ, music-rights or end-user UAT.
    test = subprocess.run(
        ["curl", "--noproxy", "*", "--silent", "--show-error",
         "--connect-timeout", "4", "--max-time", "9",
         "--resolve", DOMAIN + ":8443:" + LAN,
         "--output", "/dev/null",
         "--write-out", "%{http_code} %{ssl_verify_result}",
         "https://" + DOMAIN + ":8443/"],
        capture_output=True, text=True, timeout=12, check=False)
    require(test.returncode == 0 and
            test.stdout.strip().split()[-1:] == ["0"] and
            test.stdout.strip().split()[0] in {"200", "302", "403"},
            "native Icecast TLS handshake/trust not accepted")
    info = json.loads(command(["docker", "inspect", CONTAINER]))[0]
    require(info["State"]["Running"], "recreated Icecast did not remain running")
    require(info["HostConfig"]["PortBindings"].get("8443/tcp") ==
            [{"HostIp": LAN, "HostPort": "8443"}],
            "TLS published binding not as configured")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", required=True, action="store_true")
    parser.parse_args()
    prior, uid = preflight()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUPS / ("rrn05-icecast-before-" + stamp)
    require(not backup.exists(), "backup destination collision")
    backup.mkdir(mode=0o700)
    original_override = OVERRIDE.read_bytes()
    source_xml = command(["docker", "cp", CONTAINER + ":/etc/icecast.xml", "-"],
                         timeout=25, binary=True)
    import io
    import tarfile
    with tarfile.open(fileobj=io.BytesIO(source_xml), mode="r:") as archive:
        members = [m for m in archive.getmembers() if m.isfile()]
        require(len(members) == 1, "unexpected docker cp config archive")
        config_xml = archive.extractfile(members[0]).read()
    next_xml = render_xml(config_xml)
    next_override = render_override(original_override.decode("utf-8"))
    secure_write(backup / "radio.override.yml", original_override, 0)
    secure_write(backup / "icecast.xml", config_xml, 0)
    prepared = False
    try:
        secure_write(XML, next_xml, uid)
        os.chown(BUNDLE, uid, 0)  # Host directory remains root/0700.
        secure_write(OVERRIDE, next_override.encode("utf-8"), 0, 0o644)
        prepared = True
        check_delta(prior, model())
        radio_recreate()
        tls_acceptance()
    except Exception:
        # Only radio-owned override and Icecast are restored. Never delete volumes.
        if prepared:
            try:
                secure_write(OVERRIDE, original_override, 0, 0o644)
                radio_recreate()
                print("RRN05_ICECAST_ROLLBACK=RECREATE_RETURNED")
            except Exception:
                print("RRN05_ICECAST_ROLLBACK=MANUAL_ATTENTION", file=sys.stderr)
        XML.unlink(missing_ok=True)
        raise
    print("RRN05_ICECAST_TLS=INSTALLED")
    print("RRN05_BACKUP=" + str(backup))
    print("RRN05_INTERNAL_HTTPS=https://" + DOMAIN + ":8443/main.mp3")
    print("RRN05_WAN_NAT=NOT_CHANGED")
    print("RRN05_CERT_RENEWAL=NOT_CONFIGURED")
    print("RRN05_PUBLIC_LAUNCH=NOT_PERFORMED")


if __name__ == "__main__":
    try:
        main()
    except (Blocked, ValueError, OSError, KeyError, ET.ParseError) as exc:
        print("RRN05_STATUS=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(2)
