#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${RUN_ID:-local_run}"
TRACE_ID="${TRACE_ID:-local_trace}"
AUDIT_ID="${AUDIT_ID:-local_audit}"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[%s] [run:%s] [trace:%s] [audit:%s] %s\n' "$(ts)" "$RUN_ID" "$TRACE_ID" "$AUDIT_ID" "$*"; }
info() { printf '[%s] [INFO] [run:%s] [trace:%s] [audit:%s] %s\n' "$(ts)" "$RUN_ID" "$TRACE_ID" "$AUDIT_ID" "$*"; }
warn() { printf '[%s] [WARN] [run:%s] [trace:%s] [audit:%s] %s\n' "$(ts)" "$RUN_ID" "$TRACE_ID" "$AUDIT_ID" "$*" >&2; }
err()  { printf '[%s] [ERROR] [run:%s] [trace:%s] [audit:%s] %s\n' "$(ts)" "$RUN_ID" "$TRACE_ID" "$AUDIT_ID" "$*" >&2; }

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  err "python interpreter not found (need python3 or python)"
  exit 2
fi

EXIT_CODE=0

log "Initializing gate run..."
info "Gate session initialized"

log "Running compileall check..."
if "$PYTHON_BIN" -m compileall .; then
  info "compileall: PASS"
else
  err "compileall: FAIL"
  EXIT_CODE=1
fi

log "Running pytest check..."
if command -v pytest >/dev/null 2>&1; then
  if pytest -q --maxfail=1; then
    info "pytest: PASS"
  else
    err "pytest: FAIL"
    EXIT_CODE=1
  fi
else
  warn "pytest not installed, skipping..."
fi

log "Running ruff check..."
if command -v ruff >/dev/null 2>&1; then
  if ruff check .; then
    info "ruff: PASS"
  else
    err "ruff: FAIL"
    EXIT_CODE=1
  fi
else
  warn "ruff not installed, skipping..."
fi

if [[ "$EXIT_CODE" -eq 0 ]]; then
  info "Gate PASSED"
else
  err "Gate FAILED - One or more checks failed"
fi

exit "$EXIT_CODE"
