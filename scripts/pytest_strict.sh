#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Stable imports for tests (fix ModuleNotFoundError: app)
export PYTHONPATH=".:${PYTHONPATH:-}"

# Strict: show xfail/xpass details; target is 0 xfailed + 0 errors
python -m pytest -q -rxX
