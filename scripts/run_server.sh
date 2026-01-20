#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Load .env if present (KEY=VALUE)
if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

python -m pip install -q -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
