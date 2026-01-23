#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export PYTHONPATH=".:${PYTHONPATH:-}"
python -m pytest -q -rxX
