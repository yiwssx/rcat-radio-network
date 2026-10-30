# RCAT Radio — Docker-Only Single-Session LAN Pilot

**No Python installation on the Ubuntu host.** Operators need Bash, Docker Engine,
Docker Compose v2 and standard Linux tools (`ip`, `ss`, `curl`, `awk`, `df`,
`nproc`, `od`, `tr`, `grep`, coreutils). Python runs ONLY in a temporary
network-isolated audit container that receives the rendered Compose on stdin
and does not mount `/var/run/docker.sock`.

**Architecture:** AzuraCast stable single-container engine + Nginx listener
portal + Docker named volumes. Isolated Compose project
`rcat_radio_pilot`; no Docker-in-Docker.

## On your own PC: one SSH session for administration

```bash
ssh -L 8700:127.0.0.1:8700 rcat_iot_admin@10.10.1.100
```

The 8700 SSH tunnel exposes the admin web interface ONLY on your own PC;
it does not publish admin access across the LAN.

## On rcatiotserver: one Docker-managed test session

```bash
cd ~
git clone https://github.com/yiwssx/rcat-radio-network.git
cd rcat-radio-network
bash scripts/radioctl.sh check 10.10.1.100
```

If the Git repository is already present, use `git pull --ff-only` rather
than cloning it again. The runner does **not** install Python on the host.

## Mandatory change approval — RRN-00 / RRN-01 / RRN-02

The `check` command is **read-only** and does not mean the three blocking
Tracker issues are accepted. **Do not deploy yet** until the authorized owner
reviews the actual host inventory and existing PDF HUB/AnyFlip workflows,
network/firewall/IPv6 exposure, AzuraCast release and full rendered Compose,
backup/rollback, and signs off RRN-00, RRN-01 and RRN-02.

After documented authorization, create the following private local file
`reports/rrn-deploy-approval.txt` on the *actual server*. The values below
are a **format example**, not pre-granted approval. Use only after the evidence
and operator decisions really exist, and replace the IP with the host's
configured RFC1918 address.

```text
RRN00=APPROVED
RRN01=APPROVED
RRN02=APPROVED
SHARED_HOST_CHANGE=APPROVED
RRN_BIND_IP=10.10.1.100
```

Keep supporting evidence and the signatory/change reference in a protected
local record, not the public GitHub repository. The approval file must be a
regular file (not a symlink), mode `0600` or `0400`, in a protected
`reports/` directory. **The script only validates the recorded assertions,
not their truth.** Incomplete records and missing explicit CLI consent fail
before any Docker operation.

Only *after* that review, authorize one controlled deployment:

```bash
chmod 600 reports/rrn-deploy-approval.txt
bash scripts/radioctl.sh deploy 10.10.1.100 --ack-shared-host
```

If any gate fails, leave the station uninstalled and document the blocker.
The old `scripts/one_round.py --mode deploy` path is disabled so it cannot
bypass the reviewed operator workflow.

### Automatic gates before `docker compose up`

1. Verify that the LAN IPv4 exists on this server and is RFC1918.
2. Verify Docker Engine and Compose are available.
3. Verify at least 4 logical CPU threads, 4 GiB total RAM, 2 GiB *available*
   RAM and 40 GiB filesystem free space under `/var`.
4. Ensure none of `8700, 8750, 8600, 8605, 8606` are already occupied.
5. Smoke-test existing services before any change:
   PDF HUB `http://10.10.1.100:8081/` (HTTP 1xx–4xx accepted);
   AnyFlip `http://10.10.1.100:8094/healthz` (HTTP 200 required).
6. Prevent accidental overwrites if radio containers or unpaired DB
   credentials exist.
7. Create private `deployment/.env` and `deployment/azuracast.env`
   (permissions 0600) and a new random database credential exactly once.
8. Render effective Compose and pipe it into a disposable
   `python:3.12-alpine` audit container (**not** a Python interpreter on host).
   Reject privileged mode, Docker socket, host networking, protected existing
   ports and unauthorized host IP binding.
9. Pull radio images, initialize AzuraCast using its upstream
   `azuracast_install` command, start radio and portal.
10. Repeat existing-service HTTP baseline after startup; stop **only**
    new radio containers if startup/regression fails, preserving volumes.

### After automatic deployment

| Purpose | Access |
|---|---|
| AzuraCast Admin | `http://127.0.0.1:8700` on your PC via SSH tunnel |
| RCAT Radio Player | `http://10.10.1.100:8750` from approved LAN |
| Radio Stream | `http://10.10.1.100:8750/listen/rcat_radio/radio.mp3` via listener proxy (default mount) |

In the AzuraCast Admin UI, create the first user and **one station** with
shortcode `rcat_radio`, Icecast port `8600`, enabled AutoDJ playlist and
an original/rights-cleared audio test file. The runner attempts to create
`reports/original-test-tone.wav` from ffmpeg inside the AzuraCast container
to simplify this. Real Live DJ switching requires BUTT/Mixxx or another
configured DJ source and manual observation.

Then perform the final checks:

```bash
bash scripts/radioctl.sh verify 10.10.1.100
bash scripts/radioctl.sh status
```

