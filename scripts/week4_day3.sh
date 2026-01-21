#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# TODO:
# 1 Implement store.search scoring BM25-lite or simple term match
# 2 Wire /v1/query to use store.search
# 3 Keep QueryResponse schema-valid no extra fields

./scripts/preflight.sh
