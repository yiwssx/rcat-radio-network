---
name: radio-stack-selection
description: Maintain the owner-approved zero-fee Icecast 2.4.4 plus LibreTime 4.5.0 stack decision for RCAT Radio Network. Use for scope, license, upstream compatibility, deployment prerequisites, and requests to reconsider a streaming engine or control panel.
---

# RCAT Radio Stack Selection

## Accepted decision

**RRN-00 #2 is completed for product selection:** use **LibreTime 4.5.0 + the Icecast 2.4.4 image bundled in its official Compose file**. Use a standard free encoder (BUTT or Mixxx) for Live DJ. Incremental software-license and radio-hosting subscription fees must remain **USD 0**.

Prior SHOUTcast selection, legacy builds, managed hosting, media panels and AzuraCast are **superseded**. Do not reinstate them or change to Icecast 2.5.x without an explicit new owner decision.

## Source of truth

- [Master tracker #1](https://github.com/yiwssx/rcat-radio-network/issues/1)
- [Selection record](https://github.com/yiwssx/rcat-radio-network/blob/main/docs/RRN-00-STACK-DECISION.md)
- [Host boundaries](https://github.com/yiwssx/rcat-radio-network/blob/main/docs/RRN-01-HOST-BOUNDARIES.md)
- [Official LibreTime 4.5.0 Compose](https://github.com/libretime/libretime/blob/4.5.0/docker-compose.yml)
- [Official LibreTime 4.5.0 config](https://github.com/libretime/libretime/blob/4.5.0/docker/config.template.yml)
- [Official Icecast homepage](https://icecast.org/)

## Work sequence

1. Reuse existing research; do not reopen RRN-00 simply to add an unnecessary licensing or SHOUTcast compatibility study.
2. Complete **RRN-01** current-host resource/port/Compose-version check **once** immediately before an approved runtime change.
3. Use the existing pinned LibreTime deployment and internal output to **`icecast:8000`**; never add a second streaming process.
4. Only **RRN-02/03/04** can establish observed playback, playlist and Live DJ fallback success. Documentation is not a runtime test.
5. Keep web/admin/input ports private until listener/public HTTPS and access paths are separately authorized.
6. Avoid creating custom applications, a dedicated backend, unnecessary monitoring, extra tests or new Issues when an existing work item suffices.

## Guardrails

- One station; web uploads, playlists, AutoDJ, authenticated Live DJ, and simple listener access.
- Keep source credentials, application secrets and recordings with private access; never in Git.
- Do not impact PDF HUB or AnyFlip; no Docker Engine restarts, global pruning, host OS upgrades, DNS/ingress changes or Production launch without explicit approval.
- No account signups, purchases, public launch or software deployment as a consequence of reading this skill.
- All GitHub content remains English-only.
