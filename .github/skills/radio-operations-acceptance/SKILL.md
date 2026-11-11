---
name: radio-operations-acceptance
description: Create concise operating procedures and perform evidence-based acceptance for a one-station SHOUTcast DNAS plus ready-made AutoDJ system. Use for DJ setup, playlists, listener playback, backup/restore, launch checks, and incident recovery.
---

# RCAT Radio Operations and Acceptance

## Goal

Get a single off-the-shelf internet radio station usable and maintainable without adding a custom operations platform or repetitive acceptance gates.

## Read first

- Main plan: GitHub issue #1.
- AutoDJ uploads and playlists: #5 (RRN-03).
- Live DJ and automatic return to AutoDJ: #6 (RRN-04).
- Public player, TLS, and access controls: #7 (RRN-05).
- Backup, SOP, and sign-off: #8 (RRN-06).
- Current vendor manual for the product **actually selected** in RRN-00 (#2).

## Minimal operational workflows

### Administrator
Document login, upload/delete music, create/select a playlist, start/stop AutoDJ, and identify an offline station. Production library begins empty. Use only appropriately licensed audio for testing or public transmission.

### Live DJ
Document a standard encoder such as BUTT or Mixxx, connection settings without exposed secrets, on-air status, disconnect behavior, and the vendor-supported fallback to AutoDJ. Do not invent automatic fallback support if the selected product lacks it.

### Listener
Use the selected product's built-in player or a minimal static page. Validate audible playback on a desktop browser and a mobile browser, with no administration credentials exposed publicly.

### Backup and recovery
Document which files, metadata, credentials, and configurations must be preserved. Use supported vendor backup and restore procedures, a safe storage location, and a proportionate non-disruptive recovery check. Do not make new backup infrastructure a prerequisite unless the selected platform requires it.

## One-pass acceptance

Record evidence once for:
- AutoDJ audio is audible to a listener.
- Live DJ audio is audible, and return to AutoDJ works upon disconnect.
- Public listener page and secure administrator access work as configured.
- Existing PDF HUB and AnyFlip remain healthy after the specific radio change.
- The owner approves the actual public launch and has verified music/broadcast rights.

A successful HTTP status without audio is not evidence that a radio stream is audible. Conversely, do not demand a 24-hour soak or unrelated full test matrix by default.

## Scope management

- Avoid new features, complex scheduling, bespoke monitoring, and unnecessary tickets.
- If a documented requirement is unavailable in the selected ready-made product, surface one decision under the existing issue rather than building a custom substitute.
- Keep artifacts and issue updates in English.
- Never deploy or change Production without separate explicit approval.
