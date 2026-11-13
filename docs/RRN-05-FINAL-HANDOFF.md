# RRN-05 final technical handoff — certificate renewal only

## Previously accepted; never redo
- IOT LibreTime + native Icecast TLS installed and observed.
- RMS radio public listener webpage, Apache TLS Admin reverse proxy, scoped RMS firewall and IOT canonical URL accepted.
- MikroTik existing WAN 8600 -> IOT private 8443 and WAN 8700 -> RMS private 8700 **committed by operator**; 8605 remains the separately authenticated source port. No new NAT.
- Public URL https://radio.rcat.ac.th/ and stream URL https://radio.rcat.ac.th:8600/main.mp3 configured; LibreTime browser Admin rendered. The last screenshot showed no scheduled show and the stream player at 0:00; audio/playlist are operational, not install tests.
- Last user-directed technical scope = certificate renewal forwarding from existing RMS Certbot to IOT Icecast, then close RRN-05 on operator success evidence.

## What the existing three scripts do

- IOT \`scripts/rrn05-cert-receiver-iot.sh\`: dedicated forced-command SSH receiver, only from RMS SSH key, receives cert + private key via encrypted SSH stdin (never through chat/repo).
- IOT \`scripts/rrn05-rotate-icecast-cert.py\`: checks domain, certificate/key match, private on-disk backup, recreates **only Icecast** if new cert, accepts native TLS and attempts scoped rollback. If unchanged, prints \`RRN05_CERT_REFRESH=UNCHANGED\`.
- RMS \`scripts/rrn05-certbot-deploy-hook-rms.sh\`: executes only for renewed lineage \`/etc/letsencrypt/live/radio.rcat.ac.th\`, or for explicit one-time \`RRN05_FORCE=1\`. Verifies inputs, reloads Apache after config syntax validation for both 443 and 8700 certificate, sends bundle via pinned SSH host key and dedicated key to IOT. Other cert lineages exit with no change.

Important: **GitHub merging does not install certificate renewal on either host.** Complete these steps once, report host evidence, and only then close RRN-05. The operator must independently verify the IOT SSH host ED25519 fingerprint before trusting the RMS candidate. Do not paste private keys, session cookies, certificate bundles or passwords into issues/chat.

## A. On IOT as existing rcat_iot_admin with sudo

1. Install the two **pinned and verified** IOT scripts as root to:
   - \`/usr/local/sbin/rrn05-cert-receiver-iot.sh\` (0755)
   - \`/usr/local/sbin/rrn05-rotate-icecast-cert.py\` (0755)
2. Install the exact narrowly scoped sudoers line, mode 0440:
   \`rcat_iot_admin ALL=(root) NOPASSWD: /usr/bin/python3 /usr/local/sbin/rrn05-rotate-icecast-cert.py --apply\`
   Validate with \`visudo -cf\` before applying it.
3. Obtain IOT's true host key fingerprint independently on its own console:
   \`sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256\`.
   No SSH host private key should leave IOT.

## B. On RMS as root — restricted SSH bootstrap

1. \`install -d -m 700 /root/.ssh\` and generate a **new dedicated** ED25519 key at \`/root/.ssh/rrn05-radio-cert-ed25519\` if not already present (0600).
2. Use \`ssh-keyscan -T 5 -t ed25519 10.10.1.100\` to collect a *candidate* IOT SSH host public key, and inspect its SHA256 fingerprint with \`ssh-keygen -lf ... -E sha256\`.
3. Verify that fingerprint **matches** the trusted fingerprint read directly on IOT in section A. Only then pin the candidate in \`/root/.ssh/known_hosts\` on RMS (0600). Do NOT use \`StrictHostKeyChecking=no\`.
4. Add RMS's **public** key (never private key) as a new, append-only entry to \`/home/rcat_iot_admin/.ssh/authorized_keys\` (directory 0700, file 0600, owned by rcat_iot_admin), prefixed exactly:
   \`from="10.10.2.100",restrict,command="/usr/local/sbin/rrn05-cert-receiver-iot.sh" \`
   followed by the \`ssh-ed25519 AAAA...\` contents of \`/root/.ssh/rrn05-radio-cert-ed25519.pub\`.
   If the operator has an already trusted RMS→IOT interactive SSH session, a strictly append-only one-shot remote command can be used. Never replace other authorized keys.
5. Install the pinned, verified RMS hook at
   \`/etc/letsencrypt/renewal-hooks/deploy/rrn05-certbot-deploy-hook-rms.sh\` (root 0755).
6. One initial sync (only after SSH trust and sudoers bootstrap):
   \`RRN05_FORCE=1 bash /etc/letsencrypt/renewal-hooks/deploy/rrn05-certbot-deploy-hook-rms.sh\`.
   Expected:
   \`\`\`
   RRN05_RMS_HTTPD_CERT_RELOAD=PASS
   RRN05_CERT_REFRESH=UNCHANGED     # or PASS if IOT bundle differs
   RRN05_CERT_PUSH=APPLIED_BY_IOT_RECEIVER
   \`\`\`
   A new cert may briefly reconnect Icecast only; no radio-wide restart.
7. Verify the **existing** automatic Certbot renewal scheduler is enabled (systemd timer or cron). Do not add a duplicate scheduler. If none exists, stop and configure exactly one scheduler before closing RRN-05. The deploy hook only runs on successful renewal of Radio's certificate, not merely by time passing.

References: https://certbot.eff.org/docs/using.html#renewing-certificates and https://man.openbsd.org/sshd.8

## Closure boundary

When one forced sync succeeds **and** the scheduled Certbot renewal mechanism is verified, RRN-05 may be marked **CLOSED — Technical deployment complete** on operator evidence. Do NOT demand additional AutoDJ/DJ music playback, browser E2E, a new UI, or MikroTik testing.

**Subsequent actual use / operator responsibilities**, not a pretext to keep repeating deployment: schedule shows, upload authorized music, manage broadcasters and source secrets, check routine logs/expiry. Before permitting remote users or public broadcasts, the operator must privately ensure strong non-default LibreTime Admin and Icecast/Show Source passwords and rights for recordings. Native Icecast TLS still exposes authenticated Icecast /admin; source TCP 8605 is not inherently encrypted. Protect remote DJ credentials using a suitable encrypted tunnel such as a VPN, or a supported TLS source transport. These are **known security boundaries**, not acceptance claims.

RRN-06 local backup SHA verification has separately passed, but offsite retention and real restore proof remain open in RRN-06. Do not silently mark that scope completed or create duplicate RRN-05 gates for it.
