# RCAT Radio Network

สถานีวิทยุออนไลน์แบบผสม (Live DJ + AutoDJ) สำหรับ RCAT

## Architecture

- Broadcast engine: AzuraCast / Liquidsoap / Icecast
- Deployment strategy: shared Ubuntu Docker host, **LAN-only proof of concept first**
- Listener-facing portal: separate application, read-only Now Playing API
- Public streaming: not approved in this phase

## Project status

**RRN-00 — Infrastructure & Baseline Audit: pending execution on the actual server.**

No containers have been installed, no host ports opened and no existing services changed by this repository. Do not deploy AzuraCast until the security and regression gates are reviewed.

See `TRACKER.md` and `docs/` for the work plan. Read-only audit utilities are under `scripts/`.

## Safety boundaries

1. Never change the existing PDF HUB or AnyFlip Docker stacks in order to deploy radio.
2. Use no automatic Docker Engine updates, host-wide prune or premature public port forwarding.
3. Do not publish secrets, original server inventories, IP addresses or unredacted `docker compose config` output in public Issues.
4. Test the fully rendered AzuraCast Compose configuration before starting containers.
5. Verify user-defined roles, rights-cleared media, backup and rollback plans before LAN pilot.

**Repository note:** this is a planning and preflight project; it does not represent a running radio service.

## One-session LAN pilot (available for controlled testing)

Use [RUN-ONCE](docs/RUN-ONCE.md) for a single gated host test session. The maintained Docker-only runner can
perform a preflight and, only after signed-off gates, deploy **only** an isolated radio stack, verify existing-service
HTTP baselines, and provide a one-time human setup checkpoint before streaming tests.

```bash
# Legacy deploy mode is disabled. Use the Docker-only gated workflow below.
```

Do not run this on the shared host without reviewing the guide and choosing the correct
host private IPv4. The legacy deployment command above is **disabled**. The reviewed Docker-only
command does **not** change firewall/Reverse Proxy and does not run on GitHub.
Admin listens on loopback only; use the documented SSH tunnel. A passed GitHub CI
is **not** proof the live broadcast or production host has been tested.

## Recommended: Docker-only single-session LAN test

**No Python on Ubuntu Host.** Use the maintained `scripts/radioctl.sh`
wrapper around Docker Compose. Compose static audit runs in a disposable
container without host Docker socket access.

```bash
git clone https://github.com/yiwssx/rcat-radio-network.git
cd rcat-radio-network
bash scripts/radioctl.sh check 10.10.1.100
# After RRN-00/01/02 sign-off, prepare the private approval file
# as documented in docs/DOCKER-ONLY.md, then:
bash scripts/radioctl.sh deploy 10.10.1.100 --ack-shared-host
```

Read [the complete Docker-only runbook](docs/DOCKER-ONLY.md) before
executing it on the shared Docker server. The earlier
`scripts/one_round.py` runner remains available as a legacy option
but is **not required** for the primary operator workflow. GitHub CI is a
static check, not evidence the station has been installed.

## Operational recovery and monitoring

The [Backup & Restore runbook](docs/BACKUP-RESTORE.md) defines the
non-destructive, off-host backup process and **isolated** restoration
acceptance tests. A guide is not proof that backups, alerts or restores
are operating on the RCAT server; see RRN-06.

## Repository code delivery (deployment deferred)

Source-side components and automated tests are prepared for a supervised LAN
pilot: responsive listener portal, one-station Nginx API/stream allowlist,
fail-closed Docker-only controller, opt-in decoded-audio monitor, bounded
load/soak probe, backup-integrity manifest checker, and mock integration CI.

**This is not a claim that the RCAT host or actual station is working.**
AzuraCast administration, broadcasting schedules, real mobile playback,
alerts, off-host backup/isolated restore, host network and RT-01–17 test
evidence remain the operator's responsibility. Leave acceptance issues OPEN.

See [CODE-READY.md](docs/CODE-READY.md) for code/test coverage and safe
operator commands; [DOCKER-ONLY.md](docs/DOCKER-ONLY.md) for deployment gates.
