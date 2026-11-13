# RRN-05 — HTTPS access V2 (reuses existing public ports)

## Decision / scope (2026-11-13)

**Owner requirement:** listener, LibreTime Admin, and Live DJ must each be reachable from outside the campus; authentication applies to management/source, not to listening. This replaces the earlier "disable public 8700 and 8605" assumption. Do not block remote access without a working alternative.

**No changes are applied to MikroTik or RMS/IOT by this document.** In particular, prior MikroTik Safe Mode attempts on added TCP 8444 were invalid and/or rolled back; there is no accepted WAN cutover. Do not rerun the earlier 8444 NAT scripts or claim that Admin/DJ was secured by the partial attempts.

## Target access model

| Role | External entry point | Implementation | Authentication |
| --- | --- | --- | --- |
| Listener home | `https://radio.rcat.ac.th/` | Existing RMS Apache TLS 443; minimal static HTML5 player | None |
| Audio output | `https://radio.rcat.ac.th:8600/main.mp3` | **Existing, already valid** MikroTik public TCP 8600 DST-NAT entry updated to destination **IOT 10.10.1.100:8443**, where native Icecast TLS was installed and accepted | Public Icecast mount |
| LibreTime Admin | `https://radio.rcat.ac.th:8700/login` | **Existing** MikroTik public TCP 8700 DST-NAT entry redirected to **RMS 10.10.2.100:8700**, where an Apache TLS reverse proxy serves existing LibreTime web at `http://10.10.1.100:8700/` | LibreTime user login |
| Live DJ / Show Source | `radio.rcat.ac.th:8605` (native source protocol, existing mount `/show`) | **Existing, unchanged** WAN 8605 -> IOT 10.10.1.100:8605 | Independent source credentials; encrypted transport/VPN should be provided for password confidentiality |

This preserves the existing UniFi Controller WAN TCP 8443 -> 10.10.0.2:8443 and all unrelated NAT, DNS and host vhosts. No new public port numbers, DNS names, Docker services or app framework.

### Protocol boundary: must not conflate web with streaming

LibreTime's official documentation explicitly supports HTTPS reverse proxy for the **LibreTime web UI**, but warns not to reverse proxy Icecast **input/output stream protocols** or Liquidsoap harbor through an HTTP reverse proxy. The native Icecast output HTTPS socket already installed on IOT stays in use, accessed through the existing public port **8600** after editing the *existing rule*, rather than a new NAT 8444. Live DJ is a distinct raw source input, not an HTTPS web page.

Refs: https://libretime.org/docs/admin-manual/install/reverse-proxy/ and https://libretime.org/docs/admin-manual/configuration/

## Ordered one-pass host/edge cutover — preparation only

