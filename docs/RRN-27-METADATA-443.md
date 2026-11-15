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

## Gate A — IOT LAN API: transport PASSED; verify JSON validity once (read-only)

**Operator evidence, 2026-11-15:** `ss` shows `docker-proxy` listening on **10.10.1.100:8700**. `docker ps` confirms the existing Nginx container's `10.10.1.100:8700 -> 8080/tcp` binding. Both direct IOT LAN request and the same URL with `Host: radio.rcat.ac.th:8700` / `X-Forwarded-Proto: https` returned **HTTP 200, application/json**. `127.0.0.1:8700` connection refusal was an **incorrect target interface**, not evidence of outage. Last legacy log filter returned no matching output (not proof that server errors never occurred).

The earlier public HTTPS :8700 **500 with JSON followed by HTML** is a distinct observation. Treat it as not reproduced by these IOT LAN probes, **not proven fixed**; private logs may be needed only if the issue recurs. Do not restart containers or change headers just to chase a historical transient.

The command below checks the single remaining unknown: **full JSON-body validity and expected slots**, without printing any track metadata or secret values. Run once on **IOT**:

```bash
set -o pipefail
curl --noproxy '*' --fail --silent --show-error --max-time 8 \
  --max-filesize 262144 -H 'Accept: application/json' \
  'http://10.10.1.100:8700/api/live-info-v2/' |
python3 -c 'import json,sys; x=json.load(sys.stdin); t=x.get("tracks") if isinstance(x,dict) else None; assert isinstance(t,dict) and all(k in t for k in ("previous","current","next")), "unexpected tracks schema"; print("RRN27_IOT_JSON=PASS SLOTS=previous,current,next")'
```

If this fails, stop and inspect only targeted private LibreTime legacy/nginx errors; avoid copying raw body, internal filepaths, song names, cookie values or stack traces into public GitHub. A **valid full body** is a hard prerequisite before RMS adoption. Operator approval is required for any actual IOT repair if 500 recurs.

### Public-edge distinction

A valid IOT 200 response proves the private upstream is suitable for the sanitized RMS snapshot. It does **not** prove public HTTPS :8700 returns 200, nor does it mean public 8700 should be used by browser JavaScript. RRN-27 intentionally bypasses its cross-origin/CORS and raw-metadata problems by publishing a minimized static file on the existing public 443 listener origin.

## Gate B — Approved operator-only RMS adoption (NOT EXECUTED)

1. After full IOT JSON validation, verify python3 already installed on RMS and that RMS can reach the existing IOT LAN IP. Do not install packages in this scope. Confirm existing radio webroot and absence of unrelated radio-metadata.json.
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
- [x] Operator confirmed IOT 10.10.1.100:8700 binding and HTTP 200/application/json on both private-LAN header variants (earlier public 500 root cause unproven; no unjustified service restart)
- [ ] Verify one complete valid JSON body with all three expected slots from IOT
- [ ] RMS one-pass probe / static file proof and scheduled freshness
- [ ] Approved exact frontend build, rollback backup and one real browser UAT

**Disposition:** PREPARED / HOST-BLOCKED. Issue #27 remains open.
