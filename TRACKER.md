# RCAT Radio Network — Project Tracker
Updated: 2026-10-28. Status: planning and safe preflight preparation, **not deployed**.

| ID | Scope | Status | Acceptance gate |
|---|---|---|---|
| RRN-00 | Inventory existing Docker host, resource/ports and existing service baseline | PENDING HOST AUDIT | Sanitized inventory + full private evidence + operator sign-off |
| RRN-01 | Architecture and threat model approval | READY FOR REVIEW | Isolated network, permissions and LAN-only policy approved |
| RRN-02 | Stage AzuraCast release, inspect generated Compose | BLOCKED by RRN-00/01 | No collision, unintended exposure or unreviewed privilege |
| RRN-03 | Controlled AzuraCast installation on approved runtime | BLOCKED | Engine healthy, existing stacks unchanged |
| RRN-04 | Live DJ / AutoDJ / schedule / fallback | BLOCKED | Switching and fallback tests pass |
| RRN-05 | Listener portal, Now Playing API, mobile compatibility | BLOCKED | Cross-browser listening works |
| RRN-06 | Monitoring, backup and isolated restore | BLOCKED | Stream observability and recovery evidence |
| RRN-07 | Integration, security, capacity and regression testing | BLOCKED | Critical acceptance tests pass |
| RRN-08 | LAN pilot and operational sign-off | BLOCKED | Approved pilot handover |

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
