#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

try:
    import yaml
except Exception as e:
    print(f"FAIL: missing PyYAML: {e}", file=sys.stderr)
    sys.exit(2)

REQUIRED_AEF_KEYS = [
    "human_approval_timeout",
    "ttl_days",
    "adapter_health_threshold",
    "egress_mode",
    "allowlist",
    "protected_domains",
    "gate_switches",
]

def fail(code: str, msg: str) -> int:
    report = {
        "status": "FAIL",
        "error_code": code,
        "message": msg,
        "run_id": os.environ.get("RUN_ID", ""),
        "trace_id": os.environ.get("TRACE_ID", ""),
        "audit_id": os.environ.get("AUDIT_ID", ""),
    }
    Path("artifacts/gate").mkdir(parents=True, exist_ok=True)
    Path("artifacts/gate/GuardReport.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1

def ok(scope: dict) -> int:
    report = {
        "status": "PASS",
        "run_id": os.environ.get("RUN_ID", ""),
        "trace_id": os.environ.get("TRACE_ID", ""),
        "audit_id": os.environ.get("AUDIT_ID", ""),
        "protected_domain_hits": scope.get("protected_domain_hits", []),
        "requires_c7_check": scope.get("requires_c7_check", False),
        "requires_boundary_guard": scope.get("requires_boundary_guard", False),
        "requires_approval_chain": scope.get("requires_approval_chain", False),
    }
    Path("artifacts/gate").mkdir(parents=True, exist_ok=True)
    Path("artifacts/gate/GuardReport.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

def main() -> int:
    scope_path = Path("artifacts/gate/DiffScope.json")
    if not scope_path.exists():
        return fail("AEF-QW-002", "Missing DiffScope.json")

    scope = json.loads(scope_path.read_text(encoding="utf-8"))

    for k in ("RUN_ID", "TRACE_ID", "AUDIT_ID"):
        if not os.environ.get(k):
            return fail("AEF-QW-002", f"Missing required C-7 env: {k}")

    aef_path = Path("../aef-config/config/governance.yaml")
    if not aef_path.exists():
        return fail("AEF-QW-001", "Missing sibling aef-config governance.yaml")

    cfg = yaml.safe_load(aef_path.read_text(encoding="utf-8")) or {}
    missing = [k for k in REQUIRED_AEF_KEYS if k not in cfg]
    if missing:
        return fail("AEF-QW-001", f"Missing governance keys: {missing}")

    if cfg.get("egress_mode") != "offline":
        return fail("AEF-QW-006", "egress_mode MUST be offline in Phase 0")

    if not isinstance(cfg.get("allowlist"), list):
        return fail("AEF-QW-006", "allowlist MUST be a list")

    protected_hits = scope.get("protected_domain_hits", [])
    if protected_hits and os.environ.get("QW_HUMAN_APPROVAL") != "1":
        return fail("AEF-QW-005", "Protected diff requires QW_HUMAN_APPROVAL=1")

    return ok(scope)

if __name__ == "__main__":
    raise SystemExit(main())
