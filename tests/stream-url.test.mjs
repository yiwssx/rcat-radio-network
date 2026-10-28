import { test } from 'node:test';
import assert from 'node:assert/strict';
import { resolveStreamUrl } from '../portal/stream-url.mjs';

const portal = 'http://192.168.2.7:8750/';

test('reconstructs AzuraCast proxy path on the portal origin', () => {
  assert.equal(
    resolveStreamUrl('http://127.0.0.1:8700/listen/rcat_radio/radio.mp3', portal),
    'http://192.168.2.7:8750/listen/rcat_radio/radio.mp3'
  );
});

test('supports HTTPS same-origin proxy rather than downgrading to HTTP', () => {
  assert.equal(
    resolveStreamUrl('https://radio.test/listen/rcat_radio/low.aac?foo=1',
                     'https://radio.example.org/'),
    'https://radio.example.org/listen/rcat_radio/low.aac?foo=1'
  );
});

test('rejects other stations, admin URLs, injected schemes and credentials', () => {
  for (const raw of [
    'http://127.0.0.1:8700/admin',
    '/listen/other_station/radio.mp3',
    '/listen/rcat_radio/',
    'javascript:alert(1)',
    'data:audio/mp3,abc',
    'http://user:pass@127.0.0.1:8700/listen/rcat_radio/radio.mp3',
    'http://127.0.0.1:8700/listen/rcat_radio/radio.mp3#secret',
    '',
    null
  ]) {
    assert.equal(resolveStreamUrl(raw, portal), null, String(raw));
  }
});

test('never exposes the loopback administration origin to listeners', () => {
  const actual = resolveStreamUrl('http://127.0.0.1:8700/listen/rcat_radio/radio.mp3', portal);
  assert.ok(actual.startsWith('http://192.168.2.7:8750/'));
  assert.ok(!actual.includes(':8700'));
});

test('rejects encoded paths and arbitrary nested mounts', () => {
  for (const raw of [
    '/listen/rcat_radio/../other_station/radio.mp3',
    '/listen/rcat_radio/secret%2fadmin',
    '/listen/rcat_radio/track/metadata.json',
    '/listen/rcat_radio/%2e%2e',
  ]) {
    assert.equal(resolveStreamUrl(raw, portal), null, raw);
  }
});
