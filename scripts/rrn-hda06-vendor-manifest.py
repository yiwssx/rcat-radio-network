#!/usr/bin/env python3
"""Record registry-verified LibreTime vendor image manifests, never Host identity.

Source of service/image names: the reviewed RRN-02 installer in this repository.
This script neither pulls images nor contacts any RCAT Host or private config.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "rrn02-isolated-installer.py"
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
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
MEDIA = {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.docker.distribution.manifest.v2+json",
}
MAX_OUTPUT = 2 * 1024 * 1024


class VerificationError(ValueError):
    pass


def source_images():
    """Read a reviewed AST literal, without executing the host installer."""
    tree = ast.parse(INSTALLER.read_text(encoding="utf-8"))
    definitions = [node.value for node in tree.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(k, ast.Name) and k.id == "IMAGES"
                           for k in node.targets)]
    if len(definitions) != 1:
        raise VerificationError("Expected exactly one installer IMAGES literal")
    images = ast.literal_eval(definitions[0])
    if images != EXPECTED_IMAGES:
        raise VerificationError("Installer images differ from reviewed vendor stack")
    return images


def checked_command(*argv):
    try:
        p = subprocess.run(argv, check=False, timeout=60, capture_output=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerificationError("Registry inspect unavailable") from exc
    if p.returncode or len(p.stdout) > MAX_OUTPUT:
        raise VerificationError("Registry inspect failed or output exceeded limit")
    return p.stdout


def verify_manifest(image):
    info = checked_command("docker", "buildx", "imagetools", "inspect", image)
    matched = re.findall(rb"(?m)^Digest:\s*(sha256:[0-9a-f]{64})\s*$", info)
    if len(matched) != 1:
        raise VerificationError("Missing or ambiguous registry manifest digest")
    digest = matched[0].decode("ascii")
    if not DIGEST.fullmatch(digest):
        raise VerificationError("Invalid registry digest")
    raw = checked_command("docker", "buildx", "imagetools", "inspect", "--raw", image)
    # Buildx may append a presentation newline after the original manifest.
    candidates = [raw]
    if raw.endswith(b"\n"):
        candidates.append(raw[:-1])
    verified = next((b for b in candidates
                     if "sha256:" + hashlib.sha256(b).hexdigest() == digest), None)
    if verified is None:
        raise VerificationError("Registry manifest bytes and digest disagree")
    try:
        manifest = json.loads(verified)
    except (ValueError, UnicodeError) as exc:
        raise VerificationError("Invalid registry manifest JSON") from exc
    if (not isinstance(manifest, dict)
            or manifest.get("schemaVersion") != 2
            or manifest.get("mediaType") not in MEDIA):
        raise VerificationError("Unexpected vendor manifest format")
    return {"digest": digest, "media_type": manifest["mediaType"],
            "manifest_bytes_sha256_verified": True}


def collect(source_sha, probe=verify_manifest):
    if not isinstance(source_sha, str) or not SHA.fullmatch(source_sha):
        raise VerificationError("Exact trusted source SHA is required")
    images = source_images()
    records = {}
    for image in sorted(set(images.values())):
        records[image] = probe(image)
        receipt = records[image]
        if (not isinstance(receipt, dict)
                or receipt.get("manifest_bytes_sha256_verified") is not True
                or not isinstance(receipt.get("digest"), str)
                or not DIGEST.fullmatch(receipt["digest"])
                or receipt.get("media_type") not in MEDIA):
            raise VerificationError("Unverified vendor manifest receipt")
    return {
        "schema_version": 1,
        "kind": "rcat.radio.vendor-image-set",
        "source_repository": "yiwssx/rcat-radio-network",
        "source_commit": source_sha,
        "scope": "public upstream registry manifests for reviewed installer tags; NOT host image identity or upstream publisher signature",
        "services": [
            {"service": service, "tag": images[service], **records[images[service]]}
            for service in sorted(images)
        ],
    }


def main():
    source_sha = os.getenv("GITHUB_SHA", "")
    output = ROOT / "release" / ("vendor-image-set-" + source_sha + ".json")
    # Don't write a partial candidate when any upstream registry lookup fails.
    result = collect(source_sha)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
    output.write_bytes(payload)
    (output.parent / (output.name + ".sha256")).write_text(
        hashlib.sha256(payload).hexdigest() + "  " + output.name + "\n", encoding="ascii"
    )
    print("RRN_HDA06_VENDOR_MANIFEST=VERIFIED_REGISTRY_BYTES_ONLY")
    print("service_count=" + str(len(result["services"])))
    print("unique_image_count=" + str(len({v["tag"] for v in result["services"]})))
    print("host_image_identity_verified=false")
    print("publisher_source_attestation_verified=false")


if __name__ == "__main__":
    try:
        main()
    except (VerificationError, OSError, ValueError) as error:
        print("RRN_HDA06_STATUS=BLOCKED: " + str(error), file=sys.stderr)
        sys.exit(2)
