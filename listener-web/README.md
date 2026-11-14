# RCAT Radio Network — Listening Frontend

Issue #22 only: a responsive, public, single-station listening UI using **Svelte 5 + TypeScript + Vite + Tailwind CSS**.

- Existing stream: `https://radio.rcat.ac.th:8600/main.mp3`
- Static output: `npm run build` → `dist/`
- Intended existing production destination (requires **separate operator approval**): RMS Apache `/var/www/radio-listener/`
- No Node runtime, new container, proxy change, auth, backend, API integration, or LibreTime/Icecast configuration change.

## Local use

For a normal local development session, run `npm install` (or `npm ci` after the lockfile is committed), then `npm run dev`. For the release gate, use the command below to run the typecheck and production build together. Do not execute the original `scripts/rrn05-publish-listener-rms.sh` first-install script on an existing listener webroot.

The **hero currently uses a local reference illustration adapted from the owner-selected design**, not a verified campus photograph. The page falls back to a styled green background if unavailable. Do not misrepresent this illustration as an authenticated photo of the campus. **The college emblem is the exact, unmodified owner-supplied `RCAT.png`** stored locally at `public/images/RCAT.png` and served from `/images/RCAT.png`, with no external image URL or generated/reconstructed logo.

Playback state starts neutral and changes only on audio events. Song metadata, music schedules, social feeds, and other UI mockup cards are intentionally not implemented.

## One-command build and release-candidate preparation

From an **isolated working checkout** on a trusted machine with network access to npm and Node.js **20.19+ / 22.12+ / 24+**:

```bash
cd listener-web
bash scripts/prepare-static-release.sh
```

The script (1) verifies the owner-supplied college logo by original SHA-256, (2) installs dependencies, (3) runs `npm run check`, (4) runs `npm run build`, (5) checks the output and copied logo checksum, then (6) creates:

- `listener-web/artifacts/rrn22-listener-dist.tar.gz` — static **release candidate only**
- `listener-web/artifacts/rrn22-listener-dist.tar.gz.sha256` — checksum

It **never** touches RMS/Production, Docker, DNS, Apache, Icecast or LibreTime. If any step fails, stop and report the exact failure. No release should be claimed to have passed without a successful **real** run of that script.

There is **no committed npm lockfile yet** because npm Registry was inaccessible from the ChatGPT test container. On the first real `npm install`, inspect and commit the resulting `package-lock.json` to this same PR for reproducible subsequent `npm ci` builds. Do not invent a lockfile. The script accepts an existing lockfile and uses `npm ci` automatically.

Before approving a live release, launch the locally compiled preview with `npm run preview` and perform one targeted **actual browser** acceptance: desktop and phone layout, Thai labels, menu open/close, announcement and contact links, all four Social links, schedule/activity messages, play/pause and audio status (including a real connected stream test), and browser console errors. An earlier static HTML/CSS screenshot **does not replace** this compiled-app check.

The hero is currently an owner-approved **design-reference illustration**, not an authentic college photograph. Obtain owner sign-off for public use of that specific asset or replace it with an authorized real campus image without inventing college signage. Social-brand logo usage must also satisfy each platform's branding requirements (see `ICON-SOURCES.md`).

## Release scope (operator-only)

Preserve the current static webroot contents first, copy **only** the reviewed `dist/` contents into that same webroot, and verify page UTF-8, mobile layout and one player interaction. No Apache reload needed when only static files change. A rollback restores the preserved webroot files; never touch Icecast/LibreTime or shared vhosts.

## Owner reference fidelity — source revision (2026-11-13)

This source revision uses the **exact owner-selected green Thai-radio screenshot** as the visual reference for desktop and mobile layout. Core HTML/Svelte controls remain interactive: no image of the whole webpage is used in place of a frontend. The hero background remains **adapted from the owner-provided AI mockup** for visual comparison and is not authenticated campus photography. The college crest, by contrast, is now **the exact PNG file provided by the owner**, committed without generation or editing. The hero background still requires a rights-cleared actual college photograph before public release. The current design is not claimed as a 100% pixel-identical match across devices and font stacks.

The schedule and station-activity tiles open truthful "not yet published" messages; they do not invent separate pages or event feeds. News/contact/social links use known existing college destinations. Stream playback uses HTMLAudioElement with user-initiated play, real playing/waiting/error events, and no fictitious LIVE success state. No metadata / Now Playing feature was added.

Reference-size Chromium **HTML/CSS presentation previews**, rather than compiled Svelte captures, were produced at 1208×864 and 319×864 (the two panels of the owner-supplied reference), plus 1440×900 and 390×844 for responsive checks. These do not establish a successful Svelte/Vite build; no dependency installation or radio playback validation is implied.