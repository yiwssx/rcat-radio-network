# Listener icon sources, copyright and trademark notes

Scope: RCAT Radio Network listener web frontend, Issue #22 / PR #25. Updated 2026-11-14.

**No hand-drawn or AI-generated icon artwork is used by the Svelte page.** SVG vector path geometry has been copied from the following upstream icon projects, with only root `class`, `focusable` and `aria-hidden` attributes added for layout/accessibility. Colors and size come from CSS. No new runtime CDN, icon package, Node service or Docker service is used.

## Lucide — functional icons

- Upstream: https://github.com/lucide-icons/lucide/tree/0.468.0/icons
- Source tag: **0.468.0**
- License: [ISC, with Feather-derived MIT icons](https://lucide.dev/license)
- Reason: consistent source-owned symbols for station, player, volume, homepage, radio, shortcuts and footer.

| Icon filename | Git blob SHA at tag 0.468.0 |
|---|---|
| [`icons/house.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/house.svg) | `8bf34bdc8dc48c3f9b557b3caeb3edb064bffba6` |
| [`icons/radio.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/radio.svg) | `526838d5d3c01de6c794b524c075d8f48702bfd1` |
| [`icons/radio-receiver.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/radio-receiver.svg) | `66322e8841e41e45a8ff931ba432a1e7f87db0cc` |
| [`icons/radio-tower.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/radio-tower.svg) | `ed2a2dfef5477a4a5b0ddea2919950d2ebed4490` |
| [`icons/audio-lines.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/audio-lines.svg) | `bb80d6e56f9bcf32695ee6eca79a870b8fea5e0c` |
| [`icons/headphones.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/headphones.svg) | `4cee5b50ab8d19e0136b97646db9b017c55775d7` |
| [`icons/megaphone.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/megaphone.svg) | `ee830432a47a0e7a43cfeb58537907677e3194a1` |
| [`icons/music.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/music.svg) | `dd9faacabe2469e6127170a2b058e1a114d0d362` |
| [`icons/users-round.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/users-round.svg) | `60fa609a596063094aa7e34eacb16d51613f2b68` |
| [`icons/play.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/play.svg) | `5bd511c14a4890c5f9ae630ce4c21508bc917f38` |
| [`icons/pause.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/pause.svg) | `9b8c5009a15850d81204da33cf94434c1fa6ee1f` |
| [`icons/volume-1.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/volume-1.svg) | `65e6a6656ef6a95935ee66a84f5d872dde95cc7f` |
| [`icons/volume-2.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/volume-2.svg) | `519e6cbd4d2693a38f7db0e396354cc07b9f4e26` |
| [`icons/globe.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/globe.svg) | `53c80ee35dd294b0193642f0731010e033ba0618` |
| [`icons/menu.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/menu.svg) | `c68f00db909e51cd878299755d0884b1b202fdb4` |
| [`icons/x.svg`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/x.svg) | `e31794349d3eecea1b3ae8e974b68bb8f4becda7` |

| [\`icons/circle-play.svg\`](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/circle-play.svg) | \`f814cfd9a8b1e685df0895d20863970c22733406\` |

The Lucide license notice from this exact tag is preserved below:

```text
ISC License

Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```

Check the [upstream Lucide license page](https://lucide.dev/license) for the full Feather-derived MIT license notice where applicable.

## Social links — source-licensed generic icons, not brand logos

We investigated [Simple Icons](https://simpleicons.org/) for Facebook, YouTube and TikTok. **No social trademark/logo artwork from Simple Icons is included in the listener.** Although the Simple Icons project distributes its own work under CC0, that does not clear third-party trademark restrictions. Source disclaimer: https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md

Instead, existing social account links use *generic Lucide* pictograms with explicit accessible labels and link destinations. This avoids implying that a copied social brand logo was licensed:

| Link | Generic sourced Lucide icon |
|---|---|
| Facebook | `users-round` |
| YouTube | `circle-play` |
| TikTok | `music` |
| College website | `globe` |

For background on the decision:
- [Meta Facebook brand-resource rules](https://www.meta.com/brand/resources/facebook/logo/) state that its official approved logo pack must be used, and downloading logos from elsewhere is not acceptable.
- [TikTok for Developers brand rules](https://developers.tiktok.com/docs/en/getting-started-design-guidelines) restrict unapproved use of TikTok marks.

These social-link names describe destinations; no company endorsement or partnership is claimed. Future use of official social logos requires prior review of applicable permission and original approved assets.

## Institution mark

The header uses the real image URL published by the college: https://www.rcat.ac.th/rcat-logo-128.png . It is not generated or manually reconstructed. The station name itself is typeset text; Lucide radio symbols do not purport to be the college's official station logo.

## Update rule

For any future icon, obtain SVG artwork from a known licensed upstream library or appropriate official brand source, record the exact source version/blob SHA and rights. Do not hand-draw or generate replacement SVG geometry.
