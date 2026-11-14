#!/usr/bin/env bash
# RCAT Radio Network — Issue #22 only. Creates a candidate static build; never deploys.
set -Eeuo pipefail

readonly ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Invalidate any stale candidate before attempting a fresh build.
rm -f "$ROOT/artifacts/rrn22-listener-dist.tar.gz" "$ROOT/artifacts/rrn22-listener-dist.tar.gz.sha256"

command -v node >/dev/null || { echo 'BLOCKED: Node.js not installed' >&2; exit 1; }
command -v npm >/dev/null || { echo 'BLOCKED: npm not installed' >&2; exit 1; }

# Compatible with Vite 7 and @sveltejs/vite-plugin-svelte 6.
node -e 'const [major,minor]=process.versions.node.split(".").map(Number); if (!(major>=24 || (major===22 && minor>=12) || (major===20 && minor>=19))) { console.error("BLOCKED: require Node.js >=20.19, >=22.12 or >=24; found "+process.version); process.exit(1); }'

readonly LOGO='public/images/RCAT.png'
readonly LOGO_SHA='de9118f241788a81b3aa7eb5cd160e4462a0c933137632da4d86005f1ba57d90'
[[ -f "$LOGO" ]] || { echo "BLOCKED: missing owner-supplied $LOGO" >&2; exit 1; }
printf '%s  %s\n' "$LOGO_SHA" "$LOGO" | sha256sum --check --status || { echo 'BLOCKED: original college-logo SHA-256 mismatch' >&2; exit 1; }

# A locally generated but uncommitted lockfile can be stale after a design-system dependency update.
# Use npm ci only for a reviewed lockfile committed to this branch.
if [[ -f package-lock.json ]] && git ls-files --error-unmatch package-lock.json >/dev/null 2>&1; then
  npm ci --no-audit --no-fund
else
  echo 'NOTE: package-lock.json is not tracked; npm install will refresh it for review and a future npm ci.'
  npm install --no-audit --no-fund
fi
npm run check
npm run build

[[ -s dist/index.html ]] || { echo 'BLOCKED: Vite did not generate dist/index.html' >&2; exit 1; }
[[ -s dist/images/RCAT.png ]] || { echo 'BLOCKED: built original logo is missing' >&2; exit 1; }
printf '%s  %s\n' "$LOGO_SHA" 'dist/images/RCAT.png' | sha256sum --check --status || { echo 'BLOCKED: built original logo differs from owner supplied file' >&2; exit 1; }
compgen -G 'dist/assets/*.js' >/dev/null || { echo 'BLOCKED: missing compiled JS asset' >&2; exit 1; }
compgen -G 'dist/assets/*.css' >/dev/null || { echo 'BLOCKED: missing compiled CSS asset' >&2; exit 1; }

mkdir -p artifacts
readonly ARCHIVE="$ROOT/artifacts/rrn22-listener-dist.tar.gz"
tar -czf "$ARCHIVE" -C "$ROOT/dist" .
(cd "$ROOT/artifacts" && sha256sum "$(basename "$ARCHIVE")" > "$(basename "$ARCHIVE").sha256")

echo 'PASS: Svelte typecheck, Vite production build, hashed assets, college-logo checksum.'
echo "Release candidate: $ARCHIVE"
echo "Checksum: ${ARCHIVE}.sha256"
echo 'NOT DONE: Browser click/playback acceptance and authorized RMS deployment must still be verified separately.'
