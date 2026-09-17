#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [ ! -f dist/client/index.html ]; then
  printf '%s\n' 'Build the app first: npm install --ignore-scripts && npm run build'
  exit 1
fi
exec python3 studio/server.py "$@"
