/**
 * Public LibreTime 4.5 live-info-v2 response normalizer.
 * This module deliberately accepts unknown JSON, never HTML or private API fields.
 * @typedef {{ title: string, artist: string | null, kind: 'track' | 'webstream' | 'livestream' | 'unknown' }} Track
 * @typedef {{ previous: Track | null, current: Track | null, next: Track | null }} LiveTracks
 */

/** @param {unknown} value @returns {value is Record<string, unknown>} */
function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

/** @param {unknown} value @returns {string | null} */
function nonempty(value) {
  return typeof value === 'string' && value.trim() ? value.trim().slice(0, 240) : null;
}

/** @param {unknown} value @returns {Track | null} */
export function normalizeTrack(value) {
  if (!isObject(value)) return null;
  const meta = isObject(value.metadata) ? value.metadata : {};
  const sourceType = nonempty(value.type)?.toLowerCase();
  const kind = sourceType === 'track' || sourceType === 'webstream' || sourceType === 'livestream'
    ? sourceType : 'unknown';
  const title = nonempty(meta.track_title) ?? nonempty(meta.title) ?? nonempty(value.name);
  if (!title) return null;
  const artist = kind === 'track' ? (nonempty(meta.artist_name) ?? nonempty(meta.artist)) : null;
  return { title, artist, kind };
}

/**
 * Accept only the documented LibreTime 4.5 `tracks` shape. Malformed data
 * is rejected rather than treated as a fabricated playlist.
 * @param {unknown} value
 * @returns {LiveTracks | null}
 */
export function normalizeLiveInfo(value) {
  if (!isObject(value) || !isObject(value.tracks)) return null;
  return {
    previous: normalizeTrack(value.tracks.previous),
    current: normalizeTrack(value.tracks.current),
    next: normalizeTrack(value.tracks.next)
  };
}
