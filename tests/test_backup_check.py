import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import backup_check


class BackupIntegrityTests(unittest.TestCase):
    def test_zip_manifest_and_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "sample.zip"
            manifest = root / "sample.manifest.json"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("station/playlist.txt", "Sample licensed test media")
            details = backup_check.create(archive, manifest)
            self.assertEqual(details["zip_crc_check"], "PASS")
            self.assertEqual(manifest.stat().st_mode & 0o777, 0o600)
            self.assertEqual(backup_check.verify(archive, manifest)["status"], "PASS")
            with self.assertRaisesRegex(ValueError, "overwrite"):
                backup_check.create(archive, manifest)

    def test_modified_backup_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "sample.bin"
            manifest = root / "sample.manifest.json"
            archive.write_bytes(b"original backup")
            backup_check.create(archive, manifest)
            archive.write_bytes(b"replaced backup")
            with self.assertRaisesRegex(ValueError, "checksum"):
                backup_check.verify(archive, manifest)

    def test_invalid_zip_does_not_receive_integrity_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "damaged.zip"
            manifest = root / "manifest.json"
            archive.write_bytes(b"not a ZIP archive")
            with self.assertRaisesRegex(ValueError, "Invalid ZIP"):
                backup_check.create(archive, manifest)
            self.assertFalse(manifest.exists())

    def test_empty_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "empty.zip"
            archive.touch()
            with self.assertRaises(ValueError):
                backup_check.digest(archive)


if __name__ == "__main__":
    unittest.main()
