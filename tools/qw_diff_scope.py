#!/usr/bin/env python3
import argparse
import json
import os
import subprocess

PROTECTED_FILE_MAP = {
    "app/auth.py": "auth",
}

GOVERNANCE_CRITICAL = {
    ".github/workflows/ci.yml",
    ".github/workflows/dev-gate.yml",
    ".github/workflows/auto-merge-on-green.yml",
    "tools/qw_gate.sh",
    "scripts/validate_openapi.sh",
    "scripts/validate_schemas.sh",
    "docs/traceability/RTM.md",
}

C7_CRITICAL = {
    "contracts/schemas/common/ErrorEnvelope.v1.json",
    "app/error_envelope.py",
    "app/main.py",
}

def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{p.stderr}")
    return p.stdout.strip()

def resolve_base(base_ref: str) -> str:
    try:
        run(["git", "rev-parse", "--verify", base_ref])
        return base_ref
    except Exception:
        return "HEAD~1"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--head-ref", default="HEAD")
    args = ap.parse_args()

    base_ref = resolve_base(args.base_ref)
    head_ref = args.head_ref

    try:
        merge_base = run(["git", "merge-base", base_ref, head_ref])
    except Exception:
        merge_base = base_ref

    out = run(["git", "diff", "--name-only", merge_base, head_ref])
    changed_files = [x.strip() for x in out.splitlines() if x.strip()]

    protected_domain_hits = sorted({PROTECTED_FILE_MAP[p] for p in changed_files if p in PROTECTED_FILE_MAP})
    governance_critical_hits = sorted([p for p in changed_files if p in GOVERNANCE_CRITICAL])
    c7_hits = sorted([p for p in changed_files if p in C7_CRITICAL])

    scope = {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "merge_base": merge_base,
        "changed_files": changed_files,
        "protected_domain_hits": protected_domain_hits,
        "governance_critical_hits": governance_critical_hits,
        "requires_c7_check": bool(protected_domain_hits or c7_hits),
        "requires_boundary_guard": bool(protected_domain_hits),
        "requires_approval_chain": bool(protected_domain_hits),
    }

    os.makedirs("artifacts/gate", exist_ok=True)
    with open("artifacts/gate/DiffScope.json", "w", encoding="utf-8") as f:
        json.dump(scope, f, ensure_ascii=False, indent=2)

    print(json.dumps(scope, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
