# RRN-00 — Zero-Recurring-Fee SHOUTcast and AutoDJ Stack Selection

**Revised:** November 11, 2026  
**Owner decision:** No paid software licenses, no paid radio hosting, and no new monthly subscription.  
**Decision status:** FREE STACK SELECTED IN PRINCIPLE; VERSION-COMPATIBILITY CHECK PENDING  
**Tracker:** [Issue #2 — RRN-00](https://github.com/yiwssx/rcat-radio-network/issues/2)

> This decision **supersedes** the November 11 proposal to subscribe to YesStreaming at USD 16.99/month. That proposal is rejected by the project owner on cost grounds and must not be treated as the current recommendation. No purchase or deployment has been authorized.

## Decision

**Preferred no-new-fee stack:**

1. **SHOUTcast Basic (DNAS)** — vendor-provided Linux streaming server under a free/freemium license; plan around **MP3 at 128 kbps** and review the current licensing, registration, advertising, and directory terms before public launch.
2. **LibreTime v4.5.0** — open-source web-based media library, playlists, radio automation and Live DJ inputs, using its **official Docker Compose distribution** and its documented `stream.outputs.shoutcast` configuration.
3. **BUTT or Mixxx** — free conventional Live DJ broadcast applications, already covered by LibreTime's user guide.
4. **Existing RCAT Ubuntu host** — no new hosting bill; isolate the station's containers, data, credentials, ports, and ingress from PDF HUB and AnyFlip.

**Cost target:** **USD 0/month in incremental software license and external radio-hosting fees**. This does not eliminate electricity, the existing server's internet connection, administration, bandwidth, backups, or rights to broadcast copyrighted audio.

**Do not deploy yet.** The documentation supports LibreTime's ability to configure a SHOUTcast output, but a successful connection and **automatic Live DJ → AutoDJ recovery using the exact chosen DNAS 2 build have not been demonstrated**. This is the only integration behavior that must be checked before considering the software selection technically confirmed. There is a March 2026 LibreTime community report of difficulties connecting v4.5.0 to SHOUTcast v2.6.1.777; a report is not proof the combination is broken, but it prevents declaring compatibility proven without a targeted reproduction.

## Evidence and official references

- SHOUTcast's [Basic product page](https://www.shoutcast.com/pricing/basic) offers the self-hosted Linux server for free. [Its server license terms](https://www.shoutcast.com/legal/agreements/dnas) describe free/freemium use and MP3 128 kbps restrictions; the published legal text has an older revision date, so confirm current account conditions when obtaining the server.
- LibreTime's [official repository](https://github.com/libretime/libretime) is open-source (AGPL-3.0).
- LibreTime's [stable 4.x configuration guide](https://libretime.org/docs/admin-manual/configuration/) explicitly documents a `stream.outputs.shoutcast` output, host, port, credentials, MP3 and AAC encoding. This supports source compatibility **in documented configuration**, not an end-to-end proven v4.5.0 deployment.
- LibreTime's [Docker installation guide](https://libretime.org/docs/stable-3.x/admin-manual/install/install-using-docker/) provides a v4.5.0 Compose distribution; [official releases](https://github.com/libretime/libretime/releases) list v4.5.0 as the latest tagged release as checked on this research date.
- LibreTime's [Live broadcasting manual](https://libretime.org/docs/user-manual/live-broadcast/) documents BUTT/Mixxx input configuration and live-source behavior, including the possible need to toggle the live source.
- [LibreTime community report, March 2026](https://discourse.libretime.org/t/broadcast-to-shoutcast-with-libretime-4-5-0/1970) documents reported problems with v4.5.0 and SHOUTcast servers. **Treat as a targeted compatibility risk, not vendor-confirmed incompatibility.**
- [Surcast](https://radio-sur.github.io/) is a free all-in-one web radio option, but currently advertises **Icecast**, not SHOUTcast DNAS. It is only a possible fallback if the SHOUTcast-engine requirement is explicitly relaxed.

## At-most-three-option comparison

| Option | Software/hosting fees | Web music uploads and playlists | SHOUTcast DNAS | Live DJ / AutoDJ fallback | Operational cost and verdict |
|---|---|---|---|---|---|
| **SHOUTcast Basic + LibreTime v4.5.0 (Docker)** | **USD 0 incremental license/hosting** on existing host | Yes, via LibreTime | Official LibreTime configuration documents SHOUTcast output; **DNAS v2 connection not yet proven** | LibreTime supports live input; exact automatic recovery path to DNAS output **requires a targeted check** | **Preferred free candidate**, but a multi-service stack (Postgres, RabbitMQ, Liquidsoap, web API, etc.), not a single lightweight daemon |
| SHOUTcast Basic + standalone Liquidsoap | **USD 0 incremental license/hosting** on existing host | **No ready-made web control panel** in this pairing | Liquidsoap can serve as an encoder/source in principle; exact source configuration not checked | Requires manual integration/routing; no verified ready-made handoff | Reject for V1: insufficient web management, risks creating a custom project |
| Surcast + its bundled Icecast | **USD 0 incremental license/hosting** on existing host | Advertised as present | **No: Icecast rather than SHOUTcast** | Live workflow and fallback specifics not fully validated for this use | Only revisit if owner later relaxes the SHOUTcast DNAS requirement |

**AzuraCast is excluded by prior explicit owner decision.** Do not reopen it as the default free choice.

## Host-safety and minimal implementation constraints

The RCAT operator previously reported Ubuntu **26.04.1 LTS** on the shared server. Since the selected LibreTime installation method is container-based, check the pinned images' actual architecture, kernel requirements, port mappings, and volume paths rather than claiming that a native LibreTime installer supports Ubuntu 26.04. In particular:

- Confirm the actual host architecture and free capacity before installation; previous inventory is historical, not a live inspection.
- Inspect LibreTime's default Compose for PostgreSQL, RabbitMQ, Liquidsoap, web, and any bundled Icecast service. Do not accidentally expose default 80/443 or conflict with existing shared services.
- Keep SHOUTcast DNAS and LibreTime configurations and data isolated. Do **not** assume an arbitrary third-party SHOUTcast Docker image is officially supported; validate the official DNAS binary distribution/license first.
- Store credentials outside Git. Bind administration privately and use an explicitly approved TLS/reverse-proxy setup.
- The music library starts empty. Use only authorized sample audio for a single audibility and failover check; do not repeat unrelated tests already evidenced.
- No host-level installer, daemon change, DNS/proxy/firewall modification, deployment, or data deletion is authorized by this decision record.

## Targeted feasibility check before completing RRN-00

1. Validate a reproducible, supported SHOUTcast Basic DNAS v2 Linux binary distribution and actual freemium obligations (account, 128 kbps MP3, advertisements/directory terms).
2. Review LibreTime v4.5.0's shipped `docker-compose.yml`/configuration for isolated use on the shared host, including disabling or isolating unnecessary default Icecast output/services without breaking required dependencies.
3. Confirm that LibreTime can publish a playlist to the selected DNAS source using documented configuration.
4. Confirm one Live DJ input and one normal disconnect/fallback. If default behavior requires manual source toggling, describe that limitation accurately; do **not** build a custom gateway to conceal it.
5. If the exact product combination is not feasible without unsupported patching, keep RRN-00 blocked and recommend the simplest **free** supported alternative; do not silently switch to a paid product or reintroduce AzuraCast.

This is a **single narrowly scoped feasibility check**, not a full production acceptance suite. Execution needs separate approval for server-side deployment.

## Status and issue ownership

- **Resolved:** Free-only cost requirement; paid-hosting candidate rejected; a documented free stack candidate identified.
- **Still open:** Actual supported SHOUTcast DNAS v2 binary/version, the LibreTime v4.5.0 integration path, and confirmed Live DJ fallback. Track these under **RRN-00 (#2)** and host layout under **RRN-01 (#3)**; do not create a new issue.
- **No work performed on RCAT Production:** This record updates selection and documentation only.

## License and rights reminder

SHOUTcast Basic is **free/freemium**, not open-source software. LibreTime is AGPL-licensed open source. Neither license grants music-copyright broadcasting rights; verify rights before public audio transmission.

## Evidence update — November 11, 2026 (documentation and release files inspected)

### SHOUTcast DNAS Basic licensing and acquisition

- The [official Basic page](https://www.shoutcast.com/pricing/basic) lists the self-hosted Linux server as free. Its [license agreement](https://www.shoutcast.com/legal/agreements/dnas) limits the freemium streaming format to **MP3 at 128 kbps**.
- The [official SHOUTcast download portal](https://directory.shoutcast.com/BroadcastNow) explicitly requires a **SHOUTcast member login/registration** to access DNAS downloads; the actual distributable package, current version, download checksum, and package redistributability have **not** been verified. Do not add closed-source DNAS binaries to this public repository or download from an unofficial mirror.
- The Basic product page states that **pre-roll advertising is mandatory**. It separately advertises native SSL support, while the legal agreement lists a custom SSL certificate among premium features. Exact Basic-plan HTTPS behavior therefore requires confirmation. In particular, a free license does not necessarily imply an ad-free listener experience.
- This is a zero **subscription** target, not an ad-free or unlimited-feature guarantee.

### LibreTime 4.5.0 — upstream release files (not a running test)

The upstream pinned **tag is `4.5.0` (not `v4.5.0`)**. The official [4.5.0 Compose file](https://github.com/libretime/libretime/blob/4.5.0/docker-compose.yml) defines **ten services**: `postgres`, `rabbitmq`, `playout`, `liquidsoap`, `analyzer`, `worker`, `api`, `legacy`, `nginx`, and `icecast`; SHOUTcast DNAS would be an additional runtime component.

The upstream Compose defaults publish:
- `nginx` on **8080/tcp**;
- `liquidsoap` live inputs on **8001/tcp** and **8002/tcp**;
- bundled `icecast` on **8000/tcp**.

The [upstream config template](https://github.com/libretime/libretime/blob/4.5.0/docker/config.template.yml) ships **enabled default Icecast output**. It must be deliberately reconfigured for SHOUTcast; never start the upstream Compose on the shared RCAT host unreviewed. The 4.5.0 template contains example/default credentials which must be replaced and kept out of Git. This is a substantial multi-service deployment rather than a lightweight one-process SHOUTcast control panel.

The [official LibreTime Docker installation guide](https://libretime.org/docs/stable-3.x/admin-manual/install/install-using-docker/) references `4.5.0` and an initial database migration. These instructions describe installation but have **not** been run on the RCAT server.

### Live DJ switching — documented setting, not yet integration-proven

The official [LibreTime Stream Settings manual](https://libretime.org/docs/user-manual/settings/) documents:
- **Auto Switch On:** automatically selects an authenticated Live DJ input when it connects.
- **Auto Switch Off:** resumes scheduled playback when the input disconnects.
- A configurable transition fade and separate Source Stream credentials.

Therefore the **LibreTime source-level auto-fallback feature is supported by official documentation**. The outstanding test is narrower: confirm that the combined LibreTime 4.5.0 / actual free SHOUTcast DNAS v2 configuration sends valid audio continuously before, during, and after a Live DJ connection. A [March 2026 community case](https://discourse.libretime.org/t/broadcast-to-shoutcast-with-libretime-4-5-0/1970) reports a v4.5.0 to SHOUTcast issue, with no confirmed resolution in the published discussion. Avoid treating the report as a general product defect; equally, do not call the combination tested.

### Concise remaining gate (not a new project)

| Check | Evidence level | Remaining action |
|---|---|---|
| SHOUTcast Basic legal 128 kbps MP3 restriction, account requirement, mandatory pre-roll | Official product/legal statements: **verified** | Obtain owner's acceptance of these free-plan terms |
| LibreTime upstream release tag, service list, and default published ports | Official 4.5.0 source: **verified** | Apply radio-only network isolation under existing RRN-01 |
| Auto Switch On/Off functionality | Official LibreTime manual: **verified in documentation** | Enable both in the eventual single focused live test |
| Exact DNAS 2 Linux package build and right to use/distribute | **Not verified** (account-gated download) | Access through official SHOUTcast registration; do not put software in Git |
| LibreTime v4.5.0 to exact DNAS 2 live stream + AutoDJ return | **Not tested** | Run **one** isolated compatibility test after access and explicit deployment/test approval |

**RRN-00 status: BLOCKED FOR AN INTEGRATION PASS, NOT COMPLETE.** Do not convert documentation verification into an acceptance sign-off. No changes to existing RCAT Production systems are authorized by this document.
