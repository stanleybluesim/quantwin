#!/usr/bin/env bash
set -euo pipefail

BASE_REF="${1:-origin/main}"
HEAD_REF="${2:-HEAD}"

if [ -x "./.venv-strictgate/bin/python" ]; then
  PY="./.venv-strictgate/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  echo "FAIL: no usable python interpreter" >&2
  exit 2
fi

RUN_ID="${RUN_ID:-local_run}"
TRACE_ID="${TRACE_ID:-local_trace}"
AUDIT_ID="${AUDIT_ID:-local_audit}"
export RUN_ID TRACE_ID AUDIT_ID

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[%s] [run:%s] [trace:%s] [audit:%s] %s\n' "$(ts)" "$RUN_ID" "$TRACE_ID" "$AUDIT_ID" "$*"; }

mkdir -p artifacts/gate .gate_logs

log "Initializing Phase 0 local gate..."
log "Using python: $PY"

"$PY" tools/qw_diff_scope.py --base-ref "$BASE_REF" --head-ref "$HEAD_REF" > .gate_logs/diff_scope.stdout
"$PY" tools/qw_phase0_guard.py > .gate_logs/guard.stdout

CHANGED_JSON="artifacts/gate/DiffScope.json"

HAS_ANY_CHANGES="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
print("1" if d.get("changed_files") else "0")
PY
)"

HAS_CODE_CHANGES="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
paths=d.get("changed_files", [])
print("1" if any(p.startswith(("app/","tools/","scripts/","tests/")) for p in paths) else "0")
PY
)"

HAS_OPENAPI_CHANGE="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
paths=d.get("changed_files", [])
print("1" if "contracts/openapi/openapi.yaml" in paths else "0")
PY
)"

HAS_SCHEMA_CHANGE="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
paths=d.get("changed_files", [])
print("1" if any(p.startswith("contracts/schemas/") for p in paths) else "0")
PY
)"

HAS_AUTH_PROTECTED="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
hits=d.get("protected_domain_hits", [])
print("1" if "auth" in hits else "0")
PY
)"

STATUS="PASS"
EXECUTED_CHECKS=()

if [ "$HAS_ANY_CHANGES" = "0" ]; then
  log "No changed files detected; guard-only PASS."
  EXECUTED_CHECKS+=("guard_only")
else
  if [ "$HAS_OPENAPI_CHANGE" = "1" ]; then
    log "Running validate_openapi.sh..."
    bash scripts/validate_openapi.sh
    EXECUTED_CHECKS+=("validate_openapi")
  fi

  if [ "$HAS_SCHEMA_CHANGE" = "1" ]; then
    log "Running validate_schemas.sh..."
    bash scripts/validate_schemas.sh
    EXECUTED_CHECKS+=("validate_schemas")
  fi

  if [ "$HAS_CODE_CHANGES" = "1" ]; then
    log "Running compileall on app/tools/scripts/tests..."
    "$PY" -m compileall app tools scripts tests
    EXECUTED_CHECKS+=("compileall")

    if [ "$HAS_AUTH_PROTECTED" = "1" ]; then
      log "Protected auth diff detected; running strict smoke regression..."
      "$PY" -m pytest tests/test_smoke.py
      EXECUTED_CHECKS+=("pytest_smoke")
    else
      log "Running baseline regression..."
      "$PY" -m pytest tests/test_smoke.py tests/test_e2e_golden_thread.py
      EXECUTED_CHECKS+=("pytest_smoke")
      EXECUTED_CHECKS+=("pytest_e2e")
    fi

    log "Running ruff on app/tools/scripts/tests..."
    "$PY" -m ruff check app tools scripts tests
    EXECUTED_CHECKS+=("ruff")
  fi
fi

EXECUTED_CHECKS_JSON="$("$PY" -c 'import json,sys; print(json.dumps(sys.argv[1:], ensure_ascii=False))' "${EXECUTED_CHECKS[@]}")"

"$PY" - <<'PY'
import json
from pathlib import Path

scope = json.loads(Path("artifacts/gate/DiffScope.json").read_text(encoding="utf-8"))
Path("artifacts/gate/_scope_cache.json").write_text(
    json.dumps(scope, ensure_ascii=False, indent=2), encoding="utf-8"
)
PY

CHANGED_FILES_JSON="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
print(json.dumps(d.get("changed_files", []), ensure_ascii=False))
PY
)"
PROTECTED_HITS_JSON="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
print(json.dumps(d.get("protected_domain_hits", []), ensure_ascii=False))
PY
)"
GOV_HITS_JSON="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
print(json.dumps(d.get("governance_critical_hits", []), ensure_ascii=False))
PY
)"
REQ_C7="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
print("true" if d.get("requires_c7_check", False) else "false")
PY
)"
REQ_BOUNDARY="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
print("true" if d.get("requires_boundary_guard", False) else "false")
PY
)"
REQ_APPROVAL="$("$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
print("true" if d.get("requires_approval_chain", False) else "false")
PY
)"

cat > artifacts/gate/GateReport.json <<JSON
{
  "status": "$STATUS",
  "run_id": "$RUN_ID",
  "trace_id": "$TRACE_ID",
  "audit_id": "$AUDIT_ID",
  "base_ref": "$BASE_REF",
  "head_ref": "$HEAD_REF",
  "changed_files": $CHANGED_FILES_JSON,
  "protected_domain_hits": $PROTECTED_HITS_JSON,
  "governance_critical_hits": $GOV_HITS_JSON,
  "requires_c7_check": $REQ_C7,
  "requires_boundary_guard": $REQ_BOUNDARY,
  "requires_approval_chain": $REQ_APPROVAL,
  "executed_checks": $EXECUTED_CHECKS_JSON
}
JSON

cat > artifacts/gate/GateReport.md <<MD
# GateReport

- status: $STATUS
- run_id: $RUN_ID
- trace_id: $TRACE_ID
- audit_id: $AUDIT_ID
- base_ref: $BASE_REF
- head_ref: $HEAD_REF

## Changed Files
$( "$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
for x in d.get("changed_files", []):
    print(f"- {x}")
PY
)

## Protected Domain Hits
$( "$PY" - <<'PY'
import json
d=json.load(open("artifacts/gate/DiffScope.json", encoding="utf-8"))
hits=d.get("protected_domain_hits", [])
if hits:
    for x in hits:
        print(f"- {x}")
else:
    print("- none")
PY
)

## Executed Checks
$(for x in "${EXECUTED_CHECKS[@]}"; do echo "- $x"; done)
MD

log "Gate PASSED"
