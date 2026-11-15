# RRN-27 — Read-only Listener metadata over existing HTTPS 443

**Status:** RMS public metadata file and minute cron installed and operator-accepted 2026-11-15. New CI-built Listener candidate prepared; listener HTML cutover and real-browser UAT not yet completed. Keep RRN-00–06 and UI #22 closed.

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

## Gate B — RMS metadata adoption: PASS (operator-accepted 2026-11-15)

1. **PASS:** Apache's actual radio 443 listener DocumentRoot was confirmed as `/var/www/radio-listener`; public metadata target was free.
2. **PASS:** Operator installed SHA-256 verified script at `/usr/local/sbin/rrn27-static-metadata-rms.py` from commit `e9b71f69361cfbfeab3aa4ebe6897dbd56b9ad5e`; file hash `5e4980473772808068f4ee9df95a9a6935009184452b7229c3ddd2dec13eb194`. No runtime/package changes.
3. **PASS:** `/usr/bin/python` exporter `--probe` succeeded, no write.
4. **PASS:** One `--apply` published only sanitized, expiring `radio-metadata.json`.
5. **PASS:** Operator observed `RRN27_PUBLIC_443=PASS`, `RRN27_SANITIZATION=PASS`, `RRN27_EXPIRY=PASS` through live Apache 443.
6. **PASS:** Operator's guarded installation checked duplicate jobs, installed one root-owned `/etc/cron.d/rrn27-radio-metadata` file (0644) with this line:

```cron
* * * * * root /usr/bin/python /usr/local/sbin/rrn27-static-metadata-rms.py --apply >/dev/null 2>&1
```

7. **CI PASS:** Existing `RRN-22 Listener release candidate` workflow now builds with `VITE_LIBRETIME_LIVE_INFO_URL=/radio-metadata.json` and checks the built JS includes the path. [Run #43689080202](https://github.com/yiwssx/rcat-radio-network/actions/runs/43689080202), PR head `9e7202d6588b6e3c9975591b058da568a1ff281d`, run-tested merge SHA `b807c385632a0f1dd51a6ebdc89b8a684283fcc9`, artifact `rrn22-listener-candidate-b807c385632a0f1dd51a6ebdc89b8a684283fcc9`. Svelte check, metadata tests, Vite build, local smoke, Chromium screenshots, artifact upload all succeeded. This does not imply a deployment.
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
- [x] RMS exact-SHA exporter `--probe`, `--apply`, public 443 sanitization/expiry and single minute Cron: PASS
- [x] Environment-configured Svelte CI build and candidate artifact: PASS
- [ ] Operator deploys exact CI artifact to RMS static listener after backup, preserving `radio-metadata.json`
- [ ] One real-browser UAT for Previous/Now/Next and unaffected player; then PR review/merge and Issue closure

**Disposition:** IOT and RMS metadata production feed PASS; Listener artifact CI PASS. Only Listener static deployment and browser acceptance remain; Issue #27 stays open.
