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

Use [RUN-ONCE](docs/RUN-ONCE.md) for a single gated host test session. The runner can
perform a preflight, deploy **only** an isolated radio stack, verify existing-service
HTTP baselines, and provide a one-time human setup checkpoint before streaming tests.

```bash
python3 scripts/one_round.py --mode deploy --bind-ip YOUR_SERVER_PRIVATE_IPV4 --ack-shared-host
```

Do not run this on the shared host without reviewing the guide and choosing the correct
host private IPv4. The command does **not** modify firewall/Reverse Proxy or launch
AzuraCast automatically on GitHub; it runs only on the machine where you execute it.
Admin listens on loopback only; use the documented SSH tunnel. A passed GitHub CI
is **not** proof the live broadcast or production host has been tested.
