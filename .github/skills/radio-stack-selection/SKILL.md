---
name: radio-stack-selection
description: Evaluate and select a commercially supported or ready-made SHOUTcast DNAS plus AutoDJ/control panel stack for RCAT Radio Network. Use for product compatibility, pricing, license, operating-system support, Live DJ fallback, and vendor documentation checks before installation.
---

# RCAT Radio Stack Selection

## Objective

Choose the **smallest maintainable off-the-shelf solution** for one internet radio station. Prefer vendor-supported installation and built-in features. Do not propose a custom radio backend, frontend, stream gateway, or replacement control panel.

## Authoritative inputs

- Master tracker: GitHub issue #1.
- Product choice and compatibility: GitHub issue #2 (RRN-00).
- Shared-host deployment requirements: GitHub issue #3 (RRN-01).
- Official SHOUTcast materials: https://www.shoutcast.com/
- MediaCP system requirements: https://www.mediacp.net/doc/admin-server-manual/install/system-requirements/
- MediaCP SHOUTcast 2 integration: https://www.mediacp.net/doc/admin-server-manual/install/activate-media-plugins/shoutcast-2/
- Centova Cast system requirements: https://centova.com/en/cast/requirements

Always retrieve current official vendor documentation when making a product recommendation. Vendor requirements and prices can change; this skill is not a claim of installed compatibility.

## Decision workflow

1. Confirm the **actual** host operating-system release, architecture, resources, occupied ports, and the ability to run the product alongside existing services. Do not infer compatibility from generic claims of "Linux support".
2. Separate the components: SHOUTcast DNAS provides stream serving; AutoDJ and music upload/playlist management require an additional compatible product or provider.
3. Compare **at most three** options using a compact table with: official OS support, SHOUTcast DNAS version support, AutoDJ uploads/playlists, Live DJ and automatic fallback, install footprint, licensing, and monthly/annual cost.
4. Check whether the vendor requires an otherwise clean server, host-level services, ports 80/443, special kernel features, privileged installers, or an unsupported Ubuntu release.
5. Require vendor evidence for automatic Live DJ-to-AutoDJ switching. Mark unverified behaviors as unverified, not supported.
6. Prefer the least complex **supported** solution. If a panel conflicts with the shared host, propose a separately hosted ready-made solution instead of forcing an unsupported installation.
7. Record the decision, sources, costs, caveats, and any approvals required in RRN-00. Do not create extra architecture workstreams.

## Non-negotiable boundaries

- One station; web music uploads, simple playlist management, standard encoder-based Live DJ, and a basic listener player.
- No FM transmitter, custom React/Fastify platform, browser DJ studio, or elaborate analytics.
- No product purchases, account creation, server deployments, or public DNS changes without explicit authorization.
- Keep all repository material in English.

## Output

A brief evidence-backed recommendation with an approved-or-blocked decision. Do not mark RRN-00 complete until compatibility and any licensing decisions have been resolved.
