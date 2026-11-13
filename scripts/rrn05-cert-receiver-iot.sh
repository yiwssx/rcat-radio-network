#!/usr/bin/env bash
# Run as the non-root rcat_iot_admin via a restricted SSH authorized_keys command.
# Receives only a TLS PEM bundle over stdin, then calls exactly one guarded
# root-owned radio certificate rotator via narrow sudoers permission.
set -Eeuo pipefail
umask 077
if [[ "$(id -un)" != "rcat_iot_admin" || "$#" -ne 0 ]]; then
  echo "RRN05_CERT_RECEIVER=DENIED" >&2
  exit 2
fi
DIR=/home/rcat_iot_admin
DEST=$DIR/.rrn05-radio-cert-next.pem
[[ -d "$DIR" && ! -L "$DIR" ]] || exit 2
TMP=$(mktemp "$DIR/.rrn05-radio-inbound.XXXXXXXX")
trap 'rm -f "$TMP"' EXIT
# Limit inbound size and never echo sensitive PEM or OpenSSL private-key output.
head -c 32769 > "$TMP"
SIZE=$(wc -c < "$TMP")
[[ "$SIZE" -ge 1400 && "$SIZE" -le 32768 ]] || exit 2
chmod 600 "$TMP"
mv -f -T "$TMP" "$DEST"
sudo -n /usr/bin/python3 /usr/local/sbin/rrn05-rotate-icecast-cert.py --apply
