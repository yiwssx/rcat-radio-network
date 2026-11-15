# RRN-28 — Real LibreTime program schedule in the public Listener

## Scope and evidence

Owner approved showing a **daily / next-seven-days** program schedule inside a compact
dialog, hiding the nonfunctional "Station Activities" tile, and avoiding redundant
test/redeploy loops. This is an extension of the existing radio Listener candidate
in Draft PR #36, NOT a second broadcast or calendar service.

LibreTime 4.x documents its public, unauthenticated legacy
`/api/week-info/` schedule API. It returns `monday` through `sunday` arrays
of show names and start/end timestamps. This API is separate from the already
accepted `/api/live-info-v2/` track metadata and requires public schedule access
enabled in LibreTime Settings/General (on older UI: System/Preferences).
Reference: https://libretime.org/docs/user-manual/playout-history/#exporting-the-schedule

## Implementation (minimal / no new infrastructure)

1. On **RMS** (existing CentOS7, Apache HTTPS 443), the Python-2-compatible
   `scripts/rrn28-public-schedule-rms.py` reads the **existing IOT LAN**
   `http://10.10.1.100:8700/api/week-info/`. Only accept HTTP 200 JSON
   with the documented seven weekday arrays, bounded response size and no redirects.
   Refuse HTML, JSONP, 401, malformed and oversized data without writing anything.
2. Project only show **title**, **starts_at**, **ends_at** and public
   `rcat_public_schedule` schema/timezone/freshness metadata. Remove internal IDs,
   URLs, file paths, cookies, credentials and all other upstream data.
3. Use the station's **Asia/Bangkok (+07:00)** calendar for the rolling seven-day
   window. A show appears **only when scheduled in LibreTime**; an empty schedule
   is a valid empty result. No fabricated AutoDJ entries.
4. Publish atomic `/var/www/radio-listener/radio-schedule.json` through the
   **existing** public `https://radio.rcat.ac.th/` origin. One separate
   ten-minute root cron task refreshes it. The frontend rejects stale data after
   60 minutes and presents a nonmisleading unavailable state.
5. `listener-web/src/lib/ScheduleDialog.svelte` opens via the top navigation
   or the shortcut tile, offers a today/day selector and all seven days, and
   uses native `<dialog>` Escape/focus support. It fetches only the sanitized
   same-origin JSON **on open**, so the audio player is independent.
6. The inactive Station Activities shortcut is hidden, not populated with filler.
   Existing News, Contact, playback, Icecast, LibreTime Admin, and metadata exporter
   remain unchanged. No Apache reload/Docker restart is needed.

## One-pass host adoption (operator action; not yet claimed)

- Use the exact reviewed release SHA of the schedule Python script and verify its
  SHA-256 before running the real RMS `/usr/bin/python script --probe`. It prints
  **only** `RRN28_SCHEDULE_PROBE=PASS COUNT=N`; a zero count means LibreTime has
  no scheduled shows in the next seven days (not an API failure).
- If upstream returns HTTP 401/403, **stop**. Do not alter LibreTime from this script.
  The station operator may enable its documented public schedule/API setting via
  the LibreTime UI. Repeat only the previously blocked schedule probe once.
- Only after the probe, publish once with `--apply` and request
  `https://radio.rcat.ac.th/radio-schedule.json` over the existing TLS 443 to
  verify **only** the expected public keys and freshness. Then install the single
  schedule cron in `/etc/cron.d/rrn28-radio-schedule` (root 0644):
  `*/10 * * * * root /usr/bin/python /usr/local/sbin/rrn28-public-schedule-rms.py --apply >/dev/null 2>&1`
- Reuse the existing Listener CI workflow/build that already builds
  `VITE_LIBRETIME_LIVE_INFO_URL=/radio-metadata.json`. The schedule URL is fixed
  to same-origin `/radio-schedule.json`, so **no extra build-time secret/env var**.
- Deploy exactly the **successful CI artifact** (tar + its own SHA-256) with a
  rollback backup. Copy assets first, replace `index.html` last; preserve both
  `radio-metadata.json` and `radio-schedule.json`, existing cron and all
  Apache configuration. No `rsync --delete` or multi-service restarts.
- Owner/browser acceptance: the actual dialog opens, switch day/week, empty schedule
  is honest, close/Escape works, audio stream player is unchanged. No redundant
  IOT diagnostics, metadata reprobes, or repeated old screenshots are required.

## Rollback

Restore only backed-up Listener HTML/static assets (do not restore over the JSON
cache files). To retire RRN-28 schedule feed, remove *only* its dedicated cron and
script, and remove `radio-schedule.json` only after confirming its
`rcat_public_schedule.schema=1` marker. Preserve the functioning RRN-27 track
metadata feed and its minute cron, Apache TLS, Icecast, all Docker services.

**Current state:** Candidate GitHub Actions [#43690669765](https://github.com/yiwssx/rcat-radio-network/actions/runs/43690669765) **SUCCESS** on source commit `b80aa73e659c01eaae1047a27e4bee2152c6b7ed` (afterwards only documentation changed). Artifact `rrn22-listener-candidate-e8be14889c833b23ee4982097950d8ad9d97c084` (artifact ID `14151739921`), contains static tar.gz + matching SHA256 and browser screenshots.

Checksum-pinned RMS schedule source:
- `scripts/rrn28-public-schedule-rms.py` at commit `b80aa73e659c01eaae1047a27e4bee2152c6b7ed`
- `SHA256=d04e17036664e72ee5cadf270bbc5679656d73a2035ec6d63992543e54528c3c`

All code/CI preparation is complete. Actual RMS schedule API probe, publication,
and Listener cutover still require the operator command and browser UAT; do not
claim Host or visual UAT passed before that evidence.