The verify command checks admin/portal HTTP responses, the
`rcat_radio` Now Playing metadata, five concurrent proxy stream connections for the documented default mount
(received data only), and the PDF HUB/AnyFlip HTTP status. It writes
`reports/last-result.txt`. A successful local stream smoke is **not proof**
of accurate audio playback, 24-hour endurance, real DJ source priority,
isolated backup restore, application-level PDF/AnyFlip workflows, VLAN/Internet
blocking, or production licensing.

### Other Docker-managed controls

```bash
# Read-only preflight, no containers start
bash scripts/radioctl.sh check 10.10.1.100

# Show only the radio Compose project
bash scripts/radioctl.sh status

# Radio project logs (last 150 lines)
bash scripts/radioctl.sh logs

# Stop radio services only, preserving data volumes
bash scripts/radioctl.sh stop
```

For direct Docker Compose use after environment setup:

```bash
docker compose -p rcat_radio_pilot \
  --env-file deployment/.env \
  -f deployment/compose.pilot.yaml ps
```

**Do not execute** `docker system prune`, `docker compose down -v`,
Docker Engine auto-upgrade, global firewall changes or new public port
forwarding on the shared production host.

## Recovering an interrupted AzuraCast initialization

The installer uses `docker compose run --rm --no-deps web -- azuracast_install`.
After that temporary container exits, `docker ps -a` may show no radio
containers even though the database and station volumes are still present.
A preflight-only `reports/last-result.txt` is not evidence of successful installation.

If initialization stalls or fails on a shared host:

1. Confirm no radio deploy processes or running radio containers remain.
2. Keep `deployment/.env`, `deployment/azuracast.env`, and all
   `rcat_radio_pilot_*` Docker volumes. **Never run `down -v` or Docker prune.**
3. Back up the radio volumes before any permission or identity change.
4. Verify that `AZURACAST_PUID` and `AZURACAST_PGID` are the non-root
   operator's numeric UID/GID (for example `id -u`, `id -g`). The initial
   implementation incorrectly recorded UID/GID `0` when invoked through
   `sudo`; the runner now rejects such saved environments rather than
   silently proceeding. Existing values require an operator-reviewed,
   backed-up correction; **never regenerate database secrets**.
5. Retry only after resolving the underlying failure. The updated runner
   saves the full private initialization transcript as
   `reports/azuracast-install-YYYYMMDDTHHMMSSZ.log` (mode 0600) and
   stamps `reports/last-result.txt` at installation start and on failure.
   Installer logs may contain secrets; do not publish them unredacted.

Do not assume the UID/GID defect alone caused an `uptime_wait` stall:
the AzuraCast startup also checks dependent services. Inspect the saved
installer log and any supervisor errors to identify the actual cause.
Radio-only troubleshooting must preserve the PDF Hub and AnyFlip stacks.

## Important limitations / operator review

- This repository does not have remote shell access to your RCAT server.
  GitHub Actions checks static code and config, not real host installation.
- Audit validation runs in a minimal dedicated container without network
  or Docker socket; the host runs Bash and Docker commands only.
- The pilot is LAN-bound but host/upstream firewall rules must still be
  reviewed externally; Docker-published interfaces are not a complete
  authorization boundary.
- The trial uses mutable `stable` image tags. Record and pin digests
  before any production promotion.
- A new radio database credential must never overwrite a previously
  initialized volume. The scripts refuse unexpected existing containers.
- A custom Compose diverges from AzuraCast's default installer;
  runtime compatibility still must be confirmed with one real-host test.
- For safety, `check` may reject the host if the existing PDF/AnyFlip
  health endpoints cannot be reached. Investigate, do not bypass.

## Operator evidence

Share a **reviewed and redacted** `reports/last-result.txt` and relevant
error messages. Do not publish `deployment/.env`,
`deployment/azuracast.env`, raw Compose JSON, private IP details, Docker
inspect, personal media or hidden tokens in a public Issue.

Tracker: [#2](https://github.com/yiwssx/rcat-radio-network/issues/2).
Main work packages: [RRN-00 #3](https://github.com/yiwssx/rcat-radio-network/issues/3)
and [RRN-02 #5](https://github.com/yiwssx/rcat-radio-network/issues/5).

## Stream routing and regression checks (2026-10-28 update)

The listener player fetches ONLY AzuraCast's **one-station** public Now Playing
endpoint `/api/nowplaying/rcat_radio` through Nginx and routes the documented
`/listen/rcat_radio/<mount>` stream path through the listener portal
on port `8750` (same origin). **AzuraCast admin remains loopback-only**.
An arbitrary station or admin path must not be proxied through the portal.

The deployment stores the original HTTP response statuses of PDF HUB and
AnyFlip at `reports/predeploy-baseline.txt` (local mode `0600`). Later
`verify` runs compare against that exact before-state rather than merely
checking that ports answer. **Do not delete that baseline before running verify.**

After deploying, also open the portal in Chrome and a phone browser and
listen to the track. Five successful HTTP stream fetches do not prove the
radio contains audible audio or that the Live DJ / AutoDJ transition works.

The `verify` mode does not reapply the installation-time available-memory
threshold, since the running AzuraCast process consumes memory. It still
checks Docker reachability, the host bind IP, station response, stream bytes
and existing-service baseline.
