# RCAT Radio Network — Listening Frontend

Issue #22 only: a responsive, public, single-station listening UI using **Svelte 5 + TypeScript + Vite + Tailwind CSS**.

- Existing stream: `https://radio.rcat.ac.th:8600/main.mp3`
- Static output: `npm run build` → `dist/`
- Intended existing production destination (requires **separate operator approval**): RMS Apache `/var/www/radio-listener/`
- No Node runtime, new container, proxy change, authentication, backend service, or LibreTime/Icecast configuration change. A small optional **public read-only** client-side metadata integration is described below.

## Automatic Release Candidate (no workstation required)

**Owner-approved change on 2026-11-14:** GitHub Actions now performs the same isolated check/build/package sequence on updates to the current PR #25. This explicitly requested automation is an exception to the older rule against adding CI *merely to generate evidence*; it is used here to eliminate repeated manual builds after the owner moved computers.

Workflow: [`.github/workflows/rrn22-listener-candidate.yml`](../.github/workflows/rrn22-listener-candidate.yml). On updates to the PR targeting `main` and affecting `listener-web/`, it automatically:
1. Checks out the exact PR revision on a GitHub-hosted Ubuntu runner (Node 24).
2. Runs the existing `scripts/prepare-static-release.sh` unchanged: Node prerequisite; exact RCAT.png SHA-256; dependencies; `svelte-check`; 10 LibreTime parser fixtures; Vite production build; archive + SHA-256.
3. Starts `npm run preview` on localhost and verifies `index.html` and the original logo bytes over HTTP, without accessing private RCAT services.
4. Uploads `rrn22-listener-dist.tar.gz` + `.sha256` as a **GitHub Actions artifact (14 days)** with the immutable commit SHA in its name.

Workflow permissions: `contents: read`. It has no server credentials, public API keys, write token, production environment or remote deployment step. It does **not** merge the PR, change DNS/Apache/Docker/LibreTime/Icecast, open the private metadata API, or authorize public trademark/hero asset usage. If GitHub Actions is disabled or blocks this workflow, the source file alone does not prove an actual run; check the workflow run status before claiming the candidate exists.

There is no need to clone this repository or run Node/npm on the owner's current computer. The fresh-machine commands below remain only a fallback, not the primary workflow. Production still requires a **separately confirmed** radio-only deployment path with authorized host access and a safe rollback. Never silently replace the existing RMS webroot or enable GitHub remote SSH credentials from this workflow.

## Build on any new machine (no previous checkout required)

You do **not** need access to the original Windows PC, its `$HOME/rcat-radio-listener-build` directory, `node_modules`, generated `dist`, or local archive. The authoritative source is the **existing PR #25 branch on GitHub**. Work in a fresh, non-Production folder.

Prerequisites: Git, Bash, npm, and a Vite 7-supported Node.js release (Node 20.19+ or 22.12+; Node 24 LTS recommended). On Windows use **Git Bash**; on Linux/macOS use a Bash shell. Verify with `git --version`, `node --version`, and `npm --version`.

From the directory **where you want the new checkout** (the clone command creates a subdirectory):

```bash
git clone --depth 1 --single-branch \
  --branch feat/issue-22-green-listener-svelte \
  https://github.com/yiwssx/rcat-radio-network.git

cd rcat-radio-network/listener-web
bash scripts/prepare-static-release.sh
npm run preview
```

Open `http://127.0.0.1:4173/` on the new computer. If you **already cloned** this branch, run `git pull --ff-only` from that checkout instead of cloning again. **Do not use** hard-coded paths from a previous person's PC or pull/reset the historical Production checkout.

The current build gate uses `npm install` when `package-lock.json` is not committed and `npm ci` once a reviewed lockfile is committed. It runs Svelte checks, focused metadata parser checks, Vite build, and a source-faithful college-logo SHA-256 comparison. It then creates `listener-web/artifacts/rrn22-listener-dist.tar.gz` and `.sha256`, **only on the computer where it was run**. A new computer must generate its own candidate; do not claim that the old machine's archive is available locally.

