# RCAT Radio Network — Backup, Monitoring and Recovery Runbook (RRN-06)

**Status:** Procedures prepared; **no backup and no restoration have been
executed or verified on the RCAT production server**.

## Operational ownership

AzuraCast uses Docker named volumes for its database, station media,
upload files and backup storage. The Docker Compose project is
`rcat_radio_pilot` and its backing volumes must never be deleted
during diagnostics or rollback. Secrets in `deployment/.env` and
`deployment/azuracast.env` must be preserved in a secure offline
credential repository; they must not be committed to GitHub.

## Backup path for the LAN pilot

Use **AzuraCast Admin → System Administration → Backups** for a
manual backup, optionally with station media included.

1. Make sure there is sufficient backup space and choose a destination
   *outside* the radio container and ideally outside the Docker host.
2. Use an authorized Admin login through the **127.0.0.1:8700 SSH tunnel**.
3. Run a backup through the AzuraCast UI and confirm its completion.
4. Download/export an encrypted copy to approved, access-controlled
   off-host storage. Retain at least one previous known-good version.
5. Record backup date, size, AzuraCast image digest, station settings,
   whether media are included, and SHA-256 checksum of the final archive.
6. Also safeguard the two local environment files, **separately** from
   the public repo and from ordinary issue attachments.

Upstream notes that UI backups need not interrupt ongoing broadcasts,
but this must still be verified for the actual pilot runtime.

**Do not** use the stock AzuraCast `docker.sh` auto-updater or installer
on the existing shared host solely to perform a backup. That script
has different assumptions and may change the deployment configuration.

## Restoration is a separate, gated operation

Never restore a trial archive directly over the active station merely
to test it. Upstream backup restoration **replaces the existing
installation's stored data**. Instead:

1. Prepare a clean, isolated VM/test Docker host with adequate capacity.
2. Install a compatible version of AzuraCast and record the exact image.
3. Import the archive into the isolated test installation through the
   officially supported Restore workflow for that version.
4. Verify station/media presence, users/roles, playlists, scheduler,
   actual audio stream and Now Playing API.
5. Verify no connections from the restored environment target the
   production radio, PDF HUB, or AnyFlip networks.
6. Only after this evidence is accepted can RT-14 (backup/restore) be
   marked passed.

Do not run `docker compose down -v`, `docker volume prune`,
`docker system prune` or manually delete volume mounts to recover
from a failed installation.

## Non-destructive triage on the shared host

```bash
cd ~/rcat-radio-network
bash scripts/radioctl.sh status
bash scripts/radioctl.sh verify 10.10.1.100
bash scripts/radioctl.sh logs
```

`verify` checks station metadata, five local streaming responses and
the predeploy HTTP baseline for PDF HUB/AnyFlip. It does **not**
determine whether the actual audio is silent, or validate
cross-network exposure.

Observe container restarts, host disk growth, memory pressure and
stream quality independently. The acceptance plan calls for a full
24-hour soak (RT-13), silence/fallback testing (RT-07) and 5/20/50
listener load testing (RT-12). No monitoring system, alert delivery
or restore job is yet claimed to be operating automatically.

## Radio-only stop on incidents

```bash
bash scripts/radioctl.sh stop
```

This stops only the `rcat_radio_pilot` project's `web` and `portal`
services. It preserves the radio's named volumes and does not restart,
prune or otherwise change the PDF HUB or AnyFlip stacks.

Immediately repeat those applications' **real conversion and
download workflows**, not just HTTP status probes, and investigate
any host resource or network regression before attempting restart.

## Go/no-go

The RRN-06 issue remains open until the following exists on the real
server: successful off-host backups; a tested restore in an isolated
environment; stream-down and silence alerting; ownership/escalation;
and documented storage/retention policy.

Upstream references:
- https://www.azuracast.com/docs/administration/backup-and-restore/
- https://www.azuracast.com/docs/administration/docker/
