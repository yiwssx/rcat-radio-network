---
name: radio-operations-acceptance
description: Document minimal operations and evidence-based acceptance of one Icecast 2.4.4 plus LibreTime 4.5.0 radio station with media uploads, AutoDJ playlists, free Live DJ encoders and safe rollback.
---

# RCAT Radio Operations and Acceptance

## Accepted stack

Use **LibreTime 4.5.0 + its bundled Icecast 2.4.4**, not a separate SHOUTcast DNAS process. One station, no incremental software-license or external hosted-radio subscription fees. No custom streaming gateway, admin app, browser DJ studio or duplicate test pipelines.

## Linked scope

- [Master tracker #1](https://github.com/yiwssx/rcat-radio-network/issues/1)
- [RRN-02 #4](https://github.com/yiwssx/rcat-radio-network/issues/4): approved isolated installation and Icecast listener stream.
- [RRN-03 #5](https://github.com/yiwssx/rcat-radio-network/issues/5): media library and playlist AutoDJ.
- [RRN-04 #6](https://github.com/yiwssx/rcat-radio-network/issues/6): Live DJ via **LibreTime Show Source** and automatic fallback.
- [RRN-05 #7](https://github.com/yiwssx/rcat-radio-network/issues/7): player, TLS, admin access and public authorization.
- [RRN-06 #8](https://github.com/yiwssx/rcat-radio-network/issues/8): backups and one-pass acceptance.

## Operator tasks

**Administrator:** sign in, upload/delete appropriately licensed audio, create and arrange playlists, schedule one program, inspect AutoDJ status, and stop/start radio-only services through supported procedures.

**DJ:** use BUTT or Mixxx to connect to LibreTime's authenticated **Show Source** (internal port 8002). Do not connect directly to Icecast, which bypasses LibreTime's intended source-switching control. Keep DJ credentials separate from admin and listener credentials.

**Listeners:** access a simple Icecast/HTML5 compatible player through a separately authorized HTTPS listener ingress. Never expose source password, Icecast admin, LibreTime admin or internal RabbitMQ/Postgres.

**Recovery:** preserve private config/secrets and all radio DB/media/playout volumes. Perform one proportional restore check without removing existing PDF HUB or AnyFlip resources.

## Single meaningful acceptance

Once authorized and running, check and record:
1. LibreTime playlist AutoDJ audio is actually audible from the Icecast listener stream.
2. Live DJ is audible; on disconnect, scheduled AutoDJ audio resumes **automatically** (with LibreTime Auto Switch On/Off configured). A documented switch setting alone does not establish acceptance.
3. Listener playback and secure admin access work through their separately authorized routes.
4. Existing PDF HUB and AnyFlip remain healthy after any radio change that could affect them; otherwise reuse accepted historical health evidence.
5. The operator accepts basic recovery procedures and holds all required public audio distribution rights before launch.

No repeat testing, 24-hour soak, unnecessary dashboards or new workstreams unless there is a specific new risk. All GitHub content is English-only. This skill authorizes no Production changes.
