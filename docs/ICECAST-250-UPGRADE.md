# RCAT Radio: Icecast 2.5.0 upgrade — 2026-11-14

**State: reviewed source candidate, not yet deployed.** No Production/Mobile PASS is implied by this document.

## Release and dependency decision

- LibreTime 4.5.0 is still the latest published stable LibreTime release. Keep its seven application images, Liquidsoap and vendor-selected PostgreSQL/RabbitMQ versions unchanged; do not invent independent incompatible major updates.
- Icecast 2.4.4 is in security-only support until 2026-12-31. Icecast 2.5.0 is the latest stable official release and is available as ghcr.io/libretime/icecast:2.5.0 in the LibreTime maintainers' image repository.
- The Icecast project says 2.5.x reads 2.4.x configurations; it also changed TLS-client behavior under high buffer pressure. This makes a focused upgrade justified, NOT a guarantee that Android's two-second stream symptom is fixed.
- Listener frontend toolchain updates require a separate isolated build, not a runtime Icecast change.
- Do NOT upgrade Docker Engine, Apache, host packages or other RCAT apps on the shared host as part of this task.

Authoritative sources:
- https://www.icecast.org/download/
- https://icecast.org/news/
- https://github.com/libretime/icecast-docker
- https://github.com/libretime/libretime/releases

## Current operator evidence

Multiple phones on different carriers stop at about two seconds on both the webpage and direct HTTPS MP3 URL. Desktop works on multiple networks. The owner observed that the earlier public HTTP IP:8600 route worked on phones. The new TLS listener / HTTP response path is the priority hypothesis, not the Svelte play button.

## Apply only on the authorized IOT Host

After review/merge, use a **fresh temporary checkout** of the exact approved Git revision. Do not overwrite or reset the historical /opt/rcat-radio-network checkout. From its repository root:

    sudo python3 scripts/upgrade-icecast-2.5.py --plan
    sudo python3 scripts/upgrade-icecast-2.5.py --apply --approve-brief-stream-reconnect

The upgrade requires root, the original isolated ten-service stack, running Icecast 2.4.4, an existing RRN-06 archive checksum, and existing native TLS port 8443. It pulls the new image before altering anything, writes a private timestamped Compose rollback snapshot, replaces ONLY the Icecast image tag, and confirms the rendered configuration is otherwise identical. Then it recreates ONLY Icecast and checks native HTTPS service readiness with correct certificate verification (up to six bounded attempts); MP3 mount presence is not an immediate deployment gate because Liquidsoap may need time to reconnect. An Icecast container or TLS readiness failure attempts automatic Icecast-only rollback; a temporarily absent MP3 mount does not trigger a rollback. The command interrupts listening briefly; it does not restart other services or modify volumes, certs, NAT, DNS or RMS Apache.

Do not rerun historical initial installer/TLS installation scripts. The existing certificate renewal receiver uses the installed Compose configuration and remains in place.

## Mobile acceptance after successful Host operation

1. Phone on Wi-Fi: direct https://radio.rcat.ac.th:8600/main.mp3 continuously for at least two minutes.
2. Second phone using a different network: same direct stream, also two minutes.
3. Desktop: existing direct stream continues.
4. One public Listening-page mobile playback check for two minutes; no frontend deploy required.

Only after operator results may this be marked mobile PASS. A passing curl on IOT is NOT mobile acceptance.

## Rollback if mobile still stops at two seconds

Use BOTH EXACT paths printed as `ROLLBACK_COMPOSE_SNAPSHOT` and `ROLLBACK_OVERRIDE_SNAPSHOT` by the successful Host script. They must be restored as a matched pair; the timestamps below are intentionally illustrative:

    sudo install -o root -g root -m 600 /var/backups/rcat-radio-network/icecast-compose-before-2.5.0-YYYYMMDDTHHMMSSZ.yml /opt/rcat-libretime-runtime/docker-compose.yml
    sudo install -o root -g root -m 600 /var/backups/rcat-radio-network/icecast-override-before-2.5.0-YYYYMMDDTHHMMSSZ.yml /opt/rcat-libretime-runtime/radio.override.yml
    sudo docker compose --project-directory /opt/rcat-libretime-runtime --env-file /etc/rcat-radio-network/compose.env -p rcat_radio_network -f /opt/rcat-libretime-runtime/docker-compose.yml -f /opt/rcat-libretime-runtime/radio.override.yml up -d --no-deps --pull never --force-recreate icecast

