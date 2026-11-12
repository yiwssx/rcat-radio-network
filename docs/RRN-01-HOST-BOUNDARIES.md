# RRN-01 — Icecast + LibreTime Shared-Host Boundaries

**Updated:** November 12, 2026  
**Status:** DESIGN COMPLETE — LIVE HOST PREFLIGHT PENDING  
**Stack:** [RRN-00 accepted Icecast + LibreTime decision](./RRN-00-STACK-DECISION.md)  
**Scope:** Planning only; no server, Production, DNS, proxy or firewall changes.

## Historical evidence — reuse, do not repeat

- Operator previously removed obsolete `rcat_radio_pilot` (two Docker containers, one network, ten named volumes) and saw ports `8600/8605/8606/8700/8750` free at that time.
- Existing PDF HUB and AnyFlip returned HTTP 200 after that removal.
- Previous operator inventory recorded Ubuntu 26.04.1 LTS / x86_64 and LAN interface `10.10.1.100`.
- **None of these observations proves current port/resource availability.** No current live host inspection has been performed.

Do not repeat successful removal checks or unrelated service tests merely to produce additional evidence.

## Selected architecture and trust boundaries

Use the **official LibreTime 4.5.0** upstream Compose with its **bundled Icecast 2.4.4**. The upstream ten services are `postgres`, `rabbitmq`, `playout`, `liquidsoap`, `analyzer`, `worker`, `api`, `legacy`, `nginx`, and `icecast`.

- **Compose project name:** `rcat_radio_network`, separate from retired `rcat_radio_pilot`, PDF HUB, AnyFlip and deployment-control systems.
- **Proposed deployment checkout:** `/opt/rcat-radio-network/`.
- **Proposed private credentials and generated config:** `/etc/rcat-radio-network/`, permission-restricted and outside public Git.
- **Data:** three LibreTime Compose named volumes (`postgres_data`, `libretime_storage`, `libretime_playout`) prefixed with the isolated radio Compose project. Preserve data on stop or rollback.
- **Proposed backup location:** `/var/backups/rcat-radio-network/`; exact backup/retention mechanism belongs to RRN-06.
- **Networking:** LibreTime connects to bundled Icecast over the radio-only Compose network using service name `icecast`, internal port `8000`, from the official enabled Icecast output in `docker/config.template.yml`.
- **No separate DNAS process, proprietary binary, extra stream gateway or custom panel.** SHOUTcast research was superseded by owner approval of Icecast.

All locations and bindings are proposals, not resources verified on the server today.

## Port ownership and exposure plan

The unchanged upstream Compose publishes `8000:8000` (Icecast), `8001:8001` and `8002:8002` (Liquidsoap sources), and `8080:8080` (LibreTime UI). **Do not start it unchanged on a shared host.**

| Role | Candidate host binding | Internal Compose destination | Policy |
|---|---|---|---|
| LibreTime administrator UI | `127.0.0.1:8700` | `nginx:8080` | Loopback-only until separately approved private HTTPS access |
| Single Live DJ **Show Source** | `127.0.0.1:8605` | `liquidsoap:8002` | Loopback-only for feasibility; authorized remote DJs require an approved secure route |
| Icecast listener / test stream | `127.0.0.1:8600` | `icecast:8000` | Loopback-only until a separately approved listener-facing HTTPS ingress |
| Other LibreTime source (`main`) | **Unpublished** | `liquidsoap:8001` | Do not expose a second input unnecessarily |
| PostgreSQL / RabbitMQ / worker / API | **Unpublished** | Radio-only private network | Never bind databases/brokers to the host |
| Public HTTP(S) | **Not authorized in RRN-01** | Existing approved RCAT reverse proxy | Do not bind new radio services to host ports 80/443 |

**Important mapping correction:** LibreTime's official Liquidsoap defaults are `main:8001` and `show:8002`. The single DJ route in this plan intentionally targets **Show Source on internal port 8002**. Earlier drafts targeting 8001 for the Show Source are superseded. Host port 8605 is only a candidate.

