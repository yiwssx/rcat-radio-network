---
name: shared-host-deployment-safety
description: Safely plan, review, and control Icecast and LibreTime deployments on RCAT's shared Ubuntu Docker host without disrupting PDF HUB, AnyFlip, ingress, credentials, or other existing services.
---

# RCAT Shared-Host Deployment Safety

## Deployment context

The accepted one-station stack is **LibreTime 4.5.0 with bundled Icecast 2.4.4**, using radio-only Docker Compose resources. PDF HUB and AnyFlip are active, unrelated applications and must remain untouched.

The old AzuraCast pilot was removed with operator-confirmed checks in November 2026. Prior unused ports and HTTP 200 results are **historical evidence**, not live resource availability.

## Mandatory order

1. Read [RRN-00 accepted stack](https://github.com/yiwssx/rcat-radio-network/issues/2) and [RRN-01 shared host boundaries](https://github.com/yiwssx/rcat-radio-network/issues/3); reuse previous evidence.
2. Verify the current host architecture, disk/memory capacity, service/port ownership, path ownership and **Docker Compose >= 2.24.4** in one read-only preflight immediately before a separately approved runtime change.
3. Use a separate Compose project and private credentials. LibreTime's bundled `icecast` service connects internally at `icecast:8000`; the Show DJ source is `liquidsoap:8002`, not the Main source on 8001.
4. Upstream binds host ports 8000, 8001, 8002 and 8080. Replace these mappings by explicit loopback radio-only ports in `testing/compose.feasibility.override.yml`. Docker Compose `ports: !override` is necessary to **replace** rather than merge published ports.
5. Keep Postgres/RabbitMQ and admin/internal endpoints unpublished. A public Icecast listener URL requires separately approved HTTPS ingress.
6. Validate a secret-redacted merged Compose model and stop if port bindings are incorrect; do not mistake a static override for a successfully rendered/running stack.
7. Obtain explicit approval before installing/running containers, migrations, changing firewall/DNS, starting public audio, or modifying any shared proxy.

## Destructive-operation restrictions

- Never execute unscoped `docker system prune`, `docker volume prune`, `docker compose down -v`, engine upgrades or restarts to clean up the radio.
- Never remove PDF HUB/AnyFlip containers, networks, volumes, reverse proxy configuration or their secrets.
- Keep three LibreTime data volumes for rollback. Restore only radio-owned configuration and backed-up data if needed.
- If a selected port is occupied, choose another candidate rather than evicting the owner.
- Re-run only specific checks that a new change could invalidate. A healthy HTTP endpoint alone does not prove audible streaming.

## Acceptance boundary

Issue #3 ends with the one-time host preflight evidence; #4/#5/#6 cover actual installation, playable Icecast output, AutoDJ and Live DJ fallback respectively. Do not demand unrelated performance or soak tests.

All GitHub content is English-only. This skill installs nothing and authorizes no server action.
