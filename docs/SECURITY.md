# Security controls (LAN PoC)

1. **Interface scope:** no public listener/admin access or router forwarding.
   Bind permitted ports to an approved LAN interface and test routing/IPv6.
2. **TLS:** use a trusted certificate or SSH tunnel for administration; do not
   transmit admin credentials over unencrypted HTTP.
3. **Least privilege:** separate system admin, station manager and DJ accounts.
4. **Docker isolation:** avoid host networking, privileged mode, docker.sock,
   unreviewed Linux capabilities or shared production networks.
5. **Credentials:** never commit .env, tokens, passwords, raw inventories or
   rendered Compose containing environment secrets.
6. **Updates:** pin and inspect release/image digest before controlled update.
   Never let radio install scripts upgrade the host Docker Engine implicitly.
7. **Observability:** stream audio/silence monitoring, disk, CPU, host memory,
   listeners, backup success; Docker RUNNING alone is not audio health.
8. **Rights:** only test with audio whose distribution/recording rights are clear.
9. **Recovery:** external backup and isolated restore validation; no
   `docker system prune` or `docker compose down -v` in change/rollback plans.

## Deployment blockers

- Any protected existing port reused.
- New port accidentally bound to 0.0.0.0/:: or an unapproved address.
- Docker socket mounted or privileged container without assessed exception.
- Missing baseline or unverified rollback of existing applications.
- Unknown firewall/NAT behavior on the host or on upstream router.
