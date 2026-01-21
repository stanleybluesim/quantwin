#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

BASE_BRANCH="main"
COMMITS=("99d6d78" "6f24850")

git checkout "$BASE_BRANCH"
git pull

BR="feat/day4-recover-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$BR"

apply_commit() {
  local c="$1"
  if git merge-base --is-ancestor "$c" HEAD; then
    echo "SKIP: $c already in history"
  else
    git cherry-pick "$c"
  fi
}

for c in "${COMMITS[@]}"; do
  apply_commit "$c"
done

./scripts/preflight.sh
git push -u origin HEAD

echo "OK. Open a PR from $BR -> $BASE_BRANCH"
