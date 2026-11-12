# RRN-00 — Accepted Stack: Icecast + LibreTime

**Decision date:** November 12, 2026  
**Decision status:** ACCEPTED FOR PLANNING — NOT DEPLOYED OR RUNTIME-VERIFIED  
**Decision owner:** RCAT project owner (explicit approval in conversation)  
**Tracker:** [RRN-00 #2](https://github.com/yiwssx/rcat-radio-network/issues/2)

## Decision

Use **LibreTime 4.5.0 with its bundled Icecast 2.4.4**, plus a free standard Live DJ encoder (BUTT or Mixxx), for **one RCAT online radio station** on existing RCAT infrastructure, subject to the existing shared-host safety gate.

- **Icecast 2.4.4:** already included in the pinned LibreTime 4.5.0 upstream Docker Compose. Retain this bundled version initially; **do not silently upgrade to Icecast 2.5.0** without compatibility and change justification.
- **LibreTime 4.5.0:** ready-made web application for uploading media, scheduling/programming playlists, AutoDJ playout, and handling live input. Use its official release files, not custom streaming/control-panel code.
- **BUTT or Mixxx:** standard free Live DJ encoder connected to **LibreTime's input**, not directly to Icecast, so LibreTime can handle switching and resume AutoDJ.
- **No incremental software license or hosted-radio subscription fees.** The existing host's energy, bandwidth, administration, storage, and public broadcast/music rights are separate obligations.

The chosen solution deliberately accepts LibreTime's **ten-service** Compose footprint to obtain its existing web-based media and scheduling features. Icecast itself is lightweight; LibreTime's other services remain part of the packaged system.

## Why this replaces SHOUTcast

The earlier candidates (paid hosted panel, SHOUTcast Basic Freemium, and legacy SHOUTcast DNAS builds) were researched and documented in earlier Git history. The owner has now expressly approved changing the streaming engine to **Icecast**.

SHOUTcast Basic requires registration, is proprietary, and its official pricing page states mandatory pre-roll advertising. Legacy pre-2.5 DNAS versions are unsupported. An extra DNAS binary and an unproven LibreTime-to-DNAS integration would add little value to a single free station. **These SHOUTcast procurement, licensing, legacy-version and v2 compatibility gates are superseded, not silently counted as passing.**

Do not download proprietary DNAS, purchase SHOUTcast/MediaCP/Centova, or reintroduce AzuraCast without a new owner decision.

## Official upstream compatibility evidence

1. The [LibreTime 4.5.0 Compose file](https://github.com/libretime/libretime/blob/4.5.0/docker-compose.yml) explicitly includes `icecast: ghcr.io/libretime/icecast:2.4.4`, plus PostgreSQL, RabbitMQ, Liquidsoap, playout, API, legacy, worker, analyzer, and nginx.
2. The [LibreTime 4.5.0 configuration template](https://github.com/libretime/libretime/blob/4.5.0/docker/config.template.yml) has a **bundled Icecast output enabled by default**, using internal service host `icecast` on port `8000`.
3. The [official LibreTime Docker installation guide](https://libretime.org/docs/admin-manual/install/install-using-docker/) describes the packaged installation with pinned version `4.5.0`.
4. The [LibreTime streaming documentation](https://libretime.org/docs/admin-manual/stream-configuration/) expressly supports Icecast output and MP3 (and other compatible formats).
5. The [LibreTime Stream Settings manual](https://libretime.org/docs/user-manual/settings/) documents **Auto Switch On** and **Auto Switch Off** for a live input's connection/disconnection. This establishes **documented product capability**, not observed runtime behavior in RCAT.
6. [Icecast's official site](https://icecast.org/) confirms its GPL-based open-source licensing; it separately advertises Icecast 2.5.0, which is **not** the bundled 2.4.4 image in LibreTime 4.5.0.

## Interface and deployment plan

| Function | Planned component | Boundary |
|---|---|---|
| Stream server | Bundled Icecast 2.4.4 | Internal Compose hostname `icecast:8000`; **candidate host loopback port 8600** for controlled listener tests |
| AutoDJ / playlists / uploads | LibreTime 4.5.0 | `127.0.0.1:8700 -> nginx:8080` (candidate only) |
| One Live DJ | LibreTime **Show Source** via Liquidsoap | `127.0.0.1:8605 -> liquidsoap:8002` (candidate only; use approved access mechanism) |
| PostgreSQL / RabbitMQ | Bundled internal services | Private Compose network; do not publish host ports |
| Public listener URL | Existing approved ingress (future) | No DNS, HTTPS, reverse-proxy or firewall changes until separately approved |

**Port values are proposed, not verified free today.** A Docker container's `localhost` is not the host's `localhost`; use the Compose service name `icecast` for internal LibreTime output. Remove the previous plan to add a second SHOUTcast process entirely.

## Selection acceptance criteria (RRN-00)

- [x] Owner explicitly selects Icecast rather than SHOUTcast and maintains the USD 0 incremental software/hosting-fee requirement.
- [x] The upstream version-pinned LibreTime 4.5.0 Compose already bundles Icecast 2.4.4.
- [x] The matching LibreTime config template already defines the Icecast output.
- [x] Official LibreTime documentation identifies live input and automatic switching controls.
- [x] Existing tracker, implementation paths, and dependent acceptance criteria are revised without creating new workstreams.

**RRN-00 is a product-selection milestone, not a runtime acceptance gate.** Close RRN-00 as **completed** based on upstream artifacts and owner approval. Keep remaining live proof in existing implementation issues instead:
- **RRN-01 #3:** One current-host read-only preflight immediately before authorized installation.
- **RRN-02 #4:** Install the existing upstream bundle within radio-only boundaries and check an actual Icecast listener stream.
- **RRN-03 #5:** Web media upload and audible AutoDJ playlist.
- **RRN-04 #6:** One actual Live DJ → AutoDJ automatic fallback, with no redundant tests.
- **RRN-05 #7:** Public player and HTTPS authorization.
- **RRN-06 #8:** Backup, SOP and proportionate final sign-off.

No code execution or external runtime check has occurred. Keep RRN-01 through RRN-06 open until actual evidence exists.

## Explicit exclusions and guardrails

- Never use a paid control panel, new external hosting subscription, custom gateway, custom admin/frontend, or AzuraCast as an unapproved substitute.
- Do not launch the vendor's unmodified Compose on the shared host: its default host ports **8000, 8001, 8002, 8080**, example credentials, and `latest` image fallback need explicit containment/version pins.
- Do not delete or restart PDF HUB, AnyFlip, or the shared Docker Engine.
- Do not expose DJ inputs, panel administration, database, RabbitMQ, or Icecast admin credentials publicly.
- No installation, purchase, Production operation, public launch, DNS change, shared proxy change or firewall change is authorized by this decision.
- Avoid needless repeat testing; one scoped end-to-end acceptance pass is enough if the actual evidence supports it.

**Historical SHOUTcast research remains available in this document's Git commit history, but is no longer an active dependency.**
