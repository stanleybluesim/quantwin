#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

FORBIDDEN_RUNTIME_PATTERNS = [
    r"current\s+live\s+runtime\s+state",
    r"当前生效状态",
    r"直改线上当前生效状态",
    r"直接修改线上当前生效状态",
]

FORBIDDEN_BYPASS_PATTERNS = [
    r"bypass.*POST /v1/policy/publish",
    r"bypass.*POST /v1/policy/rollback",
    r"skip.*approval",
]

NEGATION_HINTS = [
    "must not",
    "forbid",
    "forbidden",
    "blocked",
    "block",
    "禁止",
    "阻断",
    "不得",
    "explicitly blocked",
    "not current live runtime state",
    "not runtime live-state switch asserted",
]

REQUIRED_GATEMATRIX_ANCHORS = [
    "Gate 0",
    "Gate 1",
    "C-7",
    "FastStream",
    "idempotency_key",
    "POST /v1/policy/publish",
    "POST /v1/policy/rollback",
]

REQUIRED_YAML_FIELDS = [
    "trace_id",
    "run_id",
    "audit_id",
    "FastStream",
    "idempotency_key",
]

def fail(code: str, reason: str, findings: list[dict]) -> None:
    findings.append({"code": code, "reason": reason})

def line_is_negated(line: str) -> bool:
    low = line.lower()
    return any(h in low for h in NEGATION_HINTS)

def contains_forbidden(text: str) -> bool:
    for line in text.splitlines():
        line_low = line.lower()
        for pattern in FORBIDDEN_RUNTIME_PATTERNS + FORBIDDEN_BYPASS_PATTERNS:
            if re.search(pattern, line, flags=re.IGNORECASE):
                if line_is_negated(line_low):
                    continue
                return True
    return False

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rules", required=True)
    parser.add_argument("--matrix", required=True)
    args = parser.parse_args()

    findings: list[dict] = []

    rules_path = Path(args.rules)
    matrix_path = Path(args.matrix)

    if not rules_path.exists():
        fail("AEF-QW-005", "Missing rules file", findings)
    if not matrix_path.exists():
        fail("AEF-QW-005", "Missing gate matrix file", findings)

    if findings:
        print(json.dumps({"status": "FAIL", "findings": findings}, ensure_ascii=False, indent=2))
        return 2

    rules_text = rules_path.read_text(encoding="utf-8")
    matrix_text = matrix_path.read_text(encoding="utf-8")
    rules = yaml.safe_load(rules_text)

    for field in REQUIRED_YAML_FIELDS:
        if field not in rules_text:
            fail("AEF-QW-002", f"Missing required anchor: {field}", findings)

    for anchor in REQUIRED_GATEMATRIX_ANCHORS:
        if anchor not in matrix_text:
            fail("AEF-QW-005", f"Missing gate matrix anchor: {anchor}", findings)

    if contains_forbidden(rules_text) or contains_forbidden(matrix_text):
        fail("AEF-QW-003", "Direct live runtime mutation wording detected", findings)

    protected = set(rules.get("protected_domains", []))
    expected = {"auth", "policy", "report", "audit", "sandbox", "deploy"}
    if protected != expected:
        fail("AEF-QW-004", f"Protected domains mismatch: {sorted(protected)}", findings)

    egress = rules.get("egress", {})
    if egress.get("runtime_default_policy") != "offline-first":
        fail("AEF-QW-006", "runtime_default_policy must be offline-first", findings)

    modes = set(egress.get("allowed_modes", []))
    if modes != {"offline", "allowlist"}:
        fail("AEF-QW-006", f"allowed_modes mismatch: {sorted(modes)}", findings)

    boundary = rules.get("boundary_contract", {})
    endpoints = set(boundary.get("runtime_publish_endpoints", []))
    if endpoints != {"POST /v1/policy/publish", "POST /v1/policy/rollback"}:
        fail("AEF-QW-004", "runtime publish endpoints mismatch", findings)

    if boundary.get("async_transport") != "FastStream":
        fail("AEF-QW-004", "FastStream must be the only async transport", findings)

    if boundary.get("idempotency_key_required") is not True:
        fail("AEF-QW-004", "idempotency_key_required must be true", findings)

    if boundary.get("artifact_change_publish_separation") is not True:
        fail("AEF-QW-004", "artifact_change_publish_separation must be true", findings)

    if boundary.get("forbid_direct_live_runtime_state_mutation") is not True:
        fail("AEF-QW-003", "Direct runtime mutation block must be enabled", findings)

    status = "PASS" if not findings else "FAIL"
    print(json.dumps({"status": status, "findings": findings}, ensure_ascii=False, indent=2))
    return 0 if not findings else 2

if __name__ == "__main__":
    sys.exit(main())
