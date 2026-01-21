#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "week4_day3 SAFE: will NOT overwrite app/*.py"
echo "Need the generator? Run: bash scripts/week4_day3_apply.sh"
./scripts/preflight.sh
