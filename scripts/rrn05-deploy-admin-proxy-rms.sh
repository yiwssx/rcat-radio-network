#!/usr/bin/env bash
# RRN-05: scoped RMS-only HTTPS reverse proxy for LibreTime's WEB UI.
set -Eeuo pipefail
umask 077
[[ "$#" -eq 1 && "$1" == "--apply" ]] || { echo "Usage: sudo bash rrn05-deploy-admin-proxy-rms.sh --apply"; exit 2; }

DOMAIN=radio.rcat.ac.th
RMS=10.10.2.100
IOT=10.10.1.100
CERT=/etc/letsencrypt/live/radio.rcat.ac.th
CONF=/etc/httpd/conf.d/zz-rrn05-admin-8700.conf
STAGED=0
rollback() {
  local code=$?
  trap - EXIT
  if [[ $code -ne 0 && $STAGED -eq 1 ]]; then
    rm -f -- "$CONF"
    if httpd -t >/dev/null 2>&1 && systemctl reload httpd; then
      echo "RRN05_RMS_ADMIN_ROLLBACK=CONFIG_RESTORED"
    else
      echo "RRN05_RMS_ADMIN_ROLLBACK=MANUAL_ATTENTION" >&2
    fi
  fi
  exit "$code"
}
trap rollback EXIT

[[ $(id -u) -eq 0 ]] || { echo "BLOCKED: root required" >&2; exit 2; }
for c in httpd systemctl curl ss ip openssl; do command -v "$c" >/dev/null || { echo "BLOCKED: missing $c" >&2; exit 2; }; done
[[ ! -e "$CONF" && ! -L "$CONF" ]] || { echo "BLOCKED: dedicated vhost exists" >&2; exit 2; }
[[ -s "$CERT/cert.pem" && -s "$CERT/privkey.pem" && -s "$CERT/chain.pem" ]] || { echo "BLOCKED: existing certificate/chain unavailable" >&2; exit 2; }
openssl x509 -checkend 1209600 -noout -in "$CERT/cert.pem" >/dev/null || { echo "BLOCKED: certificate expiry" >&2; exit 2; }
ip -o -4 addr show | grep -Fq "$RMS/" || { echo "BLOCKED: RMS does not own $RMS" >&2; exit 2; }
! ss -H -ltn | awk '{print $4}' | grep -Eq '(^|:)8700$' || { echo "BLOCKED: TCP 8700 occupied on RMS" >&2; exit 2; }
mods=$(httpd -M 2>/dev/null)
for m in ssl_module proxy_module proxy_http_module headers_module; do
  grep -q " $m " <<< " $mods " || { echo "BLOCKED: Apache module $m missing" >&2; exit 2; }
done
httpd -t >/dev/null || { echo "BLOCKED: existing Apache config" >&2; exit 2; }
upstream=$(curl --noproxy '*' --silent --show-error --connect-timeout 4 --max-time 8 \
  --output /dev/null --write-out '%{http_code}' "http://$IOT:8700/login") || {
  echo "BLOCKED: IOT LibreTime LAN web unreachable" >&2; exit 2;
}
[[ "$upstream" == 200 || "$upstream" == 302 || "$upstream" == 301 ]] || {
  echo "BLOCKED: IOT web returned HTTP $upstream" >&2; exit 2;
}
if command -v getenforce >/dev/null && [[ "$(getenforce)" == Enforcing ]]; then
  echo "BLOCKED: SELinux enforcing; Apache TCP 8700 bind and proxy LAN connect policy require host-specific approval" >&2
  exit 2
fi

STAGED=1
cat > "$CONF" <<'APACHE'
# RRN05-only: LibreTime WEB UI behind existing RMS radio certificate.
Listen 10.10.2.100:8700 https
<VirtualHost 10.10.2.100:8700>
    ServerName radio.rcat.ac.th
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/radio.rcat.ac.th/cert.pem
    SSLCertificateChainFile /etc/letsencrypt/live/radio.rcat.ac.th/chain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/radio.rcat.ac.th/privkey.pem
    ProxyRequests Off
    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Host "radio.rcat.ac.th:8700"
    RequestHeader set X-Forwarded-Port "8700"
    ProxyPass / http://10.10.1.100:8700/ connectiontimeout=5 timeout=300
    ProxyPassReverse / http://10.10.1.100:8700/
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "same-origin"
</VirtualHost>
APACHE
chmod 0644 "$CONF"
httpd -t
systemctl reload httpd
# Apache graceful reload can return before newly-added Listen sockets are
# observable; a successful syntax check alone does not prove a bound socket.
# Wait for only this newly-added listener and its TLS/backend readiness.
state=NO_SOCKET
http=000
verify=unknown
for attempt in {1..15}; do
  if ss -H -ltn | awk '{print $4}' | grep -Fxq "$RMS:8700"; then
    state=SOCKET_OPEN
    if result=$(curl --noproxy '*' --silent --connect-timeout 2 --max-time 7 \
      --resolve "$DOMAIN:8700:$RMS" -o /dev/null \
      -w '%{http_code} %{ssl_verify_result}' "https://$DOMAIN:8700/login" 2>/dev/null); then
      read -r http verify <<< "$result"
      if [[ "$verify" == 0 && ( "$http" == 200 || "$http" == 301 || "$http" == 302 || "$http" == 303 ) ]]; then
        state=TLS_ACCEPTED
        break
      fi
      state=SOCKET_OPEN_BAD_RESPONSE
    else
      state=SOCKET_OPEN_CONNECT_OR_TLS_FAILED
    fi
  fi
  sleep 2
done
if [[ "$state" != TLS_ACCEPTED ]]; then
  echo "RRN05_RMS_8700_STATE=$state" >&2
  echo "RRN05_RMS_8700_HTTP=$http SSL_VERIFY=$verify" >&2
  if [[ "$state" == SOCKET_OPEN_CONNECT_OR_TLS_FAILED ]]; then
    echo "NEXT=Check only RMS host INPUT firewall for 10.10.2.100:8700; do not change MikroTik" >&2
  elif [[ "$state" == NO_SOCKET ]]; then
    echo "NEXT=Inspect RMS httpd Listen startup; no host restart requested" >&2
  else
    echo "NEXT=Inspect LibreTime canonical URL and proxy headers, not router NAT" >&2
  fi
  exit 2
fi
STAGED=0
echo "RRN05_RMS_8700_STATE=TLS_ACCEPTED"
echo "RRN05_RMS_ADMIN_HTTPS=READY"
echo "RRN05_ADMIN_PUBLIC_URL=https://radio.rcat.ac.th:8700/login"
echo "RRN05_MIKROTIK=NOT_CHANGED"
echo "RRN05_IOT_PUBLIC_URL=NOT_CHANGED"
