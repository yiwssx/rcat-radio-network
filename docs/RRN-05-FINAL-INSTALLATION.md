# RRN-05 — One-pass final installation (not UAT)

## Accepted evidence: do not repeat
- RMS CentOS 7 Apache Radio certificate chain repaired; radio.rcat.ac.th public HTTPS 403, SSL_VERIFY=0 from outside.
- IOT Ubuntu 26, LibreTime 4.5.0 and Icecast 2.4.4; admin LAN http://10.10.1.100:8700 login works; Icecast LAN HTTP 8600 works; Live DJ private handoff previously accepted.
- IOT Icecast has one HTTP socket 8000, no TLS, no persistent config mount; 8443 unused at the observation time.
- Certificate lives on RMS; WAN MikroTik 8443 forwarding and WAN 8605/8700 isolation were not applied by this repo.
- Rights to every publicly played track and default admin password rotation remain a separate owner/operator responsibility.

## Target
RMS Radio vhost 443 serves a small static HTML5 audio player ONLY.
IOT bundled Icecast retains HTTP port 8000/host LAN 8600 and adds native HTTPS 8443 with own mounted XML and PEM bundle.
WAN public 8443 routes directly to IOT; WAN Admin 8700 and Show DJ 8605 are blocked by router; LAN/VPN remain accessible.
No streaming HTTP reverse proxy; no new application; no Docker Engine upgrade or non-radio vhost changes.

**Important residual risk:** native Icecast HTTPS on 8443 shares its TLS socket with Icecast's own authenticated /admin URLs. This architecture prevents public access to *LibreTime Admin* and the *Live DJ harbor* via WAN 8700/8605, but does NOT technically block Icecast's own admin URL on :8443. Strong unique Icecast admin/source credentials are mandatory. Do not describe :8443 as a path-isolated listener-only proxy.

## Production installation sequence (not repeated trial checks)

1. Operator: approve publishing only licensed/authorized content; ensure unique non-default LibreTime admin and source passwords; correct MikroTik firewall/NAT. Permit WAN 8443 TCP -> 10.10.1.100:8443, block WAN 8605 and 8700, and preferably block unnecessary WAN 8600. Safeguard existing RCAT services and LAN/VPN. MikroTik changes cannot be performed through GitHub.

2. RMS to IOT: privately transfer a combined radio PEM bundle containing fullchain.pem followed by privkey.pem, using authenticated SSH/SCP. Do NOT paste certificate private keys into chat, GitHub, URLs, scripts, or shell history. Provision on IOT at /etc/rcat-radio-network/icecast-bundle.pem, root-owned mode 0600, with the parent directory root-only mode 0700. This one-time bootstrap needs authorized access to BOTH servers.

3. IOT: get the release-commit-pinned scripts/rrn05-install-icecast-tls.py and invoke ONE command:
    sudo python3 rrn05-install-icecast-tls.py --apply
This checks required dependencies within the deployment transaction, backs up original radio override and Icecast XML, applies only Icecast persistent mounts and 8443 listener, recreates Icecast only, checks the TLS socket, and attempts radio-only rollback on failure.
Expected status: RRN05_ICECAST_TLS=INSTALLED.

4. IOT automatic renewal receiver:
  - Install scripts/rrn05-cert-receiver-iot.sh as /usr/local/sbin/rrn05-cert-receiver-iot.sh (root owned, 0755).
  - Install scripts/rrn05-rotate-icecast-cert.py as /usr/local/sbin/rrn05-rotate-icecast-cert.py (root owned, 0755).
  - Add one exact sudoers rule (validate using visudo -cf): rcat_iot_admin ALL=(root) NOPASSWD: /usr/bin/python3 /usr/local/sbin/rrn05-rotate-icecast-cert.py --apply
  - RMS root creates a dedicated ED25519 key under /root/.ssh/rrn05-radio-cert-ed25519 (mode 0600), then the operator installs its public key in rcat_iot_admin SSH authorized_keys with the forced-command restriction:
    from="10.10.2.100",restrict,command="/usr/local/sbin/rrn05-cert-receiver-iot.sh" ssh-ed25519 [REAL PUBLIC KEY]
  - The operator verifies the IOT SSH server fingerprint using an independent trusted channel and pins it in RMS /root/.ssh/known_hosts. Never use StrictHostKeyChecking=no.

5. RMS automatic renewal:
  - Install scripts/rrn05-certbot-deploy-hook-rms.sh as /etc/letsencrypt/renewal-hooks/deploy/rrn05-certbot-deploy-hook-rms.sh (root owned, 0755).
  - After IOT TLS installation and restricted SSH bootstrap, perform one initial sync via:
    sudo env RRN05_FORCE=1 bash /etc/letsencrypt/renewal-hooks/deploy/rrn05-certbot-deploy-hook-rms.sh
  - Existing certbot renew cron automatically triggers the deploy hook when the Radio certificate is actually renewed. The hook filters by exact Radio certificate lineage and changes no other domain. The IOT receiver refreshes only Icecast and reverts its old bundle on failed TLS acceptance.
Expected status: RRN05_CERT_PUSH=APPLIED_BY_IOT_RECEIVER.

6. RMS listener publication, AFTER permitted WAN NAT and rights:
    sudo bash rrn05-publish-listener-rms.sh --apply --wan-and-rights-approved
Changes only /etc/httpd/conf.d/radio-ssl.conf and creates /var/www/radio-listener/index.html; saves existing Radio vhost, runs Apache syntax validation, graceful reload, trusted HTTPS local acceptance and rollback if needed.
Expected status: RRN05_RMS_LISTENER=INSTALLED.

## Actual completion boundaries
Source publication or merging a PR does not equal server execution. The user/operator must report Host-side success AND apply router ACL/NAT. Do not close RRN-05 without proof that WAN Admin/DJ isolation exists, certificate transport and automatic renewal work, and public listener page and trusted stream are actually reachable from outside.

Runtime install acceptance (TLS handshake, Apache syntax/HTTP) is included in each one-pass apply action; *no extra trial playlist, DJ handoff, music tests, broad audits, or repeated host checks* are required as part of installation.

## Rollback
Both install commands preserve copies of radio-owned configuration and attempt scoped rollback; no command uses docker compose down -v or prunes volumes. MikroTik changes have a separate saved router configuration and rollback under the network operator. As with any live deployment, rollback command success is not proof of uninterrupted service.
