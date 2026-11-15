# RRN-27 — Read-only Listener metadata over existing HTTPS 443

**Status:** source-only candidate, owner authorized investigation/preparation on 2026-11-15. NO host execution or deployment implied. Keep RRN-00–06 and UI #22 closed.

## Operator observations (2026-11-15 11:30 Asia/Bangkok)

- HTTPS 443 path /api/live-info-v2/ returned Apache 404 text/html.
- HTTPS 8700 /api/live-info-v2/ returned HTTP 500, JSON prefix plus HTML error page; the full body is invalid JSON.
- JSON prefix reported tracks.previous, tracks.current=null, tracks.next=null; null current alone does not prove streaming failure.
- No Access-Control-Allow-Origin was observed on that 500 response. Successful HTTP 200 CORS behavior is unknown.
- Raw upstream includes internal paths, IDs, hashes and other unnecessary fields; never proxy the whole body to public 443.
- Server-side cause of 500 is NOT established. Do not parse a truncated JSON prefix or bypass non-200 responses.

## Minimal solution

- On existing RMS (CentOS Apache TLS 443), a standard-library Python 3 script from scripts/rrn27-static-metadata-rms.py reads the already available IOT LAN LibreTime API, never credentials or a private URL in browser JS.
- Requires upstream 200, application/json, exactly one valid JSON object, max 256 KiB and no redirects. Outputs only previous/current/next, title, artist, kind and an expiry timestamp.
- Atomic output is /var/www/radio-listener/radio-metadata.json served through the existing HTTPS 443 document root; no Apache proxy, new port, new container or audio changes.
- A stopped scheduler can leave the last snapshot for at most 180 seconds; frontend validates optional rcat_public_feed timestamps and then shows unavailable state.
- Existing Vite client uses build-time VITE_LIBRETIME_LIVE_INFO_URL=/radio-metadata.json after the operator verifies the same-origin file. An old Vite build with blank env remains disconnected.

## Gate A — Diagnose existing 500 on IOT; read-only operator commands

```bash
curl --noproxy '*' -sS --max-time 8 -o /dev/null \
  -w 'IOT_API_HTTP=%{http_code} CONTENT_TYPE=%{content_type}\n' \
  -H 'Accept: application/json' http://127.0.0.1:8700/api/live-info-v2/
sudo docker logs --since 5m --tail 80 rcat_radio_network-legacy-1 2>&1 | grep -Ei 'error|fatal|exception|trace|500' | tail -n 30
sudo docker logs --since 5m --tail 80 rcat_radio_network-nginx-1 2>&1 | grep -Ei 'error|fatal|exception|500' | tail -n 30
```

Review legacy error logs privately if these do not show the cause (LibreTime official troubleshooting). Share only redacted error category; never dump credentials, filenames or full stack traces to public GitHub. No restart, upgrades, playout or config changes without a diagnosed fault and radio-only backup. API 200 with a *single* valid JSON body is a hard prerequisite.

## Gate B — Approved operator-only RMS adoption (NOT EXECUTED)

1. Verify upstream fixed and python3 already installed on RMS. Do not install packages in this scope. Confirm existing radio webroot and absence of unrelated radio-metadata.json.
2. Install the **reviewed exact PR SHA** script root-owned at /usr/local/sbin/rrn27-static-metadata-rms.py mode 0755; validate downloaded checksum.
3. Probe (no write): sudo /usr/bin/python3 /usr/local/sbin/rrn27-static-metadata-rms.py --probe. If BLOCKED, STOP.
4. One apply (writes only the sanitized file): sudo /usr/bin/python3 /usr/local/sbin/rrn27-static-metadata-rms.py --apply.
5. Verify public HTTPS 443 /radio-metadata.json returns HTTP 200, application/json, only whitelisted fields and unexpired timestamps, before scheduling.
6. After checking no duplicate job, install ONE root-owned /etc/cron.d/rrn27-radio-metadata file (0644) with this single line:

```cron
* * * * * root /usr/bin/python3 /usr/local/sbin/rrn27-static-metadata-rms.py --apply >/dev/null 2>&1
```

7. Rebuild accepted Svelte source with VITE_LIBRETIME_LIVE_INFO_URL=/radio-metadata.json at Vite build time; reuse existing CI candidate workflow. Verify the candidate source/version matches the intended deployment.
8. With scoped cutover approval, back up RMS static files, deploy only Listener assets, PRESERVE radio-metadata.json (no blind rsync --delete), and test once in real browser including null current/next and playing audio unaffected.

## Rollback

- Restore only the previous RMS Listener static backup and original compiled assets.
- Remove only the single RRN-27 cron entry and its root-owned executable, and delete radio-metadata.json ONLY after confirming the rcat_public_feed.schema=1 marker.
- No Apache reload is needed for a static file; don't touch LibreTime/Icecast/Show Source, firewall, DNS, certificates or other RCAT systems.

## Evidence

- [x] External operator HTTP responses and schema evidence
- [x] Minimal code-only candidate and focused isolated checks
- [ ] Private IOT logs identify root cause and operator fixes 500; prove upstream 200 JSON
- [ ] RMS one-pass probe / static file proof and scheduled freshness
- [ ] Approved exact frontend build, rollback backup and one real browser UAT

**Disposition:** PREPARED / HOST-BLOCKED. Issue #27 remains open.
