# RCAT Radio — One-session LAN pilot test (legacy Python runner)

> **Updated operator workflow:** The preferred deployment path now uses
> `scripts/radioctl.sh` with Docker Compose and **does not require Python
> on Ubuntu**. See [DOCKER-ONLY.md](DOCKER-ONLY.md). The Python-based
> instructions below are retained for reference only.
>

## Purpose and boundaries

One test session covers actual server preflight, existing PDF HUB/AnyFlip HTTP
baseline, isolated radio Compose install, local web admin, RCAT Radio Portal,
original royalty-free audio test tone, Now Playing and 5-stream smoke test,
plus before/after HTTP regression.

**This does not automatically certify Live DJ switch, 24-hour soak, isolated
restore, security outside the LAN, full conversion/download regression or
copyright compliance.** All untested acceptance items are marked PENDING.

The official AzuraCast default Docker Compose exposes a broad port range and
includes an Updater with Docker socket access. This pilot uses a **separate,
minimal Compose** without Updater, host network, privileged mode, Docker
socket or changes to existing reverse proxy/firewall. It uses the stable
AzuraCast application image and its upstream `azuracast_install` command.

## Network and resource gates

- Admin: `127.0.0.1:8700` **only**, through SSH tunnel
- Portal: `LAN_IP:8750`
- First radio station: `LAN_IP:8600`
- DJ input (if enabled): `LAN_IP:8605`, `LAN_IP:8606`

The runner rejects unknown/busy ports, absent Docker, non-RFC1918 remote
binds, missing local network interface, fewer than 4 CPU threads, less
than 4 GiB total / 2 GiB available RAM or less than 40 GiB free on /var.
All checks happen before any radio containers are created.

## One test session

On your local workstation, open an SSH terminal **with a tunnel**:

```bash
ssh -L 8700:127.0.0.1:8700 USER@SERVER_LAN_IP
```

Then inside that SSH terminal:

```bash
git clone https://github.com/yiwssx/rcat-radio-network.git
cd rcat-radio-network
python3 scripts/one_round.py --mode deploy --bind-ip SERVER_LAN_IP --ack-shared-host
```

Replace `USER` and `SERVER_LAN_IP` with your actual SSH account and
private server IP. If already cloned, use `git pull --ff-only` instead.

### What the command does

1. Inspect host CPU/RAM/disk, listening/published ports and Docker permission.
2. Probe existing protected HTTP services at ports 8081 and 8094.
3. Create local 0600-only environments and a random DB password without
   printing or publishing it; inspect the fully rendered Compose privately.
4. Pull the radio's AzuraCast stable image and nginx portal and run
   `azuracast_install` for **this separate project**.
5. Start only the radio's two containers, smoke-test admin/portal and verify
   the existing-service baseline. Stop only the radio containers on a
   post-start failure, preserving radio volumes and existing services.
6. Generate the original audio file under `reports/pilot-*/rrn-original-test-tone.wav`.
7. Pause for first-admin and one-station setup, then validate the read-only
   Now Playing API, stream and five local listeners; save a JSON report.

### During the manual station checkpoint

Use the workstation browser: `http://127.0.0.1:8700` through SSH tunnel.
Create the Admin, set up **one** station with shortcode `rcat_radio`
and Icecast port `8600`. Upload the generated WAV and assign an enabled
AutoDJ playlist. Start broadcasting. Use authorized BUTT/Mixxx DJ credentials
to test switching to live and returning to AutoDJ.

Listener page: `http://SERVER_LAN_IP:8750`. Test from an approved LAN
device, not the Internet. Return to the SSH terminal and press Enter; the
script runs its final checks and writes `reports/pilot-*/result.json`.
It cannot evaluate the actual human-audible transition automatically.

### Other modes

Read-only capacity/port gate only:

```bash
python3 scripts/one_round.py --mode check --bind-ip SERVER_LAN_IP
```

Recheck running pilot without redeploying:

```bash
python3 scripts/one_round.py --mode verify --bind-ip SERVER_LAN_IP
```

Headless deployment with manual setup deferred:

```bash
python3 scripts/one_round.py --mode deploy --bind-ip SERVER_LAN_IP \
  --ack-shared-host --no-prompt
```

Results:
- `BLOCKED_OR_INCOMPLETE`: stop or installation problem; inspect output
- `DEPLOYED_STATION_SETUP_OR_STREAM_PENDING`: station or stream still pending
- `SMOKE_PASS_MANUAL_TESTS_PENDING`: local stream and API smoke pass;
  real DJ, 24h soak, isolated restore and full regression still pending

**Do not upload .env files, raw Docker logs or private host data to public
GitHub Issues.** Review each report before sharing it.

### Controlled stop (radio only)

```bash
docker compose -p rcat_radio_pilot -f deployment/compose.pilot.yaml stop portal web
```

Never run global Docker prune or `down -v` on the shared host. The pilot
images use mutable stable tags: record resolved digests and pin them before
production promotion. This pilot is not a public-radio production deployment.

Source references:
- https://www.azuracast.com/docs/getting-started/installation/docker/
- https://www.azuracast.com/docs/administration/docker/
- https://www.azuracast.com/docs/getting-started/requirements/