The new-machine build needs **no radio server installation**. With `VITE_LIBRETIME_LIVE_INFO_URL` unset, the optional previous/current/next cards show an honest “metadata not connected” state; setting up a new computer does **not** activate a public LibreTime API or fix CORS. Only configure an independently authorized public read-only HTTPS endpoint, with no keys or internal URLs.

This local preview/build **does not deploy** the listener. Preserve the existing RMS Apache webroot and follow a separately authorized backup/cutover procedure before any Production update.

## Local use

For a normal local development session, run `npm install` (or `npm ci` after the lockfile is committed), then `npm run dev`. For the release gate, use the command below to run the typecheck and production build together. Do not execute the original `scripts/rrn05-publish-listener-rms.sh` first-install script on an existing listener webroot.

The **hero uses the newly supplied RCAT campus image** (`public/images/rcat-campus-original.webp`) as a standalone local asset: 1621×970 pixels, lossless WebP and **pixel-identical RGB** to the attached PNG. The photo, including its existing Thai slogans and institutional signage, is not re-generated or retouched. Desktop/tablet use `background-size: contain` to retain the full composition; mobile displays the photo above the radio title. The redundant previous HTML overlay was removed, with the slogan retained in a screen-reader description. There is no claim of native 4K resolution. **The college emblem is the exact, unmodified owner-supplied `RCAT.png`** stored locally at `public/images/RCAT.png` and served from `/images/RCAT.png`, with no external image URL or generated/reconstructed logo.

Playback state starts neutral and changes only on audio events. The optional song timeline reads just **previous/current/next** playout metadata when a verified public LibreTime API URL is configured; full song history, music schedules and social feeds are not implemented.

## Design System v1 — shadcn-svelte manual integration (2026-11-14)

Following owner feedback that repeated custom CSS overrides produced inconsistent layouts, this Listener now uses **actual upstream MIT-licensed shadcn-svelte Button/Card/Badge source components** under `src/lib/components/ui/` (source and hashes in `SHADCN-SOURCES.md`).

- Tokens and one consolidated responsive stylesheet: `src/app.css`; spec: `DESIGN-SYSTEM.md`.
- `components.json`, Vite/TypeScript `$lib` aliases, and `cn` + `tailwind-variants` make further official shadcn-svelte additions possible.
- This is a **manual installation** for the existing **Vite + Svelte 5 + Tailwind v4** app; the CLI was **not** run and no SvelteKit, new backend or radio service was introduced.
- Only the existing player/buttons/shortcuts were converted. The native audio/volume behavior and external URLs remain unchanged.
- **Do not run `shadcn-svelte init` indiscriminately:** it can replace the maintained `src/app.css` and negate the owner-approved theme. Review CLI output and only add needed components.

The previous Windows compiler/Build PASS applied to the old layout and **does not validate this migration**. Re-run `bash scripts/prepare-static-release.sh` once on any supported networked build machine, then perform one focused desktop/mobile visual and interactive smoke test before approving release. The local package-lock may be stale after new dependencies: the release script now refreshes untracked lockfiles using `npm install`, then uses `npm ci` after a reviewed lockfile is committed to the PR.

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

The hero uses the **new 1621×970 PNG photograph attached by the owner**, stored as pixel-identical lossless WebP. No building, sign, slogan, or background detail was reconstructed. It is not a native 4K photo. Social-brand logo usage must also satisfy each platform's branding requirements (see `ICON-SOURCES.md`).

## Previous / Now / Next metadata (owner-approved UI addition, 2026-11-14)

