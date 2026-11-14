#!/usr/bin/env bash
# Read-only-to-production Icecast 2.5 TLS compatibility probe.
# Starts a throwaway container on local-only :8866; NEVER recreates the radio.
set -Eeuo pipefail

readonly image="ghcr.io/libretime/icecast:2.5.0"
readonly current="rcat_radio_network-icecast-1"
readonly config="/etc/rcat-radio-network/icecast-tls.xml"
readonly bundle="/etc/rcat-radio-network/icecast-bundle.pem"
readonly name="rcat-icecast-250-tls-probe-$$"
created=0

cleanup() {
  if [[ "$created" == 1 ]]; then
    docker rm -f "$name" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ "$EUID" -ne 0 ]]; then
  echo "PROBE=STOPPED: run using sudo" >&2
  exit 1
fi
for file in "$config" "$bundle"; do
  if [[ ! -f "$file" || -L "$file" ]]; then
    echo "PROBE=STOPPED: missing or symlinked TLS input: $file" >&2
    exit 1
  fi
done
if ! docker image inspect "$image" >/dev/null 2>&1; then
  echo "PROBE=STOPPED: Icecast 2.5.0 image is not cached" >&2
  exit 1
fi

running_image="$(docker inspect -f '{{.Config.Image}}' "$current")"
running_state="$(docker inspect -f '{{.State.Running}}' "$current")"
if [[ "$running_image" != "ghcr.io/libretime/icecast:2.4.4" || "$running_state" != "true" ]]; then
  echo "PROBE=STOPPED: expected live radio Icecast 2.4.4 before isolated test" >&2
  exit 1
fi
# A fixed loopback port avoids any Internet exposure and will fail closed if occupied.
echo "PROBE=STARTING_EPHEMERAL_ICECAST_250"
echo "PROBE_SCOPE=LOOPBACK_127.0.0.1_8866_ONLY"
echo "PRODUCTION_ICECAST=UNTOUCHED"
created=1
docker run --detach \
  --name "$name" --network bridge \
  --publish "127.0.0.1:8866:8443" \
  --user "1000:0" \
  --mount "type=bind,source=$config,target=/etc/icecast.xml,readonly" \
  --mount "type=bind,source=$bundle,target=/etc/icecast-bundle.pem,readonly" \
  --entrypoint icecast \
  "$image" -c /etc/icecast.xml >/dev/null

status="NOT_READY"
for attempt in 1 2 3 4 5 6; do
  set +e
  result="$(curl --noproxy '*' --silent --show-error \
    --connect-timeout 3 --max-time 5 \
    --resolve "radio.rcat.ac.th:8866:127.0.0.1" \
    --output /dev/null \
    --write-out 'HTTP=%{http_code} TLS_VERIFY=%{ssl_verify_result} BYTES=%{size_download}' \
    'https://radio.rcat.ac.th:8866/' 2>&1)"
  exit_code=$?
  set -e
  echo "ATTEMPT=$attempt CURL_EXIT=$exit_code $result"
  if [[ "$exit_code" == 0 && "$result" == *"TLS_VERIFY=0"* && "$result" == *"HTTP="* ]]; then
    status="TLS_OK"
    break
  fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null || true)" != "true" ]]; then
    status="CONTAINER_EXITED"
    break
  fi
  sleep 2
done
echo "PROBE_STATUS=$status"

# Logs are inspected inside the script. Never print raw canary logs or XML,
# because private TLS settings and stream credentials belong only on the Host.
if [[ "$status" != "TLS_OK" ]]; then
  logs="$(docker logs --tail 100 "$name" 2>&1 || true)"
  if [[ "$logs" == *"Invalid cert file"* || "$logs" == *"No TLS capability"* ]]; then
    echo "PROBE_LOG_HINT=TLS_CERTIFICATE_OR_TLS_CONTEXT"
  elif [[ "$logs" == *"Permission denied"* ]]; then
    echo "PROBE_LOG_HINT=FILE_PERMISSION"
  elif [[ "$logs" == *"Address already in use"* || "$logs" == *"bind failed"* ]]; then
    echo "PROBE_LOG_HINT=LISTENER_BIND"
  elif [[ "$logs" == *"Error"* || "$logs" == *"ERROR"* || "$logs" == *"WARN"* ]]; then
    echo "PROBE_LOG_HINT=ICECAST_ERROR_OR_WARNING"
  else
    echo "PROBE_LOG_HINT=NO_RECOGNIZED_ERROR"
  fi
fi
if [[ "$status" == "TLS_OK" ]]; then
  echo "PROBE_RESULT=TLS_CONFIG_COMPATIBLE_ICECAST_250"
  echo "PROBE_AUDIO_MOUNT=NOT_TESTED_NO_SOURCE_IN_CANARY"
else
  echo "PROBE_RESULT=TLS_NOT_VERIFIED_ON_CANARY"
  exit 1
fi
