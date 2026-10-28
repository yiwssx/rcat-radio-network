# Acceptance tests

| ID | Test | Pass condition |
|---|---|---|
| RT-01 | Docker isolation | Existing Compose stacks unchanged |
| RT-02 | Network/ports | No collisions or unintended publication |
| RT-03 | AutoDJ | Continuous real audio for 30 minutes |
| RT-04 | Scheduler | Playlist transitions according to configured schedule |
| RT-05 | Live DJ | Authenticated DJ connects with audible source |
| RT-06 | DJ disconnect | AutoDJ returns, measurable transition |
| RT-07 | Fallback | No prolonged silence, investigate >10 seconds |
| RT-08 | Clients | Chrome/Firefox/Android/iOS Safari play |
| RT-09 | Metadata | Now Playing aligns with audio |
| RT-10 | Authorization | Non-admin cannot reach admin controls |
| RT-11 | Network access | Only approved LAN scope reachable |
| RT-12 | Load | 5/20/50 simultaneous listeners; no severe host contention |
| RT-13 | Endurance | 24h stream soak without severe faults |
| RT-14 | Backup | Restore succeeds in isolated target |
| RT-15 | PDF HUB | Health + representative conversion regression |
| RT-16 | AnyFlip | Health + representative download regression |
| RT-17 | Rollback | Stop radio alone; other stacks remain healthy |

Record for each test: date, version, expected vs actual, evidence and
sanitized logs. Initial resource goals: CPU under 75% sustained, host RAM
under 80% in target peak, disk at least 20% available; adjust with baseline.
