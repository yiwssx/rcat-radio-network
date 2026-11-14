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

The upgrade requires root, the original isolated ten-service stack, running Icecast 2.4.4, an existing RRN-06 archive checksum, and existing native TLS port 8443. It pulls the new image before altering anything, writes a private timestamped Compose rollback snapshot, replaces ONLY the Icecast image tag, and confirms the rendered configuration is otherwise identical. Then it recreates ONLY Icecast and checks that the Host can download real MP3 bytes over correctly verified TLS. An error after editing attempts automatic Icecast-only rollback. The command interrupts listening briefly; it does not restart other services or modify volumes, certs, NAT, DNS or RMS Apache.

Do not rerun historical initial installer/TLS installation scripts. The existing certificate renewal receiver uses the installed Compose configuration and remains in place.

## Mobile acceptance after successful Host operation

1. Phone on Wi-Fi: direct https://radio.rcat.ac.th:8600/main.mp3 continuously for at least two minutes.
2. Second phone using a different network: same direct stream, also two minutes.
3. Desktop: existing direct stream continues.
4. One public Listening-page mobile playback check for two minutes; no frontend deploy required.

Only after operator results may this be marked mobile PASS. A passing curl on IOT is NOT mobile acceptance.

## Rollback if mobile still stops at two seconds

Use the EXACT path printed as ROLLBACK_COMPOSE_SNAPSHOT by the successful Host script; the timestamp here is intentionally illustrative:

    sudo install -o root -g root -m 600 /var/backups/rcat-radio-network/icecast-compose-before-2.5.0-YYYYMMDDTHHMMSSZ.yml /opt/rcat-libretime-runtime/docker-compose.yml
    sudo docker compose --project-directory /opt/rcat-libretime-runtime --env-file /etc/rcat-radio-network/compose.env -p rcat_radio_network -f /opt/rcat-libretime-runtime/docker-compose.yml -f /opt/rcat-libretime-runtime/radio.override.yml up -d --no-deps --pull never --force-recreate icecast

Never use docker compose down -v, prune or mass-upgrade the host. If the 2-second problem persists, collect a mobile HTTP/TLS trace before changing any more services.
