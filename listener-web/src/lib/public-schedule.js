/**
 * Validated, minimum-information, same-origin public LibreTime show schedule.
 * Input is produced by RRN-28 on the existing RMS host; never accept raw API.
 * @typedef {{ title: string, starts_at: string, ends_at: string }} PublicShow
 * @typedef {{ shows: PublicShow[] }} PublicSchedule
 */

const ZONE = 'Asia/Bangkok';
const STATION_ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+07:00$/;

/** @param {unknown} item @returns {item is Record<string, unknown>} */
const object = (item) => typeof item === 'object' && item !== null && !Array.isArray(item);

/** @param {unknown} raw @param {number} [now] @returns {PublicSchedule | null} */
export function parsePublicSchedule(raw, now = Date.now()) {
  if (!object(raw) || !object(raw.rcat_public_schedule) || !Array.isArray(raw.shows)) return null;
  const feed = raw.rcat_public_schedule;
  const seconds = now / 1000;
  if (feed.schema !== 1 || feed.timezone !== ZONE ||
      typeof feed.generated_at !== 'number' || typeof feed.expires_at !== 'number' ||
      !Number.isSafeInteger(feed.generated_at) || !Number.isSafeInteger(feed.expires_at) ||
      feed.generated_at > seconds + 60 || feed.expires_at <= seconds ||
      feed.expires_at <= feed.generated_at || feed.expires_at - feed.generated_at > 3600 ||
      raw.shows.length > 500) return null;
  /** @type {PublicShow[]} */
  const shows = [];
  for (const item of raw.shows) {
    if (!object(item) ||
        typeof item.title !== 'string' || !item.title.trim() || item.title.length > 160 ||
        typeof item.starts_at !== 'string' || typeof item.ends_at !== 'string' ||
        !STATION_ISO.test(item.starts_at) || !STATION_ISO.test(item.ends_at)) return null;
    const start = Date.parse(item.starts_at);
    const end = Date.parse(item.ends_at);
    if (!Number.isFinite(start) || !Number.isFinite(end) ||
        end <= start || end - start > 86400000) return null;
    shows.push({ title: item.title.trim(), starts_at: item.starts_at, ends_at: item.ends_at });
  }
  shows.sort((a, b) => a.starts_at.localeCompare(b.starts_at));
  return { shows };
}

/** Station-local dates, never dependent on listener browser time zone. */
export function scheduleDays(now = Date.now()) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: ZONE, year: 'numeric', month: '2-digit', day: '2-digit'
  }).formatToParts(now);
  /** @param {string} type */
  const n = (type) => Number(parts.find(part => part.type === type)?.value);
  const utcMidnight = Date.UTC(n('year'), n('month') - 1, n('day'));
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(utcMidnight + index * 86400000);
    const key = date.toISOString().slice(0, 10);
    const label = new Intl.DateTimeFormat('th-TH', {
      timeZone: 'UTC', weekday: 'short', day: 'numeric', month: 'short'
    }).format(date);
    return { date: key, label, today: index === 0 };
  });
}

/** @param {PublicShow} show */
export function showDate(show) { return show.starts_at.slice(0, 10); }
/** @param {string} iso */
export function showTime(iso) { return iso.slice(11, 16); }
