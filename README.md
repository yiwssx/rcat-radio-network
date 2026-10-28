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
