# RCAT Radio Network — Listening Design System v1

**Scope:** Existing public Listener UI only, Issue #22 / PR #25. This is an application-level design system, not a universal theme for unrelated RCAT apps.

## Design principles
- **Thai institutional radio, not a music catalog or SaaS dashboard.** Preserve the approved green brand identity, college's exact uploaded `RCAT.png`, one station and recognizable play/volume controls.
- **Content-first.** The hero identifies the school/station; the player is always the primary action; the four shortcut cards reflect real destinations or clearly disclose unpublished content.
- **A small number of deliberate patterns.** One radius scale, one elevation style, and semantic surface/text/accent colors instead of accumulating page-specific overrides.
- **Progressive disclosure.** Compact header, 1 horizontal desktop layout, menu hidden on small screens, no unsupported schedules/new backend.
- **True runtime state.** Broadcast red label means the stream type is LIVE, not proof that audio is already playing. Connection/error status only follows the HTMLAudioElement.

## Technology and provenance
- Svelte 5 + Vite + TypeScript + Tailwind CSS v4 remain unchanged.
- **shadcn-svelte source components** (Button, Card, Badge) were copied from the actual upstream MIT-licensed repo with file/blob evidence in `SHADCN-SOURCES.md` and adapted using local theming. This is a **manual Vite integration**, not a claim that its CLI was run. Components live in `src/lib/components/ui`; `$lib` is resolved by Vite and TypeScript.
- Dependencies: `cn` and `tailwind-variants`; original Lucide/Bootstrap SVGs remain as previously licensed and documented in `ICON-SOURCES.md`. No other runtime service or CDN.
- Future component additions: run the current official `shadcn-svelte` CLI against `components.json`, **review any proposed CSS overwrites** and add only relevant primitives; do not `init` indiscriminately over a maintained theme.

## Semantic tokens

Defined once in `src/app.css` (Tailwind `@theme inline` maps semantic names):

| Role | Default | Purpose |
|---|---|---|
| `--background` | `#f5f8f5` | Calm neutral page |
| `--foreground` | `#192b22` | Accessible primary text |
| `--card` | `#ffffff` | Cards and navigation menu |
| `--primary` | `#08623a` | Action buttons, navigation |
| `--secondary` | `#e7f2e9` | Soft highlighted backgrounds |
| `--muted-foreground` | `#617368` | Secondary copy |
| `--ring` | `#389260` | Keyboard focus |
| `--station-deep` | `#073c2a` | Player background |
| `--station-bright` | `#addc42` | Small functional highlights |
| `--station-live` | `#de3048` | LIVE chip only |

Typography: Sarabun / Noto Sans Thai / system fallback. Title sizes use CSS `clamp`, not individually pixel-matched text. Radii: `--radius` base 14–18px, hero 25px, player 23px. Spacing: primarily 8/12/16/22/32px.

## Component map
| UI zone | Primitive | Behavior |
|---|---|---|
| Listener player | `Card` | Grid container around real browser audio UI |
| Play/Pause | `Button` | One accessible user-activated action; no autoplay/seek |
| Mobile navigation | `Button` ghost | Disclosure with `aria-expanded` and `aria-controls` |
| Shortcut cards | `Button` outline, with `href` for actual sites | Real anchors remain anchors, unavailable cards show truthful notices |
| Live/coming-soon labels | `Badge` | Semantic stable appearance |
| Volume slider | Native HTML `input[type=range]` | Uses existing event handler; no unrelated bits-ui slider dependency |

## Breakpoint acceptance
- **>=1101px:** compact horizontal navbar, image hero, five-column inline player, four shortcut cards.
- **901–1100px:** disclosure navigation; player reorganizes across two rows.
- **641–900px:** single-row branding, centered follow links and direct radio controls.
- **<=640px:** stacked two-column player, two-column shortcuts, visible social destinations.
- **<=350px:** no clipped wordmarks, volume control, horizontal scrolling or footer text.
- Keyboard: visible focus; reduced-motion mode honored. Touch controls: roughly 44px minimum.

## Song timeline — existing public LibreTime 4.5 metadata

Added after owner's request to use excessive Desktop/Tablet whitespace with useful station content. It is a **read-only UI**, not a music database or a new scheduling service. `src/lib/TrackTimeline.svelte` displays three shadcn-svelte Cards: previous, current, next; current is visually prioritized, and small screens show the current item first with an expandable history/up-next disclosure. `src/lib/live-info.js` normalizes untrusted JSON, keeps titles as escaped text, handles livestream items and rejects malformed responses.

**Public read-only URL is opt-in via `VITE_LIBRETIME_LIVE_INFO_URL`**. No default public endpoint was confirmed for RCAT; the page therefore displays a truthful unconfigured/unavailable state until an operator supplies a verified authorized HTTPS/CORS destination. Never expose the private Admin/API keys, add CORS broadening or open an internal backend as part of this UI work. Polling is 90 seconds only when visible, and error/empty states do not present fake song names. One previous + one next only; no multi-song Playout History API.

Release acceptance now additionally checks the song timeline's 3-card layout at Desktop/Tablet, 1-card+disclosure mobile, actual public data (only when the operator-authorized endpoint is available), and graceful empty/blocked behavior.

## Release boundary
The previous 2026-11-14 Windows `svelte-check: 0 errors` and Vite build PASS apply to the **earlier code**, not this new component migration. After the new sources are pulled, rebuild **once** on the networked Windows builder, correct actual diagnostics and perform one real desktop/mobile Browser + audio smoke test. Existing `scripts/prepare-static-release.sh` still creates a candidate only, never deploys. Preserve the existing Apache listener webroot and rollback path; do not modify Icecast/LibreTime.

The hero now uses the owner-attached RCAT college photograph, cropped only to omit the tiny pre-rendered caption. The exact offer text is separate accessible HTML, not AI-generated artwork. Original photo resolution 391×234 limits genuine sharpness despite the 3840px SVG canvas. Brand-logo trademark review is separate from the MIT/ISC license of SVG code.
