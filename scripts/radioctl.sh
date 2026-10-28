#!/usr/bin/env bash
# RCAT Radio Network: Docker-first, no Python interpreter required on the host.
# Docker Compose controls all services; an isolated audit container parses Compose JSON.
set -Eeuo pipefail
umask 077

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
COMPOSE_FILE="$ROOT/deployment/compose.pilot.yaml"
ENV_FILE="$ROOT/deployment/.env"
APP_ENV="$ROOT/deployment/azuracast.env"
PROJECT="rcat_radio_pilot"
MODE="${1:-help}"
BIND_IP="${2:-}"
REPORT_DIR="$ROOT/reports"
BASELINE_FILE="$REPORT_DIR/predeploy-baseline.txt"
APPROVAL_FILE="$REPORT_DIR/rrn-deploy-approval.txt"
PORTS=(8600 8605 8606 8700 8750)
STARTED=0

say() { printf '[RCAT Radio] %s\n' "$*"; }
stop_with_error() {
  say "BLOCK: $*" >&2
  exit 2
}
compose() {
  docker compose -p "$PROJECT" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}
require() {
  command -v "$1" >/dev/null 2>&1 || stop_with_error "Missing host command: $1"
}
help_text() {
  cat <<'USAGE'
RCAT Radio Network — Docker-only operator workflow (no host Python)
Usage:
  bash scripts/radioctl.sh check  <SERVER_RFC1918_IPV4>
  bash scripts/radioctl.sh deploy <SERVER_RFC1918_IPV4> --ack-shared-host
  bash scripts/radioctl.sh verify <SERVER_RFC1918_IPV4>
  bash scripts/radioctl.sh status
  bash scripts/radioctl.sh logs
  bash scripts/radioctl.sh stop

Deploy requires a private signed-off RRN-00/01/02 gate file and explicit
--ack-shared-host, then runs a fail-closed host preflight and creates env files,
audits rendered Compose inside a temporary Python container with NO
Docker socket, then starts only the RCAT radio project.

Admin access requires SSH tunnel: -L 8700:127.0.0.1:8700.
The one-station setup is manual. Production/public use is NOT approved.
USAGE
}
verify_ip() {
  [[ -n "$BIND_IP" ]] || stop_with_error "Provide the existing server's RFC1918 IPv4."
  if [[ ! "$BIND_IP" =~ ^10\.([0-9]{1,3}\.){2}[0-9]{1,3}$ ]] &&
     [[ ! "$BIND_IP" =~ ^192\.168\.([0-9]{1,3}\.)[0-9]{1,3}$ ]] &&
     [[ ! "$BIND_IP" =~ ^172\.(1[6-9]|2[0-9]|3[01])\.([0-9]{1,3}\.)[0-9]{1,3}$ ]]; then
    stop_with_error "Only existing RFC1918 IPv4 addresses are accepted."
  fi
  ip -o -4 addr show | awk -v target="$BIND_IP" '
    { split($4, bits, "/"); if (bits[1] == target) found=1 }
    END { exit (found ? 0 : 1) }
  ' || stop_with_error "The requested LAN address is not configured on this host."
}
resources() {
  local total available disk cpus
  total="$(awk '$1=="MemTotal:"{print $2}' /proc/meminfo)"
  available="$(awk '$1=="MemAvailable:"{print $2}' /proc/meminfo)"
  disk="$(df -Pk /var | awk 'NR==2{print $4}')"
  cpus="$(nproc)"
  [[ "$total" =~ ^[0-9]+$ && "$available" =~ ^[0-9]+$ && "$disk" =~ ^[0-9]+$ ]] || stop_with_error "Cannot read resource metrics."
  (( total >= 4194304 )) || stop_with_error "At least 4 GiB of total RAM required."
  (( available >= 2097152 )) || stop_with_error "At least 2 GiB of available RAM required."
  (( disk >= 41943040 )) || stop_with_error "At least 40 GiB disk free in /var required."
  (( cpus >= 4 )) || stop_with_error "At least 4 logical CPUs required."
  say "Resources: CPUs=$cpus, available RAM KiB=$available, free /var KiB=$disk"
}
check_no_existing_radio() {
  local existing volumes
  existing="$(docker ps -aq --filter "label=com.docker.compose.project=$PROJECT")" ||
    stop_with_error "Unable to query existing containers."
  [[ -z "$existing" ]] || stop_with_error "Pilot containers already exist. Use verify/status; never overwrite running pilot."
  if [[ ! -f "$ENV_FILE" && ! -f "$APP_ENV" ]]; then
    volumes="$(docker volume ls --format '{{.Name}}')" ||
      stop_with_error "Unable to query Docker volumes."
    if printf '%s\n' "$volumes" | grep -Eq '^rcat_radio_pilot_'; then
      stop_with_error "Old radio volumes exist without saved credentials: recover secrets first."
    fi
  fi
}
ports_free() {
  local listen published port
  listen="$(ss -H -lntu)" || stop_with_error "Cannot inspect system listening sockets."
  published="$(docker ps --format '{{.Ports}}')" ||
    stop_with_error "Cannot inspect Docker published ports."
  for port in "${PORTS[@]}"; do
    if printf '%s\n' "$listen" | awk -v port="$port" '
      { n=split($5,p,":"); if(p[n]==port) found=1 }
      END { exit(found ? 0 : 1) }
    '; then
      stop_with_error "Proposed host port $port is already bound."
    fi
    if printf '%s\n' "$published" | grep -Eq ":$port(->|-[0-9]+->)"; then
      stop_with_error "Proposed host port $port is already Docker-published."
    fi
  done
  say "Candidate host ports are not currently observed in use."
}
http_code() {
  curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 7 --connect-timeout 3 "$1" || true
}
before_pdf=""
before_any=""
baseline() {
  before_pdf="$(http_code "http://$BIND_IP:8081/")"
  before_any="$(http_code "http://$BIND_IP:8094/healthz")"
  [[ "$before_pdf" =~ ^[1-4][0-9][0-9]$ ]] ||
    stop_with_error "PDF HUB HTTP baseline failed; inspect service on port 8081 before proceeding."
  [[ "$before_any" == "200" ]] ||
    stop_with_error "AnyFlip /healthz baseline failed; inspect service on port 8094 before proceeding."
  say "Existing-service HTTP baseline: PDF=$before_pdf AnyFlip=$before_any"
}
regression() {
  local pdf any
  pdf="$(http_code "http://$BIND_IP:8081/")"
  any="$(http_code "http://$BIND_IP:8094/healthz")"
  [[ "$pdf" == "$before_pdf" && "$any" == "$before_any" ]] ||
    return 1
}
check_host() {
  for cmd in docker ip ss awk df nproc curl od tr grep; do require "$cmd"; done
  docker info >/dev/null 2>&1 || stop_with_error "Docker Engine is unavailable or permission denied."
  docker compose version >/dev/null 2>&1 ||
    stop_with_error "Docker Compose plugin is unavailable."
  verify_ip
  if [[ "$MODE" == "check" || "$MODE" == "deploy" ]]; then
    resources
    check_no_existing_radio
    ports_free
    baseline
  fi
}
require_deployment_approval() {
  [[ "${3:-}" == "--ack-shared-host" ]] ||
    stop_with_error "Deployment needs --ack-shared-host AFTER RRN-00/01/02 human approval. Run check first."
  [[ -f "$APPROVAL_FILE" && ! -L "$APPROVAL_FILE" ]] ||
    stop_with_error "Missing private approval file: reports/rrn-deploy-approval.txt; see docs/DOCKER-ONLY.md."
  local perms
  perms="$(stat -c '%a' "$APPROVAL_FILE")" ||
    stop_with_error "Cannot inspect local deployment approval permissions."
  [[ "$perms" == "600" || "$perms" == "400" ]] ||
    stop_with_error "Approval file must have owner-only permissions (chmod 600)."
  local record
  for record in \
    "RRN00=APPROVED" "RRN01=APPROVED" "RRN02=APPROVED" \
    "SHARED_HOST_CHANGE=APPROVED" "RRN_BIND_IP=$BIND_IP"; do
    grep -Fqx "$record" "$APPROVAL_FILE" ||
      stop_with_error "Approval file is incomplete or targets a different server. No deployment started."
  done
  say "Operator sign-off file present; technical preflight still required."
}
make_env() {
  if [[ -e "$ENV_FILE" || -e "$APP_ENV" ]]; then
    [[ -f "$ENV_FILE" && -f "$APP_ENV" ]] ||
      stop_with_error "Partial .env setup detected; refusing to overwrite secrets."
    grep -Fqx "RRN_BIND_IP=$BIND_IP" "$ENV_FILE" ||
      stop_with_error "Existing environment is bound to a different LAN IP."
    grep -Fqx "COMPOSE_PROJECT_NAME=$PROJECT" "$ENV_FILE" ||
      stop_with_error "Unexpected Compose project in existing environment."
    say "Using existing radio environment and saved database credentials."
    return 0
  fi
  local password uid gid
  password="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
  uid="$(id -u)"
  gid="$(id -g)"
  [[ "${#password}" == 64 ]] || stop_with_error "Unable to generate secure DB secret."
  ( set -C
    cat > "$ENV_FILE" <<EOF
COMPOSE_PROJECT_NAME=$PROJECT
AZURACAST_VERSION=stable
AZURACAST_HTTP_PORT=8700
AZURACAST_HTTPS_PORT=8743
AZURACAST_SFTP_PORT=2022
AZURACAST_PUID=$uid
AZURACAST_PGID=$gid
RRN_BIND_IP=$BIND_IP
EOF
    cat > "$APP_ENV" <<EOF
APPLICATION_ENV=production
LOG_LEVEL=notice
AUTO_ASSIGN_PORT_MIN=8600
AUTO_ASSIGN_PORT_MAX=8600
MYSQL_PASSWORD=$password
MYSQL_RANDOM_ROOT_PASSWORD=yes
SHOW_DETAILED_ERRORS=false
EOF
  ) || stop_with_error "Failed to initialize local private environment."
  chmod 600 "$ENV_FILE" "$APP_ENV"
  say "Created local private radio settings (credentials not displayed)."
}
persist_baseline() {
  mkdir -p "$REPORT_DIR"
  chmod 700 "$REPORT_DIR"
  if [[ -f "$BASELINE_FILE" ]]; then
    local oldpdf oldany
    oldpdf="$(awk -F= '$1=="pdf_hub"{print $2}' "$BASELINE_FILE")"
    oldany="$(awk -F= '$1=="anyflip"{print $2}' "$BASELINE_FILE")"
    [[ "$oldpdf" == "$before_pdf" && "$oldany" == "$before_any" ]] ||
      stop_with_error "Existing service status differs from recorded pre-deployment baseline."
    return
  fi
  ( set -C
    printf 'pdf_hub=%s\nanyflip=%s\n' "$before_pdf" "$before_any" > "$BASELINE_FILE"
  ) || stop_with_error "Cannot persist pre-deployment service baseline."
  chmod 600 "$BASELINE_FILE"
}
compare_persisted_baseline() {
  [[ -f "$BASELINE_FILE" ]] || return 1
  local pdf any
  pdf="$(awk -F= '$1=="pdf_hub"{print $2}' "$BASELINE_FILE")"
  any="$(awk -F= '$1=="anyflip"{print $2}' "$BASELINE_FILE")"
  [[ -n "$pdf" && -n "$any" ]] || return 1
  [[ "$(http_code "http://$BIND_IP:8081/")" == "$pdf" ]] &&
    [[ "$(http_code "http://$BIND_IP:8094/healthz")" == "$any" ]]
}
audit_compose_in_container() {
  say "Reviewing the fully rendered Docker Compose with the isolated audit container."
  # Pipe into a disposable container; no Docker socket or host Python involved.
  # Never print rendered Compose JSON, because it includes database credentials.
  compose config --format json |
    compose --profile audit run --rm -T --no-deps \
      -e "RRN_ALLOWED_BIND_IPS=$BIND_IP" audit
}
wait_http() {
  local url="$1" wanted="$2" i status
  for (( i=0; i<60; i++ )); do
    status="$(http_code "$url")"
    if [[ "$wanted" == "2xx" && "$status" =~ ^2[0-9][0-9]$ ]]; then return 0; fi
    if [[ "$wanted" == "not5xx" && "$status" =~ ^[1-4][0-9][0-9]$ ]]; then return 0; fi
    sleep 3
  done
  return 1
}
stop_only_radio() {
  say "Stopping only the RCAT radio project's new services; keeping volumes."
  compose stop portal web || true
}
generate_original_test_audio() {
  # Use the *already running* AzuraCast container's ffmpeg for an original tone.
  # No copyrighted music or additional host media tools are required.
  local target="$REPORT_DIR/original-test-tone.wav"
  if ! docker exec "$(compose ps -q web)" ffmpeg -hide_banner -loglevel error \
    -f lavfi -i "sine=frequency=440:sample_rate=22050:duration=12" \
    -af "volume=0.12" -ac 1 -y "/tmp/rrn-test-tone.wav" >/dev/null 2>&1; then
    say "Could not generate test WAV inside AzuraCast. Upload a rights-cleared sample manually."
    return 0
  fi
  docker cp "$(compose ps -q web):/tmp/rrn-test-tone.wav" "$target" >/dev/null 2>&1 || true
  [[ -s "$target" ]] && say "Generated original WAV: $target" || true
}
stamp_report() {
  mkdir -p "$REPORT_DIR"
  chmod 700 "$REPORT_DIR" 2>/dev/null || true
  printf 'mode=%s\nstatus=%s\ncreated_utc=%s\n' "$MODE" "$1" "$(date -u +%FT%TZ)"     > "$REPORT_DIR/last-result.txt"
  chmod 600 "$REPORT_DIR/last-result.txt"
}
deploy() {
  require_deployment_approval "$@"
  check_host
  persist_baseline
  make_env
  audit_compose_in_container || stop_with_error "Compose static audit failed. No radio container deployed."
  say "Pulling only AzuraCast and portal images."
  compose pull web portal || stop_with_error "Unable to pull radio images."
  say "Initializing AzuraCast in the radio project; no existing stacks are modified."
  compose run --rm --no-deps web -- azuracast_install ||
    stop_with_error "AzuraCast initialization failed; volumes and secrets retained. Do not overwrite credentials."
  say "Starting radio services."
  if ! compose up -d web portal; then
    stop_only_radio
    stop_with_error "Radio Compose start failed."
  fi
  STARTED=1
  if ! wait_http "http://127.0.0.1:8700/" not5xx ||
     ! wait_http "http://$BIND_IP:8750/" 2xx ||
     ! regression; then
    stop_only_radio
    stop_with_error "Startup health/regression failed. Only new radio services stopped."
  fi
  mkdir -p "$REPORT_DIR"
  generate_original_test_audio
  stamp_report "RADIO_STARTED_STATION_SETUP_REQUIRED"
  say "Web Admin (workstation SSH tunnel): http://127.0.0.1:8700"
  say "Listener portal (LAN): http://$BIND_IP:8750"
  say "Set up station shortcode rcat_radio, Icecast port 8600 and AutoDJ test media."
  say "Then run: bash scripts/radioctl.sh verify $BIND_IP"
  say "Actual Live DJ, 24h soak, restore, and conversion/download workflows remain manual tests."
}
verify() {
  check_host
  [[ -f "$ENV_FILE" ]] || stop_with_error "Radio credentials not found; the project is not provisioned."
  grep -Fqx "RRN_BIND_IP=$BIND_IP" "$ENV_FILE" || stop_with_error "Bind IP differs from radio environment."
  local admin portal status metadata stream bytes temp pid failed=0
  admin="$(http_code "http://127.0.0.1:8700/")"
  portal="$(http_code "http://$BIND_IP:8750/")"
  [[ "$admin" =~ ^[1-4][0-9][0-9]$ ]] || failed=1
  [[ "$portal" == 200 ]] || failed=1
  say "Admin HTTP=$admin Portal HTTP=$portal"
  mkdir -p "$REPORT_DIR"
  temp="$(mktemp -d "$REPORT_DIR/verify.XXXXXXXX")"
  chmod 700 "$temp"
  # Remove transient Now Playing metadata and probe results even if verification fails.
  trap 'rm -rf -- "$temp"' EXIT
  if curl -fsS --max-time 8 --max-filesize 1048576 \
      "http://$BIND_IP:8750/api/nowplaying/rcat_radio" -o "$temp/nowplaying.json"; then
    if grep -Eq '"shortcode"[[:space:]]*:[[:space:]]*"rcat_radio"' "$temp/nowplaying.json" &&
       grep -Eq '"is_online"[[:space:]]*:[[:space:]]*true' "$temp/nowplaying.json"; then
      say "Now Playing API: station rcat_radio is on air."
    else
      say "Now Playing API: station rcat_radio not present yet."
      failed=1
    fi
  else
    say "Now Playing API is not available."
    failed=1
  fi
  # Consume and discard stream bytes; keep only small metadata results locally.
  # Infinite radio streams routinely hit --max-time: size_download is still useful.
  for i in 1 2 3 4 5; do
    curl --silent --max-time 6 --connect-timeout 3 --output /dev/null \
      --write-out '%{http_code} %{content_type} %{size_download}\\n' \
      "http://$BIND_IP:8750/listen/rcat_radio/radio.mp3" \
      > "$temp/stream-$i.status" &
  done
  wait || true
  local code mime
  for i in 1 2 3 4 5; do
    code="" mime="" bytes=0
    read -r code mime bytes < "$temp/stream-$i.status" || true
    if [[ "$code" == "200" && "$mime" =~ ^(audio/|application/ogg) ]] &&
       [[ "$bytes" =~ ^[0-9]+$ ]] && (( bytes >= 512 )); then
      say "Stream client $i: HTTP 200, audio MIME, $bytes discarded bytes."
    else
      say "Stream client $i: no confirmed audio HTTP response."
      failed=1
    fi
  done
  if ! compare_persisted_baseline; then
    say "WARNING: Existing PDF HUB/AnyFlip differ from the saved pre-deployment baseline."
    failed=1
  fi
  if (( failed )); then
    stamp_report "STREAM_OR_REGRESSION_INCOMPLETE"
    stop_with_error "Smoke test not complete; inspect radio stream/settings. No existing project changed."
  fi
  stamp_report "SMOKE_PASS_MANUAL_TESTS_PENDING"
  say "PASS: 5 local stream clients, portal and API. Manual acceptance tests remain pending."
}
operational() {
  [[ -f "$ENV_FILE" ]] || stop_with_error "Radio environment not initialized."
  case "$MODE" in
    status) compose ps ;;
    logs) compose logs --tail 150 ;;
    stop) stop_only_radio ;;
  esac
}
case "$MODE" in
  help|-h|--help) help_text ;;
  check)
    check_host
    stamp_report "PREFLIGHT_PASS_MANUAL_APPROVAL_REQUIRED"
    say "Read-only preflight passed. No container started."
    ;;
  deploy) deploy "$@" ;;
  verify) verify ;;
  status|logs|stop) operational ;;
  *) help_text; exit 2 ;;
esac
