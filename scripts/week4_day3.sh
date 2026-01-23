#!/usr/bin/env bash
set -euo pipefail

# QW test-mode auth (deterministic local preflight)
export QW_TEST_MODE="${QW_TEST_MODE:-1}"
export QW_TEST_BEARER_TOKEN="${QW_TEST_BEARER_TOKEN:-test-token}"

echo "==> validate docs"
bash scripts/validate_docs.sh

cd "$(git rev-parse --show-toplevel)"

echo "week4_day3 SAFE: will NOT overwrite app/*.py"
echo "Need the generator? Run: bash scripts/week4_day3_apply.sh"
./scripts/preflight.sh
