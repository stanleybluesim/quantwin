#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "==> git status"
git status -sb

echo "==> preflight"
bash scripts/week4_day3.sh

echo "OK"
