#!/usr/bin/env bash
# RRN-01: focused, read-only host preflight for the isolated Icecast/LibreTime stack.
# No sudo, network requests, Docker start/stop, configuration rendering, or changes.
# Run on the intended RCAT host only when a live preflight is necessary.
set -uo pipefail

RRN01_BLOCKERS=0
RRN01_UNKNOWN=0
section() { printf '\n=== %s ===\n' "$1"; }
ok() { printf 'PASS: %s\n' "$1"; }
pending() { printf 'UNKNOWN: %s\n' "$1"; RRN01_UNKNOWN=$((RRN01_UNKNOWN + 1)); }
blocked() { printf 'BLOCKED: %s\n' "$1"; RRN01_BLOCKERS=$((RRN01_BLOCKERS + 1)); }

section "Host identity and supported tooling"
if [ -r /etc/os-release ]; then
  (. /etc/os-release; printf 'OS: %s\n' "${PRETTY_NAME:-unknown}")
else pending "OS information unavailable"; fi
if arch="$(uname -m 2>/dev/null)" && [ -n "$arch" ]; then
  printf 'Architecture: %s\n' "$arch"
else pending "Host architecture unavailable"; fi
# Verify only the historic radio LAN address, not the host's full interface inventory.
if command -v ip >/dev/null 2>&1; then
  if ipv4="$(ip -o -4 addr show 2>/dev/null)"; then
    if printf '%s\n' "$ipv4" | awk '$4 ~ /^10[.]10[.]1[.]100\// {found=1} END {exit !found}'; then
      ok "Historic RCAT LAN IPv4 10.10.1.100 is present"
    else pending "Historic LAN IPv4 not found; confirm current host routing before any remote DJ ingress"; fi
  else pending "IPv4 interface inspection unavailable"; fi
else pending "ip CLI unavailable; LAN IPv4 not verified"; fi
if command -v docker >/dev/null 2>&1; then
  printf 'Docker client: '; docker --version 2>/dev/null || true
  if compose_version="$(docker compose version --short 2>/dev/null)"; then
    printf 'Docker Compose: %s\n' "$compose_version"
    semver="${compose_version#v}"
    semver="${semver%%[-+]*}"
    if [[ "$semver" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
      major="${BASH_REMATCH[1]}"
      minor="${BASH_REMATCH[2]}"
      patch="${BASH_REMATCH[3]}"
      if (( 10#$major > 2 || (10#$major == 2 && (10#$minor > 24 || (10#$minor == 24 && 10#$patch >= 4))) )); then
        ok "Docker Compose v2.24.4+ meets the !override syntax requirement"
      else blocked "Docker Compose must be >= 2.24.4 for !override"; fi
    else pending "Unrecognized Compose version; verify !override support before use"; fi
  else pending "Docker Compose not accessible"; fi
else pending "Docker CLI not installed or not in PATH"; fi

section "Current storage and memory (read-only)"
if command -v df >/dev/null 2>&1; then
  if disk_report="$(df -hP / /opt /etc /var/backups 2>/dev/null)"; then
    printf '%s\n' "$disk_report" | awk 'NR==1 || !seen[$1]++'
  else pending "Disk capacity report incomplete for required paths"; fi
else pending "df unavailable"; fi
if [ -r /proc/meminfo ]; then
  awk '/^(MemTotal|MemAvailable|SwapTotal|SwapFree):/ {print}' /proc/meminfo
else pending "Memory information unavailable"; fi
if [ -r /proc/loadavg ]; then
  printf 'Load 1/5/15: '; awk '{print $1, $2, $3}' /proc/loadavg
fi

section "Candidate radio-only port conflicts"
if command -v ss >/dev/null 2>&1; then
  # A failed ss must NEVER be interpreted as confirmation that ports are free.
  if listeners="$(ss -H -ltn 2>/dev/null)"; then
    for port in 8600 8605 8700; do
      matches="$(printf '%s\n' "$listeners" | awk -v p=":$port" '$4 ~ (p "$") {print $4}')"
      if [ -n "$matches" ]; then
        blocked "Port $port already has a listener; select another radio-only port without changing the existing owner"
      else
        printf 'FREE_OBSERVED: no TCP listener on %s at this instant\n' "$port"
      fi
    done
  else pending "ss failed; port occupancy UNKNOWN, not free"; fi
else pending "ss unavailable; port occupancy UNKNOWN, not free"; fi
# An available TCP port is NOT a firewall/ingress/access-control confirmation.

section "Proposed radio-only path ownership"
for path in /opt/rcat-radio-network /etc/rcat-radio-network /var/backups/rcat-radio-network; do
  if [ -e "$path" ] || [ -L "$path" ]; then
    # No file listing or secret content. Do not make directory changes.
    if command -v stat >/dev/null 2>&1; then
      stat -c '%n: exists, owner=%U group=%G mode=%a' "$path" 2>/dev/null || pending "Cannot inspect $path"
    else pending "stat unavailable; cannot inspect $path"; fi
  else printf 'NOT_CREATED: %s\n' "$path"; fi
done

section "Read-only verdict"
printf '%s\n' 'This script checks only this host at this instant; it does not reserve ports or resources.'
printf '%s\n' 'This script does not verify Docker Compose merged config, service health, Icecast audio, TLS, or runtime installation.'
printf '%s\n' 'It does not authorize any deployment, installation, file write, restart or Production change.'
printf '%s\n' 'If a port is occupied or capacity is insufficient, STOP; do not evict another service.'
if (( RRN01_BLOCKERS > 0 )); then
  printf 'RRN01_HOST_READONLY_STATUS=BLOCKED blockers=%s unknown=%s\n' "$RRN01_BLOCKERS" "$RRN01_UNKNOWN"
  exit 2
elif (( RRN01_UNKNOWN > 0 )); then
  printf 'RRN01_HOST_READONLY_STATUS=INCOMPLETE blockers=0 unknown=%s\n' "$RRN01_UNKNOWN"
  exit 3
else
  printf '%s\n' 'RRN01_HOST_READONLY_STATUS=PROVISIONAL_PASS (merged Compose and deployment approval still pending)'
  exit 0
fi
