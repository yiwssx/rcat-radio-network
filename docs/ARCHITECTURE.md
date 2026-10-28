# ADR-001: Hybrid radio architecture (proposed)

## Components

- **Broadcast:** AzuraCast / Liquidsoap / Icecast; one test station initially.
- **Sources:** scheduled rights-cleared AutoDJ audio and authorized DJ live ingest.
- **Listeners:** a separate web player with read-only Now Playing API integration.
- **Runtime:** current Docker host only after manual review; LAN-only PoC first.
- **Operations:** station roles, backups, stream silence detection, metrics, rollback.

```text
Microphone/BUTT/Mixxx ----> Live DJ -----------+
                                               |
Rights-cleared audio ----> AutoDJ/Scheduler ---+--> Liquidsoap --> Icecast --> LAN listeners
                                                        |
                                                Now Playing API --> web portal
```

## Separation from existing services

Separate Docker Compose project, volumes and networks. Do not join the management
or data networks of PDF HUB/AnyFlip. Never change their port mappings or reverse
proxy in the PoC. Do not publish a public DNS record or router forward.

## Port policy (proposed, unallocated)

Existing-service protected host ports: 80, 443, 8080, 8081, 8094.
Candidate pool for review: web 8700/8743; radio 8600–8619. Only publish
the exact ports needed, bound to an approved interface/IP. **These are not
confirmed available**. AzuraCast can publish default ranges: inspect the fully
rendered Compose, not just the overlay file.

Default AzuraCast Compose may require elevated privileges; a shared host is
not approved if required privileges cannot be isolated acceptably. A small
dedicated VM may be a safer next step than weakening host isolation.

Initial audio target: MP3 128 kbps. Test 5, 20 and 50 simultaneous listeners;
measure host egress and resource contention first.
