import assert from 'node:assert/strict';
import { normalizeLiveInfo, normalizeTrack } from '../src/lib/live-info.js';

const autoDj = normalizeLiveInfo({
  tracks: {
    previous: { type: 'track', name: 'Artist P - Track P', metadata: { artist_name: 'Artist P', track_title: 'Track P' } },
    current: { type: 'track', name: 'Artist C - Track C', metadata: { artist_name: 'Artist C', track_title: 'Track C' } },
    next: { type: 'track', name: 'Artist N - Track N', metadata: { artist_name: 'Artist N', track_title: 'Track N' } }
  }
});
assert.deepEqual(autoDj?.current, { title: 'Track C', artist: 'Artist C', kind: 'track' });
assert.equal(autoDj?.previous?.title, 'Track P');
assert.equal(autoDj?.next?.title, 'Track N');
assert.deepEqual(normalizeLiveInfo({ tracks: { current: { type: 'livestream', name: 'Live DJ' } } })?.current, { title: 'Live DJ', artist: null, kind: 'livestream' });
assert.deepEqual(normalizeLiveInfo({ tracks: {} }), { previous: null, current: null, next: null });
assert.equal(normalizeLiveInfo({ current: { name: 'wrong schema' } }), null);
assert.equal(normalizeLiveInfo('<html>login</html>'), null);
assert.equal(normalizeTrack({type:'track',name: 3}), null);
assert.equal(normalizeTrack({type:'track',name: 'A'.repeat(1000)})?.title.length, 240);
assert.equal(normalizeTrack({type:'webstream',name:'Community program',metadata:{artist_name:'unsafe name'}})?.artist, null);
console.log('PASS: 10 focused LibreTime live-info-v2 normalization checks');
