#!/usr/bin/env bash
# Extract version from src/meta.typ.
# Usage: get_version.sh --full   → "2026.1"
#        get_version.sh --year   → "2026"
set -euo pipefail

META="$(dirname "$0")/../src/meta.typ"

full=$(sed -n 's/.*version[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' "$META")
if [[ -z "$full" ]]; then
  echo "error: could not extract version from $META — check format" >&2
  exit 1
fi

case "${1:---full}" in
  --full) echo "$full" ;;
  --year) echo "$full" | cut -d. -f1 ;;
  *) echo "usage: get_version.sh [--full|--year]" >&2; exit 2 ;;
esac
