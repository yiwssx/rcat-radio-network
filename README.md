# RCAT Radio Network

A single online radio station for Roi-Et College of Agriculture and Technology (RCAT), using **LibreTime 4.5.0** and its bundled **Icecast 2.4.4**.

This repository contains RCAT deployment scripts, configuration examples and operating documentation. Media uploads, scheduling, playlists, AutoDJ and authenticated Live DJ use the existing LibreTime interface and services.

## Project status

**Main technical delivery is complete.** [Master Tracker #1](https://github.com/yiwssx/rcat-radio-network/issues/1) and all seven RRN-00–RRN-06 work items are closed within the owner-approved scope.

| Work | Accepted outcome |
| --- | --- |
| Stack and host boundaries — [RRN-00 #2](https://github.com/yiwssx/rcat-radio-network/issues/2), [RRN-01 #3](https://github.com/yiwssx/rcat-radio-network/issues/3) | Selected the vendor stack and completed the isolated host/Compose preflight. |
| Installation and AutoDJ — [RRN-02 #4](https://github.com/yiwssx/rcat-radio-network/issues/4), [RRN-03 #5](https://github.com/yiwssx/rcat-radio-network/issues/5) | Installed the radio runtime; private scheduled audio was accepted by the owner. Further playlist operations are normal station use. |
| Live DJ — [RRN-04 #6](https://github.com/yiwssx/rcat-radio-network/issues/6) | Owner confirmed Show Source live handoff and automatic return to AutoDJ. |
| HTTPS and certificates — [RRN-05 #7](https://github.com/yiwssx/rcat-radio-network/issues/7) | Listener website, HTTPS stream/Admin routes and certificate-sync handoff accepted from operator evidence. |
| Local backup and SOP — [RRN-06 #8](https://github.com/yiwssx/rcat-radio-network/issues/8) | Actual cold archive and separate SHA-256 check passed. Restore execution was waived by the owner; offsite storage, retention and backup automation are deferred. |

These are recorded acceptance results, not continuous live monitoring. The final issue dispositions take precedence over older pending statements in planning documents.

**Later work:** [Listener UI/UX #22](https://github.com/yiwssx/rcat-radio-network/issues/22) is a deferred follow-up covering the screenshot-reported garbled Thai text, responsive layout and player usability. It does not reopen the completed main delivery. No listener redesign is being implemented as part of this documentation update.

## Station access

| Purpose | Recorded endpoint |
| --- | --- |
| Public listener page | [radio.rcat.ac.th](https://radio.rcat.ac.th/) |
| Icecast MP3 stream | [HTTPS stream](https://radio.rcat.ac.th:8600/main.mp3) |
| LibreTime administration | [HTTPS Admin login](https://radio.rcat.ac.th:8700/login) |

Listening does not require an administrator account. Admin access uses authorized LibreTime credentials. DJs use the authenticated LibreTime **Show Source**, documented in the [Live DJ SOP](docs/RRN-04-LIVE-DJ-SOP.md).

The deployed access arrangement uses the existing RMS Apache for the static listener page and HTTPS Admin proxy, with native Icecast TLS on IOT for the stream. The radio runtime retains the vendor's ten-service Compose stack, including PostgreSQL and RabbitMQ.

## Runtime and backup locations

| Item | Location on IOT |
| --- | --- |
| Isolated Compose runtime | `/opt/rcat-libretime-runtime/` |
| Private application configuration and credentials | `/etc/rcat-radio-network/` |
| Compose project | `rcat_radio_network` |
| Radio-only local backups | `/var/backups/rcat-radio-network/` |

The accepted first archive is `rcat_radio_network-20261113T021024Z.tar.gz`, with an adjacent `.sha256` sidecar. It covers three radio data volumes (database, media storage and playout), private configuration/credentials and Compose files **as they existed at backup time**.

The archive contains sensitive credentials and must stay private. No isolated restore was performed; it was waived as a closeout requirement. The owner reports RAID 1 on IOT; mirroring does not establish restore usability or protect against mirrored deletion/corruption or whole-host loss.

## Documentation and operation

- [Accepted stack decision](docs/RRN-00-STACK-DECISION.md) and [host boundaries](docs/RRN-01-HOST-BOUNDARIES.md).
- [Live DJ and AutoDJ fallback](docs/RRN-04-LIVE-DJ-SOP.md).
- [HTTPS access arrangement](docs/RRN-05-HTTPS-ACCESS-V2.md) and [installation references](docs/RRN-05-FINAL-INSTALLATION.md).
- [Final certificate-renewal handoff](docs/RRN-05-FINAL-HANDOFF.md).
- [Backup, recovery and operator SOP](docs/RRN-06-BACKUP-RECOVERY-SOP.md).

The scripts in `scripts/` are operation-specific guarded tools, not a command sequence to rerun on a working installation. Preserve existing data volumes and the historical checkout; use the relevant procedure for a specifically requested change.

Routine station operation includes scheduling audio, managing users, monitoring the existing renewal scheduler, maintaining distinct strong credentials, holding the required broadcast rights, and using protected remote-DJ transport. The existing Show Source TCP path is not TLS by default. These responsibilities are described in the handoff; no extra implementation work is opened here.

## Manual signed source candidate

The existing [manual workflow](.github/workflows/signed-source-release.yml) can package the exact reviewed `main` commit. Only the `yiwssx` account on `main` can invoke its signing job. It archives Git-tracked source, generates SHA-256, and uses `actions/attest@v4` to attest the actual archive bytes. The Actions artifact retention is 14 days.

A consumer must verify the downloaded checksum and independently run:

```bash
gh attestation verify <archive> --repo yiwssx/rcat-radio-network
```

The attestation covers repository source, not upstream container image bytes, private runtime settings, media rights, backup recovery or a live station. This manual workflow performs no Host deployment, SSH, DNS change, GHCR push or GitHub Release publication.

## License

The original RCAT-authored scripts, configuration examples and documentation in this repository are licensed under the [MIT License](LICENSE).

Copyright (c) 2026 Roi-Et College of Agriculture and Technology.

MIT applies to original material for which the college holds licensing rights. It does not relicense third-party software or material copied or adapted from upstream projects. Those materials remain subject to their applicable licenses and notices.

| Component or material | License scope |
| --- | --- |
| Original RCAT-authored repository material | [MIT](LICENSE) |
| LibreTime 4.5.0 | [GNU AGPL version 3](https://github.com/libretime/libretime/blob/4.5.0/LICENSE) |
| Icecast | [GNU GPL version 2](https://www.icecast.org/) |
| Other third-party dependencies or adapted material | Respective upstream licenses and notices |

Software licensing does not grant rights to broadcast music or use institutional logos, names or other separately controlled content.
