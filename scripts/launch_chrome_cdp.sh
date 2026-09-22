#!/usr/bin/env bash
# Launch a SEPARATE Chrome instance with remote debugging on a throwaway profile.
# WorkBuddy drives this instance via CDP; the user's real Chrome profile is never touched.
#
# Usage:
#   ./launch_chrome_cdp.sh [port] [profile_dir] [extra chrome args...]
#
# Example:
#   ./launch_chrome_cdp.sh 9222 "$HOME/chrome-cdp-profile"
set -euo pipefail

PORT="${1:-9222}"
PROFILE="${2:-$HOME/chrome-cdp-profile}"
shift 2 2>/dev/null || true

mkdir -p "$PROFILE"

# Allow overriding the binary; default to a common macOS / Linux location.
CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
if [ ! -x "$CHROME_BIN" ]; then
  CHROME_BIN="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
fi
if [ -z "$CHROME_BIN" ] || [ ! -x "$CHROME_BIN" ]; then
  echo "ERROR: Chrome/Chromium not found. Set CHROME_BIN=/path/to/chrome" >&2
  exit 1
fi

echo "Launching Chrome debug instance on port $PORT (profile: $PROFILE)"
# Route downloads to a fixed directory when set, so CDP download-behavior is not
# required (the browser-level command is rejected in some Chrome states).
DL_FLAG=""
if [ -n "${DOWNLOAD_DIR:-}" ]; then
  mkdir -p "$DOWNLOAD_DIR"
  DL_FLAG="--download-default-directory=$DOWNLOAD_DIR"
fi
# --no-sandbox is required when launched from a restricted/sandboxed shell; it is
# harmless on a normal desktop too. Remove it only if your environment forbids it.
exec "$CHROME_BIN" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE" \
  --no-first-run --no-default-browser-check \
  --no-sandbox \
  $DL_FLAG \
  "$@"
