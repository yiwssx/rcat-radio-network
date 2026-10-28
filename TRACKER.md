# RCAT Radio Network — Project Tracker
Parent issue: [#2](https://github.com/yiwssx/rcat-radio-network/issues/2). Implementation PR: [#1](https://github.com/yiwssx/rcat-radio-network/pull/1). Updated: 2026-10-28. Status: planning and safe preflight preparation, **not deployed**.

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
- Command: `python3 scripts/one_round.py --mode deploy --bind-ip <LAN_IP> --ack-shared-host`.
- Web admin binds 127.0.0.1:8700 (SSH tunnel only); portal binds LAN:8750.
- Docker/socket updater omitted. No installation or host firewall work performed remotely.
- Scope: RRN-02 static artifacts **prepared**; RRN-03 installation **not yet executed**;
  RT-03–RT-17 need actual host and human/audio evidence.
- GitHub tests are non-deployment static tests and must not be described as end-to-end success.


## Docker-only operator workflow — ready for real-host audit

- Primary operator entrypoint: `bash scripts/radioctl.sh deploy <SERVER_LAN_IP>`
- No Python interpreter on the host; Compose JSON audit runs in disposable
  isolated `python:3.12-alpine` service (no Docker socket/network)
- Interactive station creation and real audio/DJ testing still manual
- GitHub CI tests validate Bash syntax and effective Compose; they do **not**
  certify real-host installation or production readiness.
- RRN-00/01/02 remain open until actual host and Compose evidence is accepted.
- Runbook: `docs/DOCKER-ONLY.md`.
