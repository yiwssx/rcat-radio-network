# RRN-27 — Read-only Listener metadata over existing HTTPS 443

**Status:** source-only candidate, owner authorized investigation/preparation on 2026-11-15. Radio host recovered by operator and RMS full JSON validated. Metadata exporter not installed/deployed. Keep RRN-00–06 and UI #22 closed.

## Operator observations (2026-11-15 11:30 Asia/Bangkok)

- HTTPS 443 path /api/live-info-v2/ returned Apache 404 text/html.
- HTTPS 8700 /api/live-info-v2/ returned HTTP 500, JSON prefix plus HTML error page; the full body is invalid JSON.
- JSON prefix reported tracks.previous, tracks.current=null, tracks.next=null; null current alone does not prove streaming failure.
- No Access-Control-Allow-Origin was observed on that 500 response. Successful HTTP 200 CORS behavior is unknown.
- Raw upstream includes internal paths, IDs, hashes and other unnecessary fields; never proxy the whole body to public 443.
- Server-side cause of 500 is NOT established. Do not parse a truncated JSON prefix or bypass non-200 responses.

## Minimal solution

- On existing RMS (CentOS 7 Apache TLS 443), the **Python 2.7/3 standard-library-compatible** script `scripts/rrn27-static-metadata-rms.py` reads the IOT LAN LibreTime API; no Python 3 installation, credentials or internal URL in browser JS. RMS's installed `python` interpreter is available and already parsed the same upstream JSON successfully.
- Requires upstream 200, application/json, exactly one valid JSON object, max 256 KiB and no redirects. Outputs only previous/current/next, title, artist, kind and an expiry timestamp.
- Atomic output is /var/www/radio-listener/radio-metadata.json served through the existing HTTPS 443 document root; no Apache proxy, new port, new container or audio changes.
- A stopped scheduler can leave the last snapshot for at most 180 seconds; frontend validates optional rcat_public_feed timestamps and then shows unavailable state.
- Existing Vite client uses build-time VITE_LIBRETIME_LIVE_INFO_URL=/radio-metadata.json after the operator verifies the same-origin file. An old Vite build with blank env remains disconnected.

## Gate A — IOT/RMS upstream validation: PASS (operator evidence, 2026-11-15)

- An initial radio outage was caused by **nine of ten existing radio containers being stopped**; Nginx could not resolve required Compose DNS aliases `legacy` then `api`. The operator restored only the original containers in dependency order, without recreation or data removal.
- Final host snapshot: **all ten containers Up**; LibreTime API `http://10.10.1.100:8700/api/live-info-v2/` returned **HTTP 200, application/json**. PostgreSQL, RabbitMQ and API health states were still **starting** in that instant; this does not certify audio playout.
- On **RMS** (not IOT), the operator confirmed `/usr/bin/python`, `/usr/bin/php`, `/usr/bin/curl`; **no `python3` executable or `jq`**. The Python standard-library read against the IOT LAN returned **`RRN27_RMS_LAN_JSON=PASS`**, validating HTTP 200, JSON content-type, bounded full-body parsing and presence of `previous`, `current`, `next` without printing metadata.
- Therefore **do not re-run LAN validation** or install Python 3 to complete RRN-27. Prior external HTTPS :8700 HTTP 500 with trailing HTML was historical and need not be investigated further unless it recurs. Public browser JS must not consume the raw :8700 metadata.

### Trust boundary

The RMS static exporter exposes *only* sanitized, expiring `/radio-metadata.json` through the existing HTTPS 443 listener origin, avoiding cross-origin/CORS and exposure of private LibreTime fields. Successful IOT/RMS LAN validation does **not** prove the public 443 static file exists until the operator performs the controlled adoption below.

## Gate B — Approved operator-only RMS adoption (NOT EXECUTED)

1. **Already passed:** RMS has a working `/usr/bin/python` and parsed the full upstream JSON. Confirm that Apache's actual radio Listener DocumentRoot is `/var/www/radio-listener` before applying; this script intentionally refuses to create an unknown webroot. Confirm that `/radio-metadata.json` does not already belong to another application.
2. Fetch the **reviewed exact PR commit** of the Python 2.7/3-compatible script, verify its checksum, and install it root-owned at `/usr/local/sbin/rrn27-static-metadata-rms.py` mode 0755. Do not alter `/usr/bin/python` or install packages.
3. Probe (no write): sudo /usr/bin/python /usr/local/sbin/rrn27-static-metadata-rms.py --probe. If BLOCKED, STOP.
4. One apply (writes only the sanitized file): sudo /usr/bin/python /usr/local/sbin/rrn27-static-metadata-rms.py --apply.
5. Verify public HTTPS 443 /radio-metadata.json returns HTTP 200, application/json, only whitelisted fields and unexpired timestamps, before scheduling.
6. After checking no duplicate job, install ONE root-owned /etc/cron.d/rrn27-radio-metadata file (0644) with this single line:

```cron
* * * * * root /usr/bin/python /usr/local/sbin/rrn27-static-metadata-rms.py --apply >/dev/null 2>&1
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
- [x] Radio host recovered: 10/10 existing Containers Up; IOT API 200/application/json
- [x] RMS confirmed full strict HTTP 200 JSON parsing and `tracks.previous/current/next` via existing Python interpreter
- [x] Draft exporter adapted for Python 2.7/3 without new packages (pending focused candidate CI)
- [ ] RMS one-pass probe / static file proof and scheduled freshness
- [ ] Approved exact frontend build, rollback backup and one real browser UAT

**Disposition:** IOT and RMS upstream validation PASS; exporter/source candidate prepared. RMS publish and Listener cutover NOT EXECUTED. Issue #27 remains open.
