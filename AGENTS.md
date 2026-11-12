# RCAT Radio Network — Agent Instructions

## Scope and authoritative state
- Deliver **one** RCAT radio station using LibreTime 4.5.0 and its **bundled Icecast 2.4.4**. Reuse the vendor's media uploads, playlists, AutoDJ and Show Source (Live DJ); do not reinvent a radio panel, streaming server, operations platform or paid service.
- Before acting, read the **current** [master tracker #1](https://github.com/yiwssx/rcat-radio-network/issues/1), the relevant existing RRN-00–RRN-06 issue (#2–#8), current branch/PRs, and the applicable `docs/RRN-00-STACK-DECISION.md` and `docs/RRN-01-HOST-BOUNDARIES.md`. Current GitHub issue evidence and operator-confirmed results supersede dated planning statements.
- Repo-local skills in `.github/skills/` are reference instructions, not running agents or evidence of host execution. Choose only the relevant skill for the requested task.

## Human-triggered, evidence-aware loop
- Work only on an explicitly requested, approved existing issue. Freeze its scope and acceptance criteria; make the smallest sufficient change. Do not add duplicate issues, trackers, orchestration, custom services, workflows, or unrelated tests.
- Reuse an earlier result only when the **specific claim, source/config version, host observation and trust boundary** still match. Recheck only affected changes or time-sensitive facts (such as occupied ports) just before an authorized host operation. Never count a paper design, checked-in script or synthetic-secret Compose render as a successful live installation or audible radio stream.
- Use existing validation scripts and real operator evidence where necessary; there is no default GitHub Actions CI in this repository. Do not create a CI workflow merely for this policy or claim a check passed when it did not run.
- Report DONE only when that issue's acceptance evidence exists. Otherwise report the precise BLOCKED / pending operator action; stop instead of cycling, retesting unrelated systems or expanding scope.

## Shared RCAT host and release boundaries
- Preserve the completed read-only host-preflight evidence in #3 and the separately authorized **radio-only** installation scope in #4. An approval does not prove deployment, and GitHub read/write access is **not** permission or technical access to execute commands on RCAT's host.
- Do not overwrite, pull/reset, inspect secrets from, or clean the historical `/opt/rcat-radio-network` checkout. If authorized to install, follow the isolated `/opt/rcat-libretime-runtime` approach and the guarded installer described in #4, with private credentials and a separate Compose project. Never use `docker compose down -v` or prune host-wide containers, images, networks or volumes.
- Do not change PDF HUB, AnyFlip, unrelated production services, shared Docker Engine, DNS, reverse proxy, firewall, public listener exposure, or privileged Admin/DJ access without a distinct explicit authorization. Do not handle unlicensed audio or publish a station solely because code or containers start.
- A source-only PR cannot satisfy actual stream playback, AutoDJ fallback, backup recovery, licensed broadcast or operator public-launch approval.
