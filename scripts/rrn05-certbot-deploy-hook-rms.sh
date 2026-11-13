#!/usr/bin/env bash
# Certbot deploy-hook on RMS. Copies ONLY renewed Radio certificate to the
# allowlisted IOT receiver over pinned-host-key SSH. Other domains untouched.
# Bootstrap once using: RRN05_FORCE=1 bash this-script
set -Eeuo pipefail
umask 077
DOMAIN=radio.rcat.ac.th
LIVE=/etc/letsencrypt/live/radio.rcat.ac.th
KEY=/root/.ssh/rrn05-radio-cert-ed25519
KNOWN=/root/.ssh/known_hosts
IOT=rcat_iot_admin@10.10.1.100

if [[ "$(id -u)" != 0 ]]; then
  echo "RRN05_CERT_PUSH=DENIED_NON_ROOT" >&2
  exit 2
fi
if [[ "$LIVE" != "${RENEWED_LINEAGE:-}" && "${RRN05_FORCE:-0}" != 1 ]]; then
  exit 0
fi
[[ -s "$LIVE/fullchain.pem" && -s "$LIVE/privkey.pem" ]] || exit 2
[[ -s "$KEY" && -s "$KNOWN" ]] || {
  echo "RRN05_CERT_PUSH=BLOCKED_SSH_TRUST_NOT_BOOTSTRAPPED" >&2
  exit 2
}
TMP=$(mktemp /root/rrn05-radio-cert-outbound.XXXXXXXX.pem)
trap 'rm -f "$TMP"' EXIT
cat "$LIVE/fullchain.pem" "$LIVE/privkey.pem" > "$TMP"
chmod 600 "$TMP"
openssl x509 -noout -checkend 1209600 -in "$TMP" >/dev/null
# The RMS listener (443) and LibreTime Admin (8700) share this certificate.
# Load the renewed lineage into the existing Apache workers without a full restart.
# Never touch another certificate lineage or a non-radio vhost config.
httpd -t >/dev/null
systemctl reload httpd
echo "RRN05_RMS_HTTPD_CERT_RELOAD=PASS"

ssh -T -i "$KEY" -o BatchMode=yes -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$KNOWN" \
  -o ConnectTimeout=8 "$IOT" < "$TMP"
echo "RRN05_CERT_PUSH=APPLIED_BY_IOT_RECEIVER"
