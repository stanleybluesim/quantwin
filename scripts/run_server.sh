#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Load .env if present (KEY=VALUE)
if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi
# lazy-install deps only when requirements.txt changes
REQ_FILE="requirements.txt"
CACHE_DIR=".cache"
HASH_FILE="$CACHE_DIR/qw_requirements.sha256"

mkdir -p "$CACHE_DIR"

REQ_HASH="$(python - <<'PY2'
import hashlib, pathlib
p = pathlib.Path("requirements.txt")
h = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
print(h)
PY2
)"

if [ -n "$REQ_HASH" ] && [ -f "$HASH_FILE" ] && [ "$(cat "$HASH_FILE")" = "$REQ_HASH" ]; then
  echo "deps: OK (requirements.txt unchanged)"
else
  echo "deps: installing (requirements.txt changed or first run)"
  python -m pip install -q -r "$REQ_FILE"
  if [ -n "$REQ_HASH" ]; then
    echo "$REQ_HASH" > "$HASH_FILE"
  fi
fi
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