Never use docker compose down -v, prune or mass-upgrade the host. If the 2-second problem persists, collect a mobile HTTP/TLS trace before changing any more services.

## Two-layer Compose bug fixed in the current upgrade script

The first operator run stopped after a strict model mismatch, and the second stopped in `--plan` with the sole difference `model.services.icecast.image`. Repo evidence confirms the original `testing/compose.feasibility.override.yml` pins Icecast 2.4.4, and the installer copies it to the runtime `radio.override.yml`. The previous script changed only the upstream base file; the override won the merge and the effective image remained old. This was an **upgrade-script defect**, not evidence of Icecast/TLS failing. The corrected preflight renders TWO temporary updated Compose files before changes. On successful preflight, it backs up and updates BOTH image pins. No Icecast restart occurs when preflight fails.

Use the current version from `main`; do not rerun the older script from a stale temporary checkout without `git pull --ff-only`. The running old Icecast image should remain active until `--apply` succeeds. Verify mobile listening separately after the Host reports TLS stream PASS.


## Post-rollback diagnostic: TLS on Icecast 2.5 without another radio interruption

Operator evidence from 2026-11-14:
- Upgrade to 2.5.0 passed the two-layer Compose preflight but failed the script's one-shot, seven-second HTTPS/MP3 readiness check. The script reported rollback to 2.4.4. Since it did not report curl status, bytes or TLS errors, this does not prove that the 2.5 XML is incompatible.
- The restored old 2.4.4 container was observed running with zero restart count. Both LAN HTTP and HTTPS MP3 returned 200 and 252000 bytes over 12 seconds, TLS verification 0, and curl exit 28 due to the live stream timeout.
- Old and new images both run as UID 1000. TLS config and PEM are UID 1000, mode 0600, so there is no evidence for a permission mismatch.
- TLS config uses legacy ssl and ssl-certificate XML tags. The Icecast official January 2026 announcement explicitly states that 2.5.x still reads Icecast 2.4.x XML. Legacy warnings are possible, but a tag alone does not prove TLS failure.

**Before trying another Production upgrade**, execute this radio-only throwaway canary in the approved IOT host from the reviewed Git checkout:

    sudo bash scripts/diagnose-icecast-2.5-tls.sh

The script requires the already cached 2.5.0 image, mounts private TLS XML and PEM read-only, bypasses the image's XML-editing entrypoint, and exposes HTTPS only on host loopback 127.0.0.1:8866. It sends SNI radio.rcat.ac.th and checks the real certificate chain. It removes its own container on exit and does not stop or recreate Production 2.4.4. If port 8866 is busy, stop rather than affecting its owner.

An affirmative canary result proves **only that the existing XML + PEM work with Icecast 2.5 TLS startup**. The canary has no Live DJ or AutoDJ source and cannot test MP3 or the mobile 2-second problem. If it succeeds, next prioritize inspecting the Production upgrade's one-shot 7-second curl readiness and Liquidsoap source reconnect timing rather than changing TLS XML without evidence. If it fails, diagnose the ephemeral container's TLS logs before any Production changes.

Official sources: https://icecast.org/news/end-of-support-2_4_4/ and https://www.icecast.org/docs/icecast-latest/config_file/.

## Simplified direct operation (2026-11-14)

The owner explicitly requested a direct upgrade instead of further separate canary or repeated preflight commands. The --apply path already executes the preflight internally, so only ONE command is necessary after pulling updated source. The script no longer requires /main.mp3 audio within the first seven seconds; that old check caused a rollback even though HTTP/TLS and source readiness were not separately diagnosed. The upgraded container must still run and serve a certificate-valid HTTPS status page. The 2.5.0 upgrade and mobile playback remain pending Host confirmation.

    sudo python3 scripts/upgrade-icecast-2.5.py --apply --approve-brief-stream-reconnect

This interrupts Icecast listeners briefly once. Do not run the isolated test container first or repeat the historical installer; LibreTime and the shared host remain outside this change.
