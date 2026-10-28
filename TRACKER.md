# RCAT Radio Network — Project Tracker
Parent issue: [#2](https://github.com/yiwssx/rcat-radio-network/issues/2). Implementation PR: [#1](https://github.com/yiwssx/rcat-radio-network/pull/1). Updated: 2026-10-28. Status: repository code prepared for CI validation; **not deployed**.

| ID | Scope | Status | Acceptance gate |
|---|---|---|---|
| [RRN-00](https://github.com/yiwssx/rcat-radio-network/issues/3) | Inventory existing Docker host, resource/ports and existing service baseline | PENDING HOST AUDIT | Sanitized inventory + full private evidence + operator sign-off |
| [RRN-01](https://github.com/yiwssx/rcat-radio-network/issues/4) | Architecture and threat model approval | READY FOR REVIEW | Isolated network, permissions and LAN-only policy approved |
| [RRN-02](https://github.com/yiwssx/rcat-radio-network/issues/5) | Stage AzuraCast release, inspect generated Compose | BLOCKED by RRN-00/01 | No collision, unintended exposure or unreviewed privilege |
| [RRN-03](https://github.com/yiwssx/rcat-radio-network/issues/6) | Controlled AzuraCast installation on approved runtime | BLOCKED | Engine healthy, existing stacks unchanged |
| [RRN-04](https://github.com/yiwssx/rcat-radio-network/issues/7) | Live DJ / AutoDJ / schedule / fallback | BLOCKED | Switching and fallback tests pass |
| [RRN-05](https://github.com/yiwssx/rcat-radio-network/issues/8) | Listener portal, Now Playing API, mobile compatibility | BLOCKED | Cross-browser listening works |
| [RRN-06](https://github.com/yiwssx/rcat-radio-network/issues/9) | Monitoring, backup and isolated restore | BLOCKED | Stream observability and recovery evidence |
| [RRN-07](https://github.com/yiwssx/rcat-radio-network/issues/10) | Integration, security, capacity and regression testing | BLOCKED | Critical acceptance tests pass |
| [RRN-08](https://github.com/yiwssx/rcat-radio-network/issues/11) | LAN pilot and operational sign-off | BLOCKED | Approved pilot handover |

## RRN-00 checklist

- [x] Dedicated GitHub repository identified
- [x] Read-only preflight script provided in repository
- [x] Compose review checker provided in repository
- [x] Baseline command guidance and test plan documented
- [ ] Read-only audit run on **actual RCAT host**
- [ ] Verify CPU, available RAM, disk, network capacity and Docker Engine version
- [ ] Verify all listening and published host ports, including IPv6
- [ ] Confirm existing PDF HUB and AnyFlip actual health URLs and workflows
- [ ] Verify backup and restoration readiness for existing systems
- [ ] Review AzuraCast generated Compose privilege and network behavior
- [ ] Approve/reject shared-host installation

## Stop/go

**STOP** if Docker or port inventory is inaccessible, host capacity is insufficient,
a protected existing service port is reused, admin/listener ports are exposed publicly,
or AzuraCast requires unreviewed privileged access.

Do not run host-wide prune, change existing reverse proxy configuration or deploy
before RRN-00 and RRN-01 are approved. Sensitive reports must not be published
in this public repository.

## Single-session pilot package (prepared, not run on RCAT server)

- Source: `deployment/compose.pilot.yaml` (AzuraCast stable + Nginx portal).
- Operator guide: [Run once](docs/RUN-ONCE.md).
- Deprecated: Python-based `--mode deploy` is disabled. Use the reviewed Docker-only workflow after written approvals.
- Web admin binds 127.0.0.1:8700 (SSH tunnel only); portal binds LAN:8750.
- Docker/socket updater omitted. No installation or host firewall work performed remotely.
- Scope: RRN-02 static artifacts **prepared**; RRN-03 installation **not yet executed**;
  RT-03–RT-17 need actual host and human/audio evidence.
- GitHub tests are non-deployment static tests and must not be described as end-to-end success.


## Docker-only operator workflow — ready for real-host audit

- Primary operator entrypoint after approvals: `bash scripts/radioctl.sh deploy <SERVER_LAN_IP> --ack-shared-host`
- No Python interpreter on the host; Compose JSON audit runs in disposable
  isolated `python:3.12-alpine` service (no Docker socket/network)
- Interactive station creation and real audio/DJ testing still manual
- GitHub CI tests validate Bash syntax and effective Compose; they do **not**
  certify real-host installation or production readiness.
- RRN-00/01/02 remain open until actual host and Compose evidence is accepted.
- Runbook: `docs/DOCKER-ONLY.md`.

## RRN-05/07 follow-up: player and live regression hardening

- Changed player to consume exactly `/api/nowplaying/rcat_radio`,
  preventing another station from masquerading as the on-air RCAT station.
- Browser stream uses an allowlisted same-origin URL through Nginx
  (`/listen/rcat_radio/`) rather than reusing a possibly incorrect mount
  path on Icecast port 8600.
- Installation-time RAM gate is no longer applied when verifying
  an already running station.
- Actual pre-install PDF HUB/AnyFlip HTTP statuses persist privately
  and must match later verification.
- Nginx syntax and Node URL resolver tests run in GitHub CI.
- **No live host verification has been completed.** RRN-00 through 08
  must remain open until host-specific acceptance evidence is available.

## RRN-06: Operational recovery prepared

- [x] Draft safe backup and isolated restore runbook (`docs/BACKUP-RESTORE.md`)
- [x] Describe radio-only incident stop and verification of PDF HUB/AnyFlip
- [ ] Verify off-host AzuraCast backup is actually generated
- [ ] Verify isolated restore and capture evidence (RT-14)
- [ ] Enable and test silence/stream-down monitoring and alert delivery
- [ ] Confirm retention, escalation owner and restore acceptance

**RRN-06 stays OPEN** until these actual operational gates have passed.


## 2026-10-28: predeployment gate and portal-regression hardening (PR #15 merged)

- [x] Inspect merged PRs #1, #12, #13 and #14 and verify all were merged.
- [x] Prepare explicit `--ack-shared-host` plus **private, owner-only**
  RRN-00/01/02 approval-file gate; fail before Docker actions.
- [x] Disable alternate legacy Python deployment path that lacked the gate.
- [x] Restrict the portal Now Playing proxy to `/api/nowplaying/rcat_radio`.
- [x] Align the smoke stream request with the listener-proxy default mount.
- [x] Add CI regression checks for missing consent, legacy bypass and API scope.
- [x] GitHub Actions successful (**unit-tests** and **compose-static**); PR [#15](https://github.com/yiwssx/rcat-radio-network/pull/15) merged to `main` (commit `ba1b556b`).
- [ ] Obtain actual server baseline, documented owner approvals and full
  RRN-02 Compose/upstream image review **before** attempting radio deployment.

**No real-host deployment, 24-hour soak, DJ tests or restore evidence yet.**
All RRN-00 through RRN-08 acceptance issues remain **OPEN**.

## Code-completion batch — 2026-10-28

See [docs/CODE-READY.md](docs/CODE-READY.md). This batch prepares:
- [x] Opt-in read-only audio decoding / silence and disconnection monitor
- [x] Optional HTTPS webhook alerting, disabled unless owner configures it
- [x] 5/20/50 bounded client HTTP load and timed soak sampling utility
- [x] Offline backup checksum / ZIP CRC manifest verifier (no extraction)
- [x] Accessible player playback recovery and listener metadata
- [x] Nginx API allowlist and same-origin media CSP hardening
- [x] CI mock-backed proxy integration and optional monitor image build checks
- [x] Offline tests for the new code paths
- [ ] Real host deployment/configuration and upstream-version review (owner)
- [ ] Real streaming/Live DJ/AutoDJ/silence/multi-browser tests (owner)
- [ ] Off-host backup and isolated restore evidence (owner)
- [ ] Network, PDF HUB/AnyFlip functional regression and signed acceptance (owner)

**Code implementation does not equal operational acceptance.** RRN-00…08
remain open until actual host evidence and the dependency gates are met.