0. **Stop prior MikroTik experiments.** If Safe Mode is still active and contains *only* abandoned Radio trial changes, operator can cancel via `Ctrl+D`. If it contains other changes, review those before canceling. Confirm the existing three radio NAT entries are active, and don't rerun prior 8444 commands. Do not purge router connections or restart MikroTik.
1. **RMS prepare:** Keep its live radio.rcat.ac.th HTTPS 443 certificate/vhost in place. On RMS only, preflight that TCP 8700 isn't used, Apache has required `mod_ssl`, `mod_proxy`, `mod_proxy_http` and `mod_headers`, and IOT LAN 10.10.1.100:8700 is reachable. Stage a separate TLS Apache vhost **listening on 8700** using the **same existing radio.rcat.ac.th certificate**, reverse-proxying only the LibreTime *web* to IOT 8700. Keep unrelated Apache vhosts unchanged. Use authenticated HTTPS front-to-back if subsequently available; current private HTTP link exists within the LAN. Example config is in `config/examples/radio-admin-8700.conf.example`; adapt to actual RMS Apache configuration and validate `httpd -t` before graceful reload.
2. **IOT configuration:** The current LibreTime `general.public_url` was LAN-based. Update **only this Radio setting** to `https://radio.rcat.ac.th:8700`, with backup and affected-service restart as required by installed LibreTime deployment; preserve stream output and DJ service settings except its public stream URL metadata `https://radio.rcat.ac.th:8600/main.mp3` if needed. LibreTime requires the browser origin to match `general.public_url`; blindly proxying :8700 without setting this results in `Oops!` login failures. Respect operator's existing radio-only Compose workflow and backup.
3. **Edge switch via existing router rules only:** In a **fresh** WinBox Safe Mode transaction, modify rather than add/recreate the unique existing public `202.29.239.145:8600 -> 10.10.1.100:8600` DST-NAT rule to point to `10.10.1.100:8443`. Modify only existing public `202.29.239.145:8700 -> 10.10.1.100:8700` DST-NAT to point to `10.10.2.100:8700`. Leave `202.29.239.145:8605 -> 10.10.1.100:8605` unchanged. Check the two edited entries are **enabled and valid**, with port/target and UniFi unchanged, before Safe Mode commit. Abort via `Ctrl+D` if invalid; do not duplicate NAT. **This step requires the RMS 8700 proxy and IOT public_url already ready**, to avoid an outage.
4. **Listener page:** Only after public 8600 native HTTPS route works and broadcast rights are approved, publish the existing RMS static listener script (its source now points to `https://radio.rcat.ac.th:8600/main.mp3`). The script's existing `--wan-and-rights-approved` flag is an operator attestation, not proof of rights.
5. **Renewal:** Maintain the existing Radio cert renewal process on RMS and the Icecast TLS cert relay on IOT. The listener/Admin TLS certificate must remain valid; there is no justification for another Icecast installation.

### Apache 8700 reverse-proxy guardrails

- Do **not** copy the sample verbatim into Production without verifying RMS Apache `Listen` directives, module loading, SELinux policy, cert path/chain, and conflicts with other school vhosts. Configure an isolated `:8700` TLS vhost for `radio.rcat.ac.th`; no edits to other RMS vhosts.
- Ensure `ProxyPreserveHost On`, correct `X-Forwarded-Proto: https` and forwarded host/port, `ProxyPass` and `ProxyPassReverse`. `general.public_url` must have exact origin `https://radio.rcat.ac.th:8700`.
- LibreTime user login is still public-network reachable, not unauthenticated administration. Owner must privately confirm unique non-default Admin credentials before publishing. Consider login rate limiting and separate account privileges.
- The existing DJ TCP 8605 path remains reachable from WAN at operator's request; **TCP does not mean TLS**. Do not call this an HTTPS-protected DJ input. Secure source authentication and plan a supported encrypted transport such as a VPN for remote operators before using untrusted networks. Do not assume an Apache HTTP proxy can encrypt the Liquidsoap harbor.
- Do not expose Icecast admin credentials or files containing private keys. Native Icecast TLS 8443 carries Icecast's own password-protected `/admin` paths; a public 8600 forward does not provide path isolation.
- Check LAN client resolution/hairpin access to public domain after canonical URL migration; don't assume every campus client can reach the WAN address via NAT.

## Rollback boundaries

- On router: restore **only** the prior destination for the existing public 8600 rule (`10.10.1.100:8600`) and prior destination for existing 8700 rule (`10.10.1.100:8700`) using Safe Mode, preserving DJ 8605 and UniFi 8443. No `8444` cleanup should be needed after the failed trial sessions.
- On IOT: restore the backed-up Radio `general.public_url` and public stream metadata only.
- On RMS: disable only the new Radio Admin 8700 virtual host and restore preexisting Radio static listener config if a publication attempt fails; leave existing other Apache vhosts and certificates alone.

## Current evidence status

- IOT native Icecast TLS installed on private `10.10.1.100:8443` with owner-supplied install PASS.
- RMS radio.rcat.ac.th TLS 443 responds 403 intentionally until listener publication; cert verified previously.
- MikroTik initial audit shows valid **old public mappings** 8600, 8605, 8700; new 8444 attempts never passed.
- No evidence yet of a live RMS Apache :8700 proxy, updated IOT canonical URL, edited 8600/8700 NAT, cert-renewal automation, or public access. Avoid marking any of those done solely from this source-only update.