Do not expose source passwords or administrator endpoints in the Icecast listener URL or public player. Do not claim that a container's `localhost` points to the host: LibreTime's internal Icecast connection should use the Compose service DNS name `icecast`.

## Safe Compose implementation

- Pin **LibreTime images to `4.5.0`**, keep bundled **Icecast `2.4.4`** initially. No automatic major upgrades.
- Use `testing/compose.feasibility.override.yml` only alongside the official upstream Compose and a **private, fully configured** LibreTime file.
- Upstream published port lists must be **replaced**, not merged. Docker Compose `!override` requires **Compose v2.24.4+**; verify current host Compose capability during preflight. Do not claim a rendered model was validated without actually running that check.
- Reject default example passwords. PostgreSQL, RabbitMQ, Icecast source/admin/relay, LibreTime API and session secrets must be unique and managed outside Git. Use permission-restricted files and avoid dumping substituted secrets to GitHub or logs.
- Do not remove a service merely because it appears unused: the upstream composition is the supported baseline.
- Avoid Docker Engine restarts/upgrades, host-wide package installers, global container/network/volume pruning and unrelated proxy edits.

## Single read-only preflight before authorized installation

1. Confirm current host OS/CPU architecture, disk/memory headroom, active Docker/Compose version, and intended path ownership.
2. Check **only** proposed host ports `8600`, `8605`, and `8700`, plus any specifically requested DJ/ingress changes. Select another radio-only port if occupied; never evict the incumbent service.
3. Render and inspect the merged radio-only Compose model **without exposing secrets**; confirm exactly three loopback mappings, no host ports 8000/8001/8002/8080, and the private Icecast source target `icecast:8000`.
4. Confirm no connection to PDF HUB or AnyFlip Docker networks, volumes, paths, shared reverse proxy or app credentials.
5. Obtain explicit runtime authorization before pulling images, creating containers, migrating DBs, starting streams, editing public ingress or modifying firewall settings.

**No need to perform this preflight repeatedly.** Run once directly before the approved action; repeat only the specific fact that changes.

## Stop and rollback

Stop if host resources or ports conflict; any secret is unsafe; the upstream or override config introduces unintended host exposure; shared infrastructure would be altered; or the owner has not approved runtime installation.

After an approved installation, stop **only** project `rcat_radio_network`, leaving all three data volumes intact. Never use `docker compose down -v` or host-wide `docker system prune`. Restore radio-only config or backup if necessary; do not assume downgrading an image reverses DB migrations. Revert **only** any explicitly approved radio ingress changes, preserving the rest of the shared proxy. Perform one minimal PDF HUB/AnyFlip regression check after a radio change **only when** there is a plausible interaction.

## Completion status

- [x] Document upstream services and exact bundled Icecast dependency.
- [x] Define radio-only project, paths, credentials, volumes, backups and rollback.
- [x] Define loopback-only port candidates, correct **Show Source** routing, and public ingress boundary.
- [x] Exclude untrusted legacy software and destructive shared-host operations.
- [ ] Confirm current host resources/ports/paths/Compose version **once** before runtime execution.
- [ ] Render and validate approved merged Compose configuration in a suitable environment.

**RRN-01 remains OPEN until its actual preflight evidence is collected.** Implementation is RRN-02 and still requires separate approval. No server was accessed or modified in this document update.

## Sources

- [Official LibreTime 4.5.0 Compose](https://github.com/libretime/libretime/blob/4.5.0/docker-compose.yml)
- [Official LibreTime config template](https://github.com/libretime/libretime/blob/4.5.0/docker/config.template.yml)
- [Docker Compose merge and override rules](https://docs.docker.com/reference/compose-file/merge/)
- [RRN-00 accepted stack](./RRN-00-STACK-DECISION.md)
