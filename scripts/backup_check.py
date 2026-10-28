#!/usr/bin/env python3
"""Offline, non-extracting AzuraCast backup integrity/manifest checker.

A valid checksum or ZIP CRC does NOT prove a restore will succeed. No upload,
delete, Docker access, unpacking, or external network calls are performed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import zipfile


def digest(path):
    sha = hashlib.sha256()
    size = 0
    with path.open("rb") as archive:
        while True:
            chunk = archive.read(1024 * 1024)
            if not chunk:
                break
            sha.update(chunk)
            size += len(chunk)
    if not size:
        raise ValueError("Empty backup file")
    return {"size_bytes": size, "sha256": sha.hexdigest()}


def crc_if_zip(path):
    if not zipfile.is_zipfile(path):
        return "NOT_ZIP_ARCHIVE"
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()  # Validate without ever extracting.
    if bad is not None:
        raise ValueError("Archive ZIP checksum verification failed")
    return "PASS"


def create(archive, manifest):
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("Backup must be an existing regular file")
    if manifest.exists() or manifest.is_symlink():
        raise ValueError("Refusing to overwrite existing manifest")
    record = {
        "format_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        **digest(archive),
        "zip_crc_check": crc_if_zip(archive),
        "note": "Integrity only. Isolated restore RT-14 must be proven separately.",
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(manifest, flags, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(fd, "w", encoding="utf-8") as dest:
        json.dump(record, dest, indent=2)
        dest.write("\n")
    return record


def verify(archive, manifest):
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("Missing or unsafe backup archive")
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("Missing or unsafe manifest")
    with manifest.open(encoding="utf-8") as source:
        expected = json.load(source)
    if expected.get("format_version") != 1:
        raise ValueError("Unsupported manifest version")
    actual = digest(archive)
    if any(expected.get(key) != value for key, value in actual.items()):
        raise ValueError("Backup checksum or size does not match manifest")
    crc_if_zip(archive)
    return {"status": "PASS", "sha256": actual["sha256"],
            "size_bytes": actual["size_bytes"],
            "limitation": "No isolated restore performed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("create", "verify"))
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        record = (create(args.archive, args.manifest)
                  if args.mode == "create"
                  else verify(args.archive, args.manifest))
    except (OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        print("BLOCK: archive integrity check failed (" +
              type(error).__name__ + ")", file=sys.stderr)
        return 2
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