The `TrackTimeline.svelte` below the shortcuts uses **existing LibreTime 4.5.0 `/api/live-info-v2/` data** with the documented `tracks.previous`, `tracks.current` and `tracks.next` shape. It displays one item in each group, **not** an invented album feed or multiple-song listening history. A live DJ may supply a live-program label instead of music track titles. Inactive, empty, malformed, timed-out and unreachable endpoints show a plain unavailable state, never fictitious titles or stale songs.

The public RCAT LibreTime API endpoint **could not be reached/verified from this environment**. The new view therefore remains visible but unconfigured by default; **no credentials or internal endpoint are embedded in the client**. An operator may only set an independently authorized, publicly readable URL (prefer a pre-existing cached, same-origin HTTPS endpoint), e.g. in a local **uncommitted** environment:

```bash
# Set only to an actual operator-verified public HTTPS URL with CORS access.
# Never use your private LibreTime admin/API key or internal IP address.
export VITE_LIBRETIME_LIVE_INFO_URL='https://<approved-public-endpoint>/api/live-info-v2/'
bash scripts/prepare-static-release.sh
```

The example URL above is deliberately a placeholder, **not** a claim that RCAT already exposes this address. Leave the variable unset to avoid any metadata requests until the operator verifies an accessible, anonymous JSON response with the `tracks` schema. If the endpoint is a different origin, its CORS policy must explicitly allow the listener origin; the frontend does **not** bypass CORS or publish the private LibreTime Admin UI. **Do not open Public API / reverse proxy / firewall as an automatic side effect of this UI change.**

For an already-authorized public endpoint, the page fetches with `credentials: omit`, at most once per 90 seconds while visible, with an eight-second timeout, cancellation on unmount and no persistent storage. If LibreTime reports a live source it is labeled as a live program; no fabricated next-song data. Browser tabs not in view skip polling. At scale, prefer an approved cached static JSON source as recommended by LibreTime; do not direct unlimited public listener traffic to the admin backend.

Focused local parser test: `npm run test:live-info` (10 fixtures/assertions for AutoDJ, Live DJ, empty, invalid and long payloads). This command is included in the existing build gate, not a new CI workflow. A **new actual Svelte check/build is still required** after these changes; previous owner checks predated the metadata feature.

## Release scope (operator-only)

Preserve the current static webroot contents first, copy **only** the reviewed `dist/` contents into that same webroot, and verify page UTF-8, mobile layout and one player interaction. No Apache reload needed when only static files change. A rollback restores the preserved webroot files; never touch Icecast/LibreTime or shared vhosts.

## Owner reference fidelity — source revision (2026-11-13)

This source revision uses the **exact owner-selected green Thai-radio screenshot** as the visual reference for desktop and mobile layout. Core HTML/Svelte controls remain interactive: no image of the whole webpage is used in place of a frontend. The hero background uses the **newest owner-uploaded photograph** without cropping the asset. The slogan "เรียนฟรี หอพักฟรี อาหารฟรี มีรายได้ระหว่างเรียน" is already baked into this uploaded image; the previous duplicate visible HTML text was removed, but an accessible screen-reader description remains. The college crest, by contrast, is now **the exact PNG file provided by the owner**, committed without generation or editing. The hero photo was directly provided by the owner; confirm institutional publication rights as part of the normal production review. The current design is not claimed as a 100% pixel-identical match across devices and font stacks.

The schedule and station-activity tiles open truthful "not yet published" messages; they do not invent separate pages or event feeds. News/contact/social links use known existing college destinations. Stream playback uses HTMLAudioElement with user-initiated play, real playing/waiting/error events, and no fictitious LIVE success state. A later owner-authorized **previous/current/next** music metadata display was added in Issue #22, separately from the existing audio playback controls.

Reference-size Chromium **HTML/CSS presentation previews**, rather than compiled Svelte captures, were produced at 1208×864 and 319×864 (the two panels of the owner-supplied reference), plus 1440×900 and 390×844 for responsive checks. These do not establish a successful Svelte/Vite build; no dependency installation or radio playback validation is implied.