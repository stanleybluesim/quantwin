#!/usr/bin/env bash
set -euo pipefail
echo "==> validate docs"
bash scripts/validate_docs.sh

cd "$(git rev-parse --show-toplevel)"

echo "==> validate openapi"
bash scripts/validate_openapi.sh

echo "==> validate schemas"
bash scripts/validate_schemas.sh

echo "==> run tests"
python -m pytest -q

echo "OK: preflight passed"
