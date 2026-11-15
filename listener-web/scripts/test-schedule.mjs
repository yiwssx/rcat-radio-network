import assert from 'node:assert/strict';
import { parsePublicSchedule, scheduleDays, showDate, showTime } from '../src/lib/public-schedule.js';

const now = Date.parse('2026-11-15T07:10:00+07:00');
const feed = {
  rcat_public_schedule: {
    schema: 1, timezone: 'Asia/Bangkok',
    generated_at: Math.floor(now / 1000) - 20,
    expires_at: Math.floor(now / 1000) + 3540
  },
  shows: [{
    title: 'เพลงเกษตรไทย',
    starts_at: '2026-11-15T08:00:00+07:00',
    ends_at: '2026-11-15T09:00:00+07:00'
  }]
};

assert.equal(parsePublicSchedule(feed, now)?.shows[0].title, 'เพลงเกษตรไทย');
assert.equal(parsePublicSchedule({ ...feed, shows: [] }, now)?.shows.length, 0);
assert.equal(parsePublicSchedule({ ...feed, rcat_public_schedule: { ...feed.rcat_public_schedule, expires_at: now / 1000 - 1 } }, now), null);
assert.equal(parsePublicSchedule({ ...feed, rcat_public_schedule: { ...feed.rcat_public_schedule, timezone: 'UTC' } }, now), null);
assert.equal(parsePublicSchedule({ ...feed, shows: [{ ...feed.shows[0], starts_at: '2026-11-15 08:00:00' }] }, now), null);
assert.equal(parsePublicSchedule({ ...feed, shows: [{ ...feed.shows[0], ends_at: '2026-11-15T07:00:00+07:00' }] }, now), null);
assert.equal(parsePublicSchedule({ ...feed, shows: [{ ...feed.shows[0], title: null }] }, now), null);
assert.equal(scheduleDays(now)[0].date, '2026-11-15');
assert.equal(scheduleDays(now)[6].date, '2026-11-21');
assert.equal(showDate(feed.shows[0]), '2026-11-15');
assert.equal(showTime(feed.shows[0].starts_at), '08:00');
console.log('RRN28_SCHEDULE_FRONTEND_TESTS=PASS');
