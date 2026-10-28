/**
 * Map AzuraCast's documented proxy mount into the same-origin listener URL.
 * A custom mount URL outside the RCAT station's /listen/ path is rejected.
 * The browser must never fetch the loopback-only admin port directly.
 */
export function resolveStreamUrl(raw, portalOrigin) {
  if (typeof raw !== 'string' || !raw.trim()) return null;
  try {
    const page = new URL(portalOrigin);
    const source = new URL(raw, page);
    if (!['http:', 'https:'].includes(page.protocol)) return null;
    if (!['http:', 'https:'].includes(source.protocol)) return null;
    if (!source.pathname.startsWith('/listen/rcat_radio/')) return null;
    // Reject encoded segments and traversal-like or arbitrary upstream paths.
    if (!/^\/listen\/rcat_radio\/[A-Za-z0-9._-]+$/.test(source.pathname)) return null;
    if (source.username || source.password || source.hash) return null;
    return page.origin + source.pathname + source.search;
  } catch {
    return null;
  }
}
