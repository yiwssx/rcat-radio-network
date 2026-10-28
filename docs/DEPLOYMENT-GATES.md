# Deployment gates

## Gate A — RRN-00 (currently waiting for host evidence)

Run read-only inventory, record resource and port bindings, verify PDF HUB and
AnyFlip baseline, backups and reachability. Review private host outputs locally,
share only sanitized summaries.

## Gate B — RRN-01/02 design and staging

Review installed AzuraCast version, release channel, image digests and official
docker.sh before **execution**. Its installer may create/start containers.
Generate the effective Compose in a controlled staging environment, inspect
all inherited port bindings, capabilities, environment variables and volumes.
Adding Compose override ports need not remove existing default ports.

Example reviewing a staged Compose (does NOT start containers):

```bash
docker compose config --format json | python3 /path/to/rcat-radio-network/scripts/compose_audit.py
```

**Do not post the raw Compose JSON to public issues: it may contain secrets.**

## Gate C — controlled deployment (NOT AUTHORIZED YET)

Approve explicit change record, backup/rollback and downtime plan. Start only
AzuraCast containers on approved network. Immediately repeat baseline and
functional workflow tests for existing services.

## Gate D — acceptance

Live/AutoDJ transitions, playback compatibility, RBAC, listener stress,
24-hour soak, silence detection, isolated restoration and regression all pass.
Public launch requires a separate review for TLS, bandwidth, licensing and
internet exposure.

Rollback must target **only** the radio project's containers. Preserve
persistent volumes for recovery. Never run global Docker prune.
