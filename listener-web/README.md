# RCAT Radio Network — Listening Frontend

Issue #22 only: a responsive, public, single-station listening UI using **Svelte 5 + TypeScript + Vite + Tailwind CSS**.

- Existing stream: `https://radio.rcat.ac.th:8600/main.mp3`
- Static output: `npm run build` → `dist/`
- Intended existing production destination (requires **separate operator approval**): RMS Apache `/var/www/radio-listener/`
- No Node runtime, new container, proxy change, auth, backend, API integration, or LibreTime/Icecast configuration change.

## Local use

Run `npm install` (or `npm ci` once a reviewed lockfile is committed), then `npm run check`, `npm run dev`, and `npm run build`. Do not execute the original `scripts/rrn05-publish-listener-rms.sh` first-install script on an existing listener webroot.

The hero URL is an **official-site-owned RCAT image endpoint candidate**, not a verified photograph of a specific campus building. The page falls back to a styled green background if unavailable. The header uses an official college emblem URL with a textual fallback. Replace these only with operator-verified institutional assets before live release if needed.

Playback state starts neutral and changes only on audio events. The green Thai-radio design approved by the owner is reflected in the hero, custom player and four visual shortcut tiles. The schedule tile is explicitly unavailable (no fabricated schedule); the news, college activity and contact tiles use existing institutional destinations. Social buttons link to the college's existing official profiles. Now Playing, metadata APIs, new station program pages and feeds are not implemented.

## Evidence and design boundary

The approved green Thai-radio concept is a **visual reference**, not proof that an AI-rendered campus background is an actual campus photo. The source uses a college-owned image endpoint candidate rather than shipping generated signage; confirm that image and branding with the operator before a live release. Screenshots supplied in ChatGPT were rendered from an offline HTML/CSS preview reflecting the revised layout, **not** a compiled Svelte bundle or running broadcast service. The npm registry was unavailable in that environment, so `npm run check` and `npm run build` remain pending: do not mark these checks as passed.

## Release scope (operator-only)

Preserve the current static webroot contents first, copy **only** the reviewed `dist/` contents into that same webroot, and verify page UTF-8, mobile layout and one player interaction. No Apache reload needed when only static files change. A rollback restores the preserved webroot files; never touch Icecast/LibreTime or shared vhosts.
