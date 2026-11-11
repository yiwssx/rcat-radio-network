---
name: shared-host-deployment-safety
description: Safely plan, review, or execute SHOUTcast and AutoDJ deployment changes on RCAT's shared Ubuntu Docker host. Use when inspecting ports, installer requirements, compose files, secrets, volumes, reverse proxies, rollback, or commands that could affect PDF HUB and AnyFlip.
---

# RCAT Shared-Host Deployment Safety

## Operating context

The Ubuntu host runs other active applications, including PDF HUB and AnyFlip. A radio installation must remain a **separate service boundary** and must not change unrelated service configuration or data.

The legacy AzuraCast project was removed by an operator on November 10, 2026; the operator observed that radio containers and ports were gone and that the existing PDF HUB and AnyFlip HTTP health endpoints returned 200. This is historical evidence, not proof of current host state.

## Mandatory sequence

1. Read RRN-00 (#2) and RRN-01 (#3). Confirm the chosen panel is supported on the **exact host OS** before planning an install.
2. Inspect only the host facts required for the change: installed version, ports, disk/RAM headroom, running stacks, and proxy ownership. Reuse valid evidence rather than rerun unrelated acceptance suites.
3. List every host-wide installer action, dependency, service, and port, especially 80/443, before approval. Treat a vendor's "fresh server" requirement as a potential deployment blocker.
4. Prefer isolated service names, configuration paths, data paths, credentials, and networks. Do not assume an existing control panel can safely be placed in Docker if the vendor does not support that method.
5. Keep secrets out of Git, logs, issue bodies, and rendered Compose output. Provide redacted diagnostics.
6. For proposed changes, specify expected impact, backup/rollback steps, and the exact radio-only resources involved.
7. Require **separate explicit approval** before live deployment, downtime, data deletion, DNS, firewall, or reverse-proxy changes.

## Destructive-operation guardrails

- Never run host-wide commands such as `docker system prune`, `docker volume prune`, or unfiltered container deletion to "clean up" radio.
- Never use `docker compose down -v` or delete volumes without an exact resource inventory and explicit approval of the resulting data loss.
- Avoid restarting Docker Engine, modifying shared reverse proxies, or upgrading system dependencies merely to fit a control panel.
- Use scoped radio-only actions and preserve unrelated containers, named volumes, networks, and ingress paths.
- Do not claim a deployment or removal succeeded without actual host evidence.

## Acceptance boundary

Verify only the affected radio function and minimal PDF HUB/AnyFlip regressions once. Avoid repeat testing of previously verified unrelated functions unless new evidence suggests a regression.

## Source guidance

- Docker Compose documentation: https://docs.docker.com/compose/
- Docker-maintained agent skills, consulted for safety patterns: https://github.com/docker/skills/tree/main/skills/docker-compose-patterns and https://github.com/docker/skills/tree/main/skills/docker-destructive-guardrails
- GitHub issue #3 (RRN-01) holds the project-specific deployment boundaries.

This is an instruction-only skill. It contains no deployment script and does not authorize server changes.
