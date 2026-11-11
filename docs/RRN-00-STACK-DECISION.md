# RRN-00 — SHOUTcast DNAS + Ready-Made AutoDJ/Control Panel Selection

**Research date:** 2026-11-11  
**Decision state:** PREFERRED CANDIDATE — NOT APPROVED FOR PURCHASE OR DEPLOYMENT  
**Parent:** [RRN-00 Issue #2](https://github.com/yiwssx/rcat-radio-network/issues/2)  
**Project:** [RCAT Radio Network](https://github.com/yiwssx/rcat-radio-network)

## Executive decision

**Preferred option:** a vendor-hosted **SHOUTcast DNAS v2 + Centova Cast v3 AutoDJ** service, with **YesStreaming** as the current candidate.

**Reference product:** YesStreaming **US SHOUTcast V2 128 kbps / 500 simultaneous listeners / 15 GB AutoDJ**, advertised at **USD 16.99/month** on the vendor's product catalog (price subject to checkout confirmation, taxes, and changes).

**Why:** The project's shared Ubuntu server was previously reported as **Ubuntu 26.04.1 LTS, x86_64** (November 9 operator evidence), while the evaluated self-hosted panels do not list that exact Ubuntu release as supported. A shared-host installation could introduce incompatible system packages, unsupported root-level installer changes, or conflicts with the existing PDF HUB and AnyFlip applications. Vendor-hosted streaming keeps the broadcast stack separate and does not require any SHOUTcast/control-panel installation on that server.

**Critical caveat:** This recommendation changes the original local-host deployment assumption and introduces a recurring external-service cost. **Owner approval is mandatory before final product selection, ordering, account setup, DNS changes, or implementation.** RRN-00 remains OPEN.

## Requirements and evidence boundary

The project's V1 requirement is **one online station** using off-the-shelf software, with:
- SHOUTcast DNAS v2 as the stream server;
- control-panel uploads and straightforward AutoDJ playlists;
- standard encoder-based Live DJ (BUTT/Mixxx) with automatic return to AutoDJ on disconnect;
- a secure listener player/HTTPS, separate administration access, and minimal backup/operations procedures;
- no bespoke React/Fastify application, browser DJ studio, custom streaming engine, or multi-station platform.

The historical host evidence is **not** a live inventory or current resource/port verification. It establishes an OS compatibility concern, not an installation failure. The earlier operator also confirmed removal of the legacy AzuraCast stack and HTTP 200 responses from PDF HUB and AnyFlip after removal. Do not repeat these unrelated checks until a specific new change warrants them.

## Comparison of three shortlisted options

| Criterion | MediaCP + SHOUTcast (self-host) | Centova Cast + SHOUTcast (self-host) | YesStreaming SHOUTcast v2 + Centova Cast (vendor-hosted) |
|---|---|---|---|
| Vendor-supported OS / placement | Vendor lists Debian 12/13, Ubuntu 22.04/24.04 and other Linux variants; **Ubuntu 26.04 is not listed**. Vendor recommends a dedicated server, Debian 13 for new installations. | Vendor lists CentOS/RHEL, AlmaLinux/Rocky, and Debian Stable; **Ubuntu is not listed**. | Runs on the provider's infrastructure; the RCAT host OS does not constrain the streaming stack. |
| SHOUTcast compatibility | Vendor explicitly supports SHOUTcast 1.9.8 and 2.x. | Vendor lists SHOUTcast v1.9 and v2.x. | Provider explicitly describes **SHOUTcast DNAS v2** managed with Centova Cast v3. |
| AutoDJ music uploads and playlists | Supported by MediaCP media library and Liquidsoap AutoDJ. | Supported by Centova Cast media library and AutoDJ. | Provider explicitly advertises music uploads and AutoDJ playlists; 15 GB included in the reference plan. |
| Live DJ / return to AutoDJ | Separate DJ logins and priority are documented; AutoDJ-on-air events include resumption after a Live DJ disconnects. | SHOUTcast v2 DJ/AutoDJ support exists; compatibility of a given installation still requires configuration verification. | Provider explicitly advertises automatic switching between Live and AutoDJ when the live feed disconnects. |
| Player / TLS | Built-in HTML5 player and HTTPS proxy advertised. | Panel and stream integration possible; HTTPS exposure is an operator responsibility. | Provider advertises secure streaming links and Centova panel. Confirm the exact custom-domain/player workflow before purchase. |
| Host installation impact | Medium-to-high: root-level services and ports 80/443/2020, FTP and streaming ports; may conflict on the shared host. | Medium-to-high: vendor OS mismatch and privileged system installation; not supported on the existing Ubuntu release. | Low impact on the RCAT Ubuntu host; a future static player/domain change may still require approval. |
| Publicly advertised cost | **USD 12/month** for a single-station MediaCP panel license; own server, bandwidth, and any operational costs extra. | **USD 11/month** listed for a 10-station Centova Cast software package; hosting not included. | **USD 16.99/month** for the stated US SHOUTcast v2 128 kbps / 500-listener / 15 GB AutoDJ plan; confirm fees in checkout. |
| RRN-00 outcome | **Not selected** for the current Ubuntu 26.04 shared host. | **Not selected** for the current Ubuntu 26.04 shared host. | **Preferred, conditional on owner approval and current vendor confirmation.** |

The 500-listener cap is a starter plan limit, **not a forecast of maximum station demand**. Upgrade options exist in the vendor catalog, but their final prices and migration terms must be confirmed before relying on them.

## Vendor documentation and primary sources

1. MediaCP official system requirements, supported OS list, dedicated-server guidance, and port requirements: https://www.mediacp.net/doc/admin-server-manual/install/system-requirements/
2. MediaCP official panel pricing (single station, USD 12/month): https://www.mediacp.net/pricing/
3. MediaCP official SHOUTcast/AutoDJ/HTML5 player capabilities: https://www.mediacp.net/mediacp/shoutcast-control-panel/
4. MediaCP Live DJ connections: https://www.mediacp.net/doc/user-manual/audio/live-dj-connections/
5. MediaCP AutoDJ event descriptions, including resume after Live DJ disconnects: https://www.mediacp.net/doc/user-manual/audio/audio-stream-events/
6. Centova Cast official supported OS: https://centova.com/en/cast/requirements
7. Centova Cast official license packages and pricing (software only): https://centova.com/en/cast/packages
8. YesStreaming official technology description (SHOUTcast DNAS v2 with Centova Cast v3, playlist fallback): https://www.yesstreaming.com/get-started
9. YesStreaming official SHOUTcast V2 128 kbps / 500-listener / 15 GB AutoDJ product listing: https://my.yesstreaming.com/store/usa-server-shoutcast-v2-plan
10. YesStreaming support FAQ confirming SHOUTcast DNAS v2: https://my.yesstreaming.com/knowledgebase/71/Can-I-Stream-Live-with-a-Shoutcast-V1-Source.html
11. YesStreaming main hosting features, HTTPS and fallback: https://www.yesstreaming.com/shoutcast-hosting
12. SHOUTcast official pricing (basic self-host server software is free; additional AutoDJ/panel or hosting is separate): https://www.shoutcast.com/pricing

**Research limitation:** Provider feature/pricing pages are vendor claims, not independent uptime, billing, security, or performance audits. The selected subscription and exact billing terms were not validated in a checkout session, and no trial account was created. The specific underlying DNAS build and vendor patch cadence were not independently inspected.

## RRN-00 owner decision required

Confirm **one** of the following:
1. **Approve managed hosting in principle:** a recurring externally hosted SHOUTcast v2 + AutoDJ plan, with YesStreaming as the candidate and a starting vendor-advertised price of **USD 16.99/month** (plus any applicable taxes/fees). This is not authorization to pay or deploy; final order specifics and use of the public domain remain separate approvals.
2. **Require self-hosting:** keep the broadcast engine on institution-controlled infrastructure, but use a separately isolated **vendor-supported** OS/server or obtain explicit vendor support for Ubuntu 26.04 before installing a control panel. Costs and resource requirements will need a new decision record.
3. **No recurring cost:** record a blocker and do not assert that SHOUTcast DNAS alone provides the required web AutoDJ/control panel.

Further vendor confirmations if option 1 is approved: actual panel/version and SHOUTcast v2 availability on the selected plan, operator/DJ roles, ability to export station media/configuration, HTTPS player URL and custom-domain support, payment/renewal terms, external data retention, and Thailand playback latency.

## Acceptance status

- [x] Compared a maximum of three options, including official sources and stated license costs.
- [x] Documented vendor-stated SHOUTcast DNAS, AutoDJ, and Live DJ-to-AutoDJ fallback functionality.
- [x] Recorded host OS mismatch, installation limitations, and an alternative with reduced shared-host risk.
- [ ] Owner approves the hosting model and any recurring financial commitment.
- [ ] Final vendor/product/plan and required compatibility are confirmed; then close RRN-00 and adapt downstream implementation issues if the hosting model changes.

**Guardrail:** No software deployed, no subscriptions ordered, and no DNS, reverse-proxy, firewall, or Production configuration changed as part of this research.
