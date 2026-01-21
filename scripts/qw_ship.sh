#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git checkout main >/dev/null 2>&1 || true
git pull

DIRTY="$(git status --porcelain | awk '{print $2}' | grep -vE '^scripts/qw_one\.sh$' || true)"
if [ -n "$DIRTY" ]; then
  echo "ERROR: 还有其它未提交改动："
  echo "$DIRTY"
  git status -sb
  exit 1
fi

if [ ! -f scripts/qw_one.sh ]; then
  echo "ERROR: scripts/qw_one.sh not found"
  exit 1
fi

git add scripts/qw_one.sh
git commit -m "chore(scripts): add qw_one helper (status + preflight)" || true
git push

echo "==> status"
git status -sb

echo "==> run one-click"
bash scripts/qw_one.sh

echo "OK: shipped"
