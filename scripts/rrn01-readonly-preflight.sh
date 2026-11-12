#!/usr/bin/env bash
# RRN-01: focused, read-only host preflight for the isolated Icecast/LibreTime stack.
# No sudo, network requests, Docker start/stop, configuration rendering, or changes.
# Run on the intended RCAT host only when a live preflight is necessary.
set -uo pipefail

section() { printf '\n=== %s ===\n' "$1"; }
ok() { printf 'PASS: %s\n' "$1"; }
pending() { printf 'PENDING: %s\n' "$1"; }

section "Host identity and supported tooling"
if [ -r /etc/os-release ]; then
  (. /etc/os-release; printf 'OS: %s\n' "${PRETTY_NAME:-unknown}")
else pending "OS information unavailable"; fi
printf 'Architecture: %s\n' "$(uname -m 2>/dev/null || printf unknown)"
if command -v docker >/dev/null 2>&1; then
  printf 'Docker client: '; docker --version 2>/dev/null || true
  if compose_version="$(docker compose version --short 2>/dev/null)"; then
    printf 'Docker Compose: %s\n' "$compose_version"
    semver="${compose_version#v}"
    semver="${semver%%[-+]*}"
    if [[ "$semver" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
      major="${BASH_REMATCH[1]}"
      minor="${BASH_REMATCH[2]}"
      if (( 10#$major > 2 || (10#$major == 2 && 10#$minor >= 24) )); then
        ok "Compose CLI supports !override (v2.24.4+ threshold still requires patch check below)"
        if (( 10#$major == 2 && 10#$minor == 24 )) && (( 10#${BASH_REMATCH[3]} < 4 )); then
          printf 'BLOCKED: Compose CLI version must be >=2.24.4 for !override\n'
        fi
      else printf 'BLOCKED: Compose CLI version must be >=2.24.4 for !override\n'; fi
    else pending "Unrecognized Compose version; verify !override support before use"; fi
  else pending "Docker Compose not accessible"; fi
else pending "Docker CLI not installed or not in PATH"; fi

section "Current storage and memory (read-only)"
if command -v df >/dev/null 2>&1; then
  df -hP / /opt /etc /var/backups 2>/dev/null | awk 'NR==1 || !seen[$1]++'
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
        printf 'CONFLICT: port %s has listener(s); select a different radio-only port\n' "$port"
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
    fi
  else printf 'NOT_CREATED: %s\n' "$path"; fi
done

section "Read-only verdict"
printf '%s\n' 'This script does not verify Docker Compose merged config, service health, Icecast audio, TLS, or runtime installation.'
printf '%s\n' 'It does not authorize any deployment, installation, file write, restart or Production change.'
printf '%s\n' 'If a port is occupied or capacity is insufficient, STOP; do not evict another service.'
