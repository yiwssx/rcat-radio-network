#!/usr/bin/env bash
# RRN-05: guarded Radio-only static listener publication on RMS.
# Not a proxy for Icecast, not an Admin/DJ endpoint.
set -Eeuo pipefail
umask 077

if [[ "$1" != "--apply" || "$2" != "--wan-and-rights-approved" ]]; then
  echo "Usage: bash rrn05-publish-listener-rms.sh --apply --wan-and-rights-approved" >&2
  exit 2
fi

DOMAIN=radio.rcat.ac.th
CONF=/etc/httpd/conf.d/radio-ssl.conf
WEBROOT=/var/www/radio-listener
CERT=/etc/letsencrypt/live/radio.rcat.ac.th
BACKUP=""
NEXT=""
MODIFIED=0
CREATED=0

rollback() {
  rc=$?
  trap - EXIT
  if [[ "$rc" -ne 0 ]]; then
    if [[ "$MODIFIED" == 1 && -s "$BACKUP" ]]; then
      cp -p "$BACKUP" "$CONF"
      if httpd -t >/dev/null 2>&1 && systemctl reload httpd; then
        echo "RRN05_RMS_ROLLBACK=RELOAD_RETURNED"
      else
        echo "RRN05_RMS_ROLLBACK=MANUAL_ATTENTION" >&2
      fi
    fi
    if [[ "$CREATED" == 1 ]]; then
      rm -f "$WEBROOT/index.html"
      rmdir "$WEBROOT" || true
    fi
    echo "RRN05_RMS_STATUS=BLOCKED" >&2
  fi
  [[ -z "$NEXT" ]] || rm -f "$NEXT"
  exit "$rc"
}
trap rollback EXIT

echo "=== RADIO LISTENER ONE-PASS INSTALL ==="
[[ "$(id -u)" == 0 ]] || exit 2
[[ -f "$CONF" && ! -L "$CONF" ]] || exit 2
[[ -s "$CERT/cert.pem" && -s "$CERT/chain.pem" && -s "$CERT/privkey.pem" ]] || exit 2
[[ ! -e "$WEBROOT" ]] || { echo "existing webroot: abort" >&2; exit 2; }
[[ "$(grep -Ec '^[[:space:]]*ServerName[[:space:]]+radio\.rcat\.ac\.th[[:space:]]*$' "$CONF")" == 1 ]] || exit 2
[[ "$(grep -Ec '^[[:space:]]*DocumentRoot /var/www/radio-acme[[:space:]]*$' "$CONF")" == 1 ]] || exit 2
[[ "$(grep -Ec '^[[:space:]]*Require all denied[[:space:]]*$' "$CONF")" == 1 ]] || exit 2
grep -q "SSLCertificateChainFile $CERT/chain.pem" "$CONF"
! grep -Eqi 'ProxyPass|RewriteRule|AliasMatch' "$CONF"
httpd -t

# Check only the new prerequisite affected by this release, not prior host tests.
CHECK=$(curl --noproxy '*' -sS --connect-timeout 4 --max-time 10 \
  --resolve "$DOMAIN:8443:10.10.1.100" -o /dev/null \
  -w '%{ssl_verify_result} %{http_code}' "https://$DOMAIN:8443/") || {
  echo "IOT Icecast TLS not yet available; no RMS change" >&2
  exit 2
}
read -r VERIFY HTTP <<< "$CHECK"
[[ "$VERIFY" == 0 && ( "$HTTP" == 200 || "$HTTP" == 302 || "$HTTP" == 403 ) ]] || exit 2

BACKUP=$(mktemp /root/rrn05-radio-ssl-before.XXXXXXXX.conf)
cp -p "$CONF" "$BACKUP"
NEXT=$(mktemp /etc/httpd/conf.d/.rrn05-radio-ssl.XXXXXXXX)
install -d -m 755 -o root -g root "$WEBROOT"
CREATED=1

