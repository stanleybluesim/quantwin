#!/usr/bin/env bash
set -euo pipefail

PY="./.venv-strictgate/bin/python"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[%s] %s\n' "$(ts)" "$*"; }
die() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

[ -x "$PY" ] || die "missing $PY"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not in git repo"

for p in \
  tools/qw_gate.sh \
  tools/qw_diff_scope.py \
  tools/qw_phase0_guard.py \
  .ruff.toml \
  pytest.ini \
  .github/workflows/dev-gate.yml \
  .github/workflows/auto-merge-on-green.yml
do
  [ -f "$p" ] || die "missing required file: $p"
done

log "Running Phase 0 local gate..."
bash tools/qw_gate.sh origin/main HEAD

log "Validating GateReport.json..."
"$PY" - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/gate/GateReport.json")
if not p.exists():
    raise SystemExit("GateReport.json missing")

d = json.loads(p.read_text(encoding="utf-8"))
required = [
    "status",
    "run_id",
    "trace_id",
    "audit_id",
    "base_ref",
    "head_ref",
    "changed_files",
    "protected_domain_hits",
    "governance_critical_hits",
    "requires_c7_check",
    "requires_boundary_guard",
    "requires_approval_chain",
    "executed_checks",
]
missing = [k for k in required if k not in d]
if missing:
    raise SystemExit(f"GateReport missing keys: {missing}")
if d["status"] != "PASS":
    raise SystemExit(f"GateReport status != PASS: {d['status']}")
if not isinstance(d["executed_checks"], list) or not d["executed_checks"]:
    raise SystemExit("executed_checks must be non-empty list")
print("PASS GateReport.json")
PY

log "Validating workflow YAML..."
"$PY" - <<'PY'
import yaml
for p in [
    ".github/workflows/dev-gate.yml",
    ".github/workflows/auto-merge-on-green.yml",
]:
    with open(p, "r", encoding="utf-8") as f:
        yaml.safe_load(f)
    print(f"PASS {p}")
PY

mkdir -p artifacts/gate
cat > artifacts/gate/PR_BODY_phase0.md <<'MD'
## Scope
Implements QuantWin AEF Phase 0 only.

## Included
- local diff-first gate
- diff scope + phase0 guard
- gate audit report with executed_checks
- dev-gate workflow
- protected auto-merge workflow
- YAML parsing fix for auto-merge workflow

## Verified
- `bash tools/qw_gate.sh origin/main HEAD` => PASS
- `GateReport.json` contains `changed_files / governance_critical_hits / executed_checks`
- protected auth diff:
  - without approval => blocked
  - with approval => pass
- workflow YAML parse:
  - `.github/workflows/dev-gate.yml` => PASS
  - `.github/workflows/auto-merge-on-green.yml` => PASS

## Out of Scope
- Phase 1~6
- runtime policy publish/rollback
- devloop contracts/docs residual files
MD

log "Generated artifacts/gate/PR_BODY_phase0.md"
log "Done."

echo
echo "==> Gate report"
cat artifacts/gate/GateReport.json
echo
echo "==> Current status"
git status --short
echo
echo "==> PR body file"
echo "artifacts/gate/PR_BODY_phase0.md"
