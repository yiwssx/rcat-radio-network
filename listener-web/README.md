# RCAT Radio Network — Listening Frontend

Issue #22 only: a responsive, public, single-station listening UI using **Svelte 5 + TypeScript + Vite + Tailwind CSS**.

- Existing stream: `https://radio.rcat.ac.th:8600/main.mp3`
- Static output: `npm run build` → `dist/`
- Intended existing production destination (requires **separate operator approval**): RMS Apache `/var/www/radio-listener/`
- No Node runtime, new container, proxy change, auth, backend, API integration, or LibreTime/Icecast configuration change.

## Local use

Run `npm install` (or `npm ci` once a reviewed lockfile is committed), then `npm run check`, `npm run dev`, and `npm run build`. Do not execute the original `scripts/rrn05-publish-listener-rms.sh` first-install script on an existing listener webroot.

The hero URL is an **official-site-owned RCAT image endpoint candidate**, not a verified photograph of a specific campus building. The page falls back to a styled green background if unavailable. The header uses an official college emblem URL with a textual fallback. Replace these only with operator-verified institutional assets before live release if needed.

Playback state starts neutral and changes only on audio events. Song metadata, music schedules, social feeds, and other UI mockup cards are intentionally not implemented.

## Release scope (operator-only)

Preserve the current static webroot contents first, copy **only** the reviewed `dist/` contents into that same webroot, and verify page UTF-8, mobile layout and one player interaction. No Apache reload needed when only static files change. A rollback restores the preserved webroot files; never touch Icecast/LibreTime or shared vhosts.