cat > "$WEBROOT/index.html" <<'HTML'
<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0c1729">
<title>RCAT Radio Network | ฟังวิทยุออนไลน์</title>
<style>
:root{color-scheme:dark;font-family:system-ui,-apple-system,"Segoe UI",Tahoma,sans-serif}
*{box-sizing:border-box}
body{min-height:100vh;margin:0;background:radial-gradient(circle at 50% 14%,#24405e,#0c1729 55%,#070f1d);color:#f8fafc;display:flex;flex-direction:column}
header{width:min(100%,1000px);margin:0 auto;padding:27px 22px;color:#ffd49c;letter-spacing:.08em;font-weight:750}
main{width:min(100% - 32px,650px);margin:10vh auto auto}
section{padding:clamp(25px,5vw,48px);border:1px solid #54708a66;border-radius:26px;background:#15283ded;box-shadow:0 20px 60px #060a1888}
small{letter-spacing:.15em;color:#ffd49c;font-weight:750}
h1{font-size:clamp(2.3rem,6vw,3.6rem);line-height:1.12;margin:18px 0}
p{color:#b4c8db;line-height:1.7}
.player{margin-top:30px;padding:22px;border-radius:17px;background:#0b192b;border:1px solid #49658055}
audio{width:100%;display:block;margin:18px 0}
footer{text-align:center;color:#849bb0;font-size:.8rem;padding:36px}
</style>
</head>
<body>
<header>♫ &nbsp; RCAT RADIO NETWORK</header>
<main><section>
<small>RCAT • ONLINE RADIO</small>
<h1>เสียงดี ๆ จาก RCAT</h1>
<p>สถานีวิทยุออนไลน์ วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด</p>
<div class="player">
<strong>รับฟังผ่านสตรีม HTTPS</strong>
<audio id="radio" controls preload="none" aria-label="เครื่องเล่นวิทยุ RCAT">
<source src="https://radio.rcat.ac.th:8443/main.mp3" type="audio/mpeg">
เบราว์เซอร์นี้ไม่รองรับ HTML5 Audio
</audio>
<p id="notice" role="status">กดเล่นเพื่อเริ่มรับฟัง</p>
</div></section></main>
<footer>© RCAT Radio Network • สำหรับผู้ฟังเท่านั้น</footer>
<script>
const a=document.getElementById("radio"),n=document.getElementById("notice");
a.addEventListener("playing",()=>n.textContent="กำลังรับฟังสถานี");
a.addEventListener("waiting",()=>n.textContent="กำลังเชื่อมต่อ...");
a.addEventListener("error",()=>n.textContent="ยังไม่สามารถรับสัญญาณได้");
</script>
</body>
</html>
HTML
chmod 644 "$WEBROOT/index.html"

awk '
  /^[[:space:]]*DocumentRoot \/var\/www\/radio-acme[[:space:]]*$/ {
    print "    DocumentRoot /var/www/radio-listener"; changed_root++; next
  }
  /^[[:space:]]*Require all denied[[:space:]]*$/ {
    print "        Require all granted"; changed_auth++; next
  }
  /^<\/VirtualHost>$/ {
    print "    <Directory \"/var/www/radio-listener\">"
    print "        Options -Indexes -ExecCGI -Includes"
    print "        AllowOverride None"
    print "        Require all granted"
    print "    </Directory>"
    print "    DirectoryIndex index.html"
    print "    Header always set X-Frame-Options \"DENY\""
    print "    Header always set Strict-Transport-Security \"max-age=31536000\""
    print "    Header always set Referrer-Policy \"no-referrer\""
    print; changed_vhost++; next
  }
  {print}
  END { if(changed_root!=1 || changed_auth!=1 || changed_vhost!=1) exit 9 }
' "$CONF" > "$NEXT"

chmod 644 "$NEXT"
chown root:root "$NEXT"
cp -p "$NEXT" "$CONF"
MODIFIED=1
httpd -t
systemctl reload httpd
STATUS=$(curl --noproxy '*' -sS --connect-timeout 4 --max-time 10 \
  --resolve "$DOMAIN:443:127.0.0.1" -o /dev/null \
  -w '%{http_code} %{ssl_verify_result}' "https://$DOMAIN/")
[[ "$STATUS" == "200 0" ]] || exit 2
echo "RRN05_RMS_LISTENER=INSTALLED"
echo "RRN05_PUBLIC_URL=https://$DOMAIN/"
echo "RRN05_STREAM=https://$DOMAIN:8443/main.mp3"
echo "RRN05_UNRELATED_VHOSTS=NOT_EDITED"
echo "RRN05_WAN_AND_RIGHTS=OPERATOR_ATTESTED_NOT_VERIFIED"
