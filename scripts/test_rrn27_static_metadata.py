"""RRN-27 focused isolated checks: data minimization and safe publication."""
import importlib.util
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('rrn27-static-metadata-rms.py')
spec = importlib.util.spec_from_file_location('rrn27_static', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MetadataTests(unittest.TestCase):
    def test_only_whitelisted_fields_are_public(self):
        raw = {'station': {'env': 'production', 'internal': 'secret'},
               'tracks': {
                   'previous': {'type': 'track', 'name': 'unused', 'metadata': {
                       'track_title': 'ทดสอบ', 'artist_name': 'ศิลปิน',
                       'filepath': '/private/song.mp3', 'owner_id': 7,
                       'md5': 'abc123', 'copyright': 'internal'}},
                   'current': None, 'next': None},
               'sources': {'admin': 'private'}}
        output = module.project(raw, now=1000)
        self.assertEqual(output, {
            'rcat_public_feed': {'schema': 1, 'generated_at': 1000, 'expires_at': 1180},
            'tracks': {'previous': {'type': 'track', 'metadata': {
                'track_title': 'ทดสอบ', 'artist_name': 'ศิลปิน'}},
                       'current': None, 'next': None}})
        for hidden in ('filepath', 'owner_id', 'md5', 'station', 'sources', 'copyright'):
            self.assertNotIn(hidden, json.dumps(output))

    def test_live_dj_does_not_invent_artist(self):
        payload = {'tracks': {'current': {'type': 'livestream', 'name': 'DJ Live',
                                          'metadata': {'artist_name': 'should-not-display'}}}}
        out = module.project(payload, now=1000)
        self.assertEqual(out['tracks']['current'], {'type': 'livestream',
                                                       'metadata': {'track_title': 'DJ Live'}})
        self.assertIsNone(out['tracks']['next'])

    def test_unicode_from_python_two_json_is_preserved_and_ascii_encoded(self):
        raw = {'tracks': {'current': {'type': 'track', 'metadata': {
            'track_title': 'เพลงไทย', 'artist_name': 'ศิลปิน'}}}}
        snapshot = module.project(raw, now=1000)
        serialized = json.dumps(snapshot, ensure_ascii=True).encode('ascii')
        self.assertIn(b'\\u', serialized)
        self.assertEqual(json.loads(serialized.decode('ascii'))['tracks']['current']['metadata']['track_title'], 'เพลงไทย')

    def test_bad_schema_rejected(self):
        for payload in ({}, None, {'tracks': []}, '<html>error</html>'):
            with self.assertRaises(module.Blocked):
                module.project(payload)

    def test_atomic_file_and_ownership_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / 'radio-metadata.json'
            with patch.object(module, 'DOCROOT', root), patch.object(module, 'TARGET', target):
                data = module.project({'tracks': {}}, now=1000)
                module.publish(data)
                self.assertEqual(json.loads(target.read_text())['tracks']['current'], None)
                self.assertTrue(target.read_bytes().endswith(b'\n'))
                self.assertFalse(any(root.glob('.rrn27-*.tmp')))
                target.write_text('{"unrelated":"document"}')
                with self.assertRaises(module.Blocked):
                    module.publish(data)
                self.assertEqual(json.loads(target.read_text())['unrelated'], 'document')


if __name__ == '__main__':
    unittest.main()
