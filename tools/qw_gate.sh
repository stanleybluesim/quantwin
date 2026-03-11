#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${RUN_ID:-local_run}"
TRACE_ID="${TRACE_ID:-local_trace}"
AUDIT_ID="${AUDIT_ID:-local_audit}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log()  { printf '[%s] [run:%s] [trace:%s] [audit:%s] %s\n'  "$(ts)" "$RUN_ID" "$TRACE_ID" "$AUDIT_ID" "$*"; }
info() { printf '[%s] [INFO] [run:%s] [trace:%s] [audit:%s] %s\n'  "$(ts)" "$RUN_ID" "$TRACE_ID" "$AUDIT_ID" "$*"; }
err()  { printf '[%s] [ERROR] [run:%s] [trace:%s] [audit:%s] %s\n' "$(ts)" "$RUN_ID" "$TRACE_ID" "$AUDIT_ID" "$*" >&2; }

PYTHON_BIN=""
if [[ -x "$REPO_ROOT/.venv-strictgate/bin/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv-strictgate/bin/python"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.11)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  err "python interpreter not found"
  exit 2
fi

"$PYTHON_BIN" -m pytest --version >/dev/null 2>&1 || {
  err "pytest not available in selected python: $PYTHON_BIN"
  exit 2
}
"$PYTHON_BIN" -m ruff --version >/dev/null 2>&1 || {
  err "ruff not available in selected python: $PYTHON_BIN"
  exit 2
}

EXIT_CODE=0

log "Initializing strict gate run..."
info "Gate session initialized"
info "Using python: $PYTHON_BIN"

log "Running compileall check..."
if "$PYTHON_BIN" -m compileall .; then
  info "compileall: PASS"
else
  err "compileall: FAIL"
  EXIT_CODE=1
fi

log "Running pytest check..."
if "$PYTHON_BIN" -m pytest -q --maxfail=1; then
  info "pytest: PASS"
else
  err "pytest: FAIL"
  EXIT_CODE=1
fi

log "Running ruff check..."
if "$PYTHON_BIN" -m ruff check .; then
  info "ruff: PASS"
else
  err "ruff: FAIL"
  EXIT_CODE=1
fi

if [[ "$EXIT_CODE" -eq 0 ]]; then
  info "Gate PASSED"
else
  err "Gate FAILED - One or more checks failed"
fi

exit "$EXIT_CODE"
