# RCAT Radio Network — Listening Frontend

Issue #22 only: a responsive, public, single-station listening UI using **Svelte 5 + TypeScript + Vite + Tailwind CSS**.

- Existing stream: `https://radio.rcat.ac.th:8600/main.mp3`
- Static output: `npm run build` → `dist/`
- Intended existing production destination (requires **separate operator approval**): RMS Apache `/var/www/radio-listener/`
- No Node runtime, new container, proxy change, auth, backend, API integration, or LibreTime/Icecast configuration change.

## Local use

Run `npm install` (or `npm ci` once a reviewed lockfile is committed), then `npm run check`, `npm run dev`, and `npm run build`. Do not execute the original `scripts/rrn05-publish-listener-rms.sh` first-install script on an existing listener webroot.

The hero URL is an **official-site-owned RCAT image endpoint candidate**, not a verified photograph of a specific campus building. The page falls back to a styled green background if unavailable. **The college emblem is the exact, unmodified owner-supplied `RCAT.png`** stored locally at `public/images/RCAT.png` and served from `/images/RCAT.png`, with no external image URL or generated/reconstructed logo.

Playback state starts neutral and changes only on audio events. Song metadata, music schedules, social feeds, and other UI mockup cards are intentionally not implemented.

## Release scope (operator-only)

Preserve the current static webroot contents first, copy **only** the reviewed `dist/` contents into that same webroot, and verify page UTF-8, mobile layout and one player interaction. No Apache reload needed when only static files change. A rollback restores the preserved webroot files; never touch Icecast/LibreTime or shared vhosts.

## Owner reference fidelity — source revision (2026-11-13)

This source revision uses the **exact owner-selected green Thai-radio screenshot** as the visual reference for desktop and mobile layout. Core HTML/Svelte controls remain interactive: no image of the whole webpage is used in place of a frontend. The hero background remains **adapted from the owner-provided AI mockup** for visual comparison and is not authenticated campus photography. The college crest, by contrast, is now **the exact PNG file provided by the owner**, committed without generation or editing. The hero background still requires a rights-cleared actual college photograph before public release. The current design is not claimed as a 100% pixel-identical match across devices and font stacks.

The schedule and station-activity tiles open truthful "not yet published" messages; they do not invent separate pages or event feeds. News/contact/social links use known existing college destinations. Stream playback uses HTMLAudioElement with user-initiated play, real playing/waiting/error events, and no fictitious LIVE success state. No metadata / Now Playing feature was added.

Reference-size Chromium **HTML/CSS presentation previews**, rather than compiled Svelte captures, were produced at 1208×864 and 319×864 (the two panels of the owner-supplied reference), plus 1440×900 and 390×844 for responsive checks. These do not establish a successful Svelte/Vite build; no dependency installation or radio playback validation is implied.