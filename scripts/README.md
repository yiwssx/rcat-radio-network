# Read-only audit execution

On the approved Docker host:

```bash
git clone https://github.com/yiwssx/rcat-radio-network.git
cd rcat-radio-network
python3 scripts/preflight.py --output-dir reports/rrn-00
```

`shareable-summary.json` intentionally excludes hostnames, IP addresses,
container names, full Docker environment, and credentials. **Still inspect
before sharing:** it includes capacity and port usage. It writes only inside
the specified `reports/` directory and does not change services.

A clean script exit does **not** approve installation. Firewall, permissions,
system backups and existing-service functional baselines require manual review.

Stage AzuraCast Compose separately and only then run:

```bash
docker compose config --format json | python3 /path/to/rcat-radio-network/scripts/compose_audit.py
```

To permit an explicitly reviewed LAN address, run the checker with
`RRN_ALLOWED_BIND_IPS=YOUR_APPROVED_LAN_IP`. Without this setting, only
loopback addresses are accepted. This environment variable only changes the
checker allowlist and **does not** configure Docker or the firewall.

Never upload the raw Compose or Docker inspect JSON to public GitHub issues.
The Compose review prints only high-level findings.

The proposed host-port numbers are **unallocated**. Do not install,
port-forward or use host-wide cleanup scripts at this stage.
