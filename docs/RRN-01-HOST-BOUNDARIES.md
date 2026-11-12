# RRN-01 — Shared-Host Deployment Boundaries

**Status:** Deployment boundary design completed; live host preflight pending.  
**Date:** 2026-11-12  
**Scope:** Planning and documentation only. No host access, deployment, DNS change, firewall change, or Production modification.  
**Related issues:** [RRN-00 #2](https://github.com/yiwssx/rcat-radio-network/issues/2), [RRN-01 #3](https://github.com/yiwssx/rcat-radio-network/issues/3), [RRN-02 #4](https://github.com/yiwssx/rcat-radio-network/issues/4)

## 1. Decision and constraints

Reserve a **radio-only Docker Compose project** on the existing RCAT Ubuntu host. Use a minimally changed, **version-pinned LibreTime 4.5.0 upstream Compose distribution** if RRN-00 confirms the precise SHOUTcast DNAS v2 integration and permits the required DNAS binary use. The closed-source SHOUTcast binary may require a separate host service or independently packaged container; **its deployment mechanism and private source route are NOT approved or finalized** until official binary and license details are known.

- Incremental control-panel/software-license and external radio-hosting subscription target: **USD 0/month**.
- Exactly one station; LibreTime media uploads/playlists + standard Live DJ, SHOUTcast DNAS output and a listener player.
- Never recreate AzuraCast. Do not develop a custom radio backend/control panel or a custom stream gateway.
- Do not run a native control-panel installer as root, change the host OS, or upgrade/restart the shared Docker Engine to make the radio stack work.
- The existing PDF HUB, AnyFlip production/staging, tunnels, and any PDF HUB drill containers are **out of scope**. Do not change, restart, delete, or clean them.
- A technical plan is not permission to deploy. RRN-00 remains blocked on a focused integration check and official DNAS package acquisition.

## 2. Existing evidence and confidence

| Fact | Source | Treatment |
|---|---|---|
| RCAT shared host previously reported Ubuntu 26.04.1 LTS / x86_64, LAN IP `10.10.1.100` | Historical operator inventory | **Historical only**; verify once immediately before deployment |
| Legacy `rcat_radio_pilot` Docker project removed (2 containers, 1 network, 10 named volumes) | Operator-provided output, November 2026 | **Accepted**; do not redo teardown |
| Radio ports 8600, 8605, 8606, 8700, 8750 showed no listener after removal | Operator-provided `ss` output | **Previously available, not reserved**; recheck only proposed ports at the preflight gate |
| PDF HUB HTTP 200 and AnyFlip `/healthz` HTTP 200 after removal | Operator-provided `curl` output | **Accepted baseline**, no repeat unless a radio change may affect them |
| Current host port ownership, memory, disk headroom, firewall and proxy routing | No live host connector/inspection in this planning turn | **Unknown**; must not assert that the proposed runtime is safe to start yet |

No inference about available RAM, storage space, open firewall ports or spare CPU may be made from healthy container status alone.

## 3. LibreTime 4.5.0 upstream deployment footprint

[Official tagged Compose file](https://github.com/libretime/libretime/blob/4.5.0/docker-compose.yml): **10 upstream services** — `postgres`, `rabbitmq`, `playout`, `liquidsoap`, `analyzer`, `worker`, `api`, `legacy`, `nginx`, `icecast`. Official Compose data volumes: `postgres_data`, `libretime_storage`, and `libretime_playout`.

The unmodified upstream host bindings are **8080:8080** for the web service, **8001:8001** and **8002:8002** for Liquidsoap live inputs, and **8000:8000** for bundled Icecast. All of these are unacceptable as default host-wide bindings on RCAT's shared server. The default Compose file also contains sample credentials, and the images use `LIBRETIME_VERSION:-latest` unless explicitly pinned.

**Important:** The upstream `icecast` service is not automatically redundant just because the intended external output is SHOUTcast. Confirm LibreTime's internal services and configuration dependencies before disabling it. Do not remove service dependencies speculatively or claim the SHOUTcast output works until RRN-00 is proven.

## 4. Proposed radio-only namespace and filesystem ownership

| Resource | Proposed location / identifier | Policy |
|---|---|---|
| Compose project | `rcat_radio_network` | Distinct from retired `rcat_radio_pilot`, `pdf-hub`, and AnyFlip projects; only radio-owned resources are in scope |
| Deployment checkout and approved Compose overrides | `/opt/rcat-radio-network/` | Proposed; **do not assume this path is currently empty**; check ownership and any existing deployment-control conventions first |
| Runtime secrets and generated LibreTime `config.yml` | `/etc/rcat-radio-network/` | Host-private directory (mode 0700); secret files 0600 where practical; mount read-only into consumers; never commit actual credentials |
| Persistent DB/media/playout | Radio-only Compose volumes `postgres_data`, `libretime_storage`, `libretime_playout` | Expect project-prefixed volume names when Compose creates them; preserve on stop and rollback |
| DNAS config, logs and license/account material | Radio-specific paths under `/etc/rcat-radio-network/` and `/var/log/rcat-radio-network/` | Final location depends on official DNAS packaging; no proprietary binaries or account secrets in Git |
| Radio backups | `/var/backups/rcat-radio-network/` | Back up media, DB, playlists and configuration/credentials securely before any destructive migration; choose an approved backup retention location before launch |
| Docker network(s) | `rcat_radio_network_default` or explicit radio-only network | DB/RabbitMQ/services private to radio; no attachment to PDF HUB/AnyFlip networks except through a separately approved, narrowly defined ingress |

These are **design decisions, not directories or volumes already created**. Use supported vendor mounting conventions and current host policy when implementing.

## 5. Proposed port and access boundary

The following **candidate mappings** reuse old radio-only ports observed as released after AzuraCast removal. They are not confirmed free today.

| Interface | Candidate host binding | Upstream destination | Exposure |
|---|---|---|---|
| LibreTime admin/web | `127.0.0.1:8700` | LibreTime nginx `:8080` | Host loopback only; authenticated private access, with later approved HTTPS ingress if needed |
| Standard Live DJ source | `10.10.1.100:8605` | LibreTime Liquidsoap `:8001` | LAN only with credential checks and source-IP restrictions; exact interface must be confirmed |
| Secondary Live DJ source | **Not published by default**; `10.10.1.100:8606` only if required | LibreTime Liquidsoap `:8002` | Avoid opening unused entry points |
| SHOUTcast listener endpoint | `127.0.0.1:8600` **candidate only** | DNAS service, final private-network route TBD | Keep private for feasibility; public HTTPS access requires separately approved ingress |
| Bundled LibreTime Icecast | **No host published port by default** | Internal `:8000`, only if LibreTime needs it | Never expose unused upstream `:8000` to the host |
| LibreTime Postgres/RabbitMQ/API/worker | **No host published ports** | Internal Compose network | No unrelated service can connect directly |

**Route feasibility caveat:** `localhost` in a Docker container refers to that container, not the host. If DNAS is a separate host service on `127.0.0.1:8600`, LibreTime cannot connect to it merely by using `localhost`. Do not assume a working route; RRN-00 must choose a supported networking method and demonstrate a source connection. A dedicated radio-only container/network route is acceptable **only if DNAS licensing and packaging permit it**. Avoid host networking and open bind addresses merely to bypass this issue.

**Future public deployment:** Prefer the existing institution-approved ingress at `radio.rcat.ac.th`, subject to domain authorization, TLS validation, source/listener separation, and current proxy capacity. No new listener is allowed to claim host ports 80/443 or alter existing DNS/proxy/firewall settings as part of RRN-01. The public player must never expose admin/source credentials.

## 6. One-time preflight gate, immediately before any runtime change

The following is a **read-only verification procedure**, to be performed once as part of a separately approved deployment/test action. Do not ask the owner to rerun earlier successful removal tests.

1. Verify the exact host OS and architecture, current disk/memory headroom, Docker/Compose availability, and ownership of the proposed `/opt`, `/etc` and backup locations.
2. Inspect active listeners on **only the candidate radio ports** (8600/8605/8606/8700), current interface/IP, and conflicts with existing Compose services. If any port is occupied, select a different radio-only port instead of modifying the incumbent service.
3. Render the proposed radio-only Compose config **without printing interpolated secrets** and check project name, version pin, bound interfaces, mounts, exposed ports and non-radio resource references.
4. Confirm that SHOUTcast DNAS has a legal official download/distribution method and that the selected LibreTime-to-DNAS network path is possible without changes to unrelated services.
5. If the targeted compatibility experiment is explicitly authorized, run it in an isolated, non-public radio scope with a single authorized test audio file. Do not launch the public player or change ingress during the experiment.

No resource creation, package installation, Docker Engine restart, or data migration is part of this read-only preflight. Stop before deployment if the prerequisites are not met.

## 7. Stop conditions and rollback

**Stop immediately** when: an essential host port is occupied; unreviewed root-level installer/80/443 requirement appears; resource headroom is inadequate; the official DNAS license/download is unavailable; the required network route is unsupported; secrets would be committed/logged; or an unrelated PDF HUB/AnyFlip service would need changes.

**Radio-only rollback, after a separately authorized installation:**
1. End the radio test or release and stop **only** the `rcat_radio_network` Compose services and any explicitly approved radio-owned DNAS unit. Do not stop the Docker daemon or non-radio containers.
2. Restore previous radio-only configuration from its recorded version. Preserve the three radio data volumes; **do not** execute `docker compose down -v` or host-wide prune.
3. For incompatible DB or media schema changes, use the approved pre-change backup rather than assuming that a container-image downgrade automatically reverses migrations.
4. If a future ingress change was approved, restore **only the radio-specific ingress configuration** using its known-good version. Never overwrite the shared proxy's other vhosts.
5. Confirm radio has stopped or recovered and perform **one** proportionate health check of PDF HUB and AnyFlip if the executed change could have affected them. Reuse existing evidence otherwise.

## 8. Scope completion and dependency gate

**RRN-01 design deliverables complete:**
- [x] Separate namespace, proposed directories, data/secret/backup boundaries and ownership rules defined.
- [x] Vendor Compose services/default port mappings inspected, with proposed scoped mappings and exposure rules.
- [x] Host-wide installer, shared service and destructive-operation restrictions documented.
- [x] Explicit stop conditions and radio-only rollback documented.
- [x] Existing operator evidence accepted without unnecessary retesting.

**Not yet verified / runtime gate (do not call completed):**
- [ ] Current host ports, IP, memory, disk headroom and destination-path ownership: verify once before deployment, not in GitHub-only planning.
- [ ] DNAS v2 official binary/terms and LibreTime source route: RRN-00 integration blocker.
- [ ] Runtime network/health behavior: requires separately authorized, isolated test.

**Disposition:** Design-ready, **host-preflight pending**. Keep RRN-01 open until the host-boundary availability gate has actual evidence, or explicitly transfer the gate to RRN-02 without presenting it as verified.

## Sources

- LibreTime 4.5.0 official Compose: https://github.com/libretime/libretime/blob/4.5.0/docker-compose.yml
- LibreTime Docker config template: https://github.com/libretime/libretime/blob/4.5.0/docker/config.template.yml
- LibreTime official Docker installation guide: https://libretime.org/docs/stable-3.x/admin-manual/install/install-using-docker/
- Docker Compose documentation: https://docs.docker.com/compose/
- Project stack decision: [RRN-00](./RRN-00-STACK-DECISION.md)

**No live system was accessed or modified during this RRN-01 work.**
