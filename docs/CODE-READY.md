# RRN Code Delivery — prepared without host installation

**Date:** 2026-10-28. **Scope:** All repository-side deliverables prepared for review.
No RCAT Docker containers are installed/changed by GitHub Actions, and
**no** actual broadcast, operational or security acceptance is asserted.

## Code / operations ownership split

| Tracker | Repository-side deliverable | Owner-performed later |
|---|---|---|
| RRN-00 | `radioctl.sh check`, read-only preflight, protected baseline | Host inventory; resource and port evidence; existing PDF HUB/AnyFlip workflow baseline |
| RRN-01 | Security architecture, gate documentation | Network/firewall/VLAN and server choice sign-off |
| RRN-02 | Separate Compose, static audit, approval gate, CI checks | Review AzuraCast official release/installer, rendered config and image digest on the target host |
| RRN-03 | Approval-gated `radioctl.sh deploy/verify/status/stop` | Real deployment after explicit approval and rollback preparedness |
| RRN-04 | Live/AutoDJ settings and fallback test procedures | Create DJ accounts, playlist, schedule; test live and fallback with an actual source |
| RRN-05 | Nginx station-scoped portal, resilient HTML5 player, metadata and CI mock integration | Browser/mobile/iOS listening and real AzuraCast compatibility |
| RRN-06 | Opt-in audio-decoding monitor with stateful alerts; offline backup checksum/CRC verifier | Start monitor, configure alert receiver, off-host backups, isolated restoration |
| RRN-07 | Bounded 5/20/50-listener HTTP load/soak runner and test plan RT-01…17 | Perform 24-hour endurance, rights, security, PDF conversion and AnyFlip download regression |
| RRN-08 | Documentation and acceptance checklist | Operator training, recovery drill, signed handover |

## Important design decisions

- Radio, portal and optional utilities never share PDF HUB or AnyFlip volumes or
  Compose projects. No host-wide prune, Docker update or reverse proxy changes.
- `monitor` and `acceptance` services have **Compose profiles** and are never
  launched by the default `up -d web portal` path. No Docker socket access.
- The monitor checks **decoded 16-bit PCM RMS** from a short ffmpeg sample,
  not merely HTTP 200. Alerts require consecutive failing samples to reduce
  false positives. It emits structured JSON logs and optionally posts to an
  operator-provided HTTPS webhook; no webhook is configured by default.
- The standalone load tool checks only bounded public read-only listener URLs
  on a private address; it **does not** decode audio or prove continuous 24-hour
  broadcast (a timed run performs periodic bounded sample requests).
- The backup tool verifies SHA-256 and ZIP CRC where applicable **without
  extraction**. Backup integrity does not prove isolated restoration.
- Portal CSP restricts media to its own origin; Nginx exposes only the RCAT
  Now Playing API path and RCAT stream proxy, not arbitrary administration API.
- All deployment approvals and evidence stay in private local files. A checked
  approval file cannot prove the underlying human decisions by itself.
- Mutable upstream image tags are retained for the LAN trial; operator
  must choose and pin reviewed immutable image digests before production.

## Non-deployment CI suite

`audit-unit-tests.yml` runs:

1. Python stdlib unit tests for preflight, Compose safety, approval gates,
   monitoring, backup integrity, and acceptance runner.
2. JavaScript tests for strict stream URL resolution; Bash syntax and CLI help.
3. Compose rendered-config audit in a disposable isolated container.
4. Nginx syntax check and actual route allowlist integration against a benign
   mock AzuraCast backend. The mock contains **no real audio** or secrets.
5. Build and CLI entrypoint check of the optional ffmpeg monitor image.

CI green is **code-ready**, not production-ready. Report host-specific
errors privately and keep RRN-00–RRN-08 issues OPEN until evidence passes.

## Future operator commands (do not run before RRN gates)

```bash
cd ~/rcat-radio-network
git pull --ff-only
bash scripts/radioctl.sh check <APPROVED_RFC1918_IP>
# Review/approve RRN-00/01/02 before deploying. See DOCKER-ONLY.md.
```

After owner-configured station is broadcasting, use the **existing** Compose
project. Never combine opt-in profiles with a broad, unreviewed `up`.

### Monitor (owner enables after radio is running)

```bash
docker compose -p rcat_radio_pilot --env-file deployment/.env \
  -f deployment/compose.pilot.yaml --profile monitor build monitor
docker compose -p rcat_radio_pilot --env-file deployment/.env \
  -f deployment/compose.pilot.yaml --profile monitor up -d --no-deps monitor
docker compose -p rcat_radio_pilot --env-file deployment/.env \
  -f deployment/compose.pilot.yaml logs --tail 100 monitor
```

Optional webhook: `RRN_ALERT_WEBHOOK_URL` must be an authorized **HTTPS**
endpoint supplied via protected local environment to Compose when starting.
Never commit it or paste into an issue. Receiver protocol is simple POST JSON
with `station`, `event`, `reason`, `time`; owner should verify successful
delivery, notification handling and escalation. If no webhook is configured,
alerts appear in monitor logs only.

### Periodic load and soak (owner runs after station setup)

```bash
docker compose -p rcat_radio_pilot --env-file deployment/.env \
  -f deployment/compose.pilot.yaml --profile acceptance \
  run --rm --no-deps acceptance --clients 5
# Repeat with --clients 20 and --clients 50 ONLY after host capacity check.
# For 24-hour *periodic probe*, not continuous full-stream soak:
# --clients 5 --duration 86400 --interval 60
```

### Backup integrity (owner performs after exporting real off-host backup)

Requires Python 3.12 on a separate workstation or a temporary Python
container with an approved read-only backup mount. Does **not** perform backup
creation or restore.

```bash
python3 scripts/backup_check.py create --archive /secure/azuracast-backup.zip \
  --manifest /secure/azuracast-backup.manifest.json
python3 scripts/backup_check.py verify --archive /secure/azuracast-backup.zip \
  --manifest /secure/azuracast-backup.manifest.json
```

Run a full isolated restore separately and record RT-14 evidence. Maintain
off-host copies, retention, and encrypted credentials under owner control.
