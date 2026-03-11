#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
REVIEW_DIR = REPO_ROOT / "artifacts" / "review"
DELIVERY_DIR = REPO_ROOT / "artifacts" / "delivery"

Status = Literal["PASS", "WARN", "FAIL"]

@dataclass
class ReviewCheck:
    name: str
    status: Status
    detail: str

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()

def changed_files(base_ref: str) -> list[str]:
    out = run_git(["diff", "--name-only", f"{base_ref}...HEAD"])
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]

def load_preview_manifest() -> dict | None:
    manifest = DELIVERY_DIR / "PreviewManifest.json"
    if not manifest.exists():
        return None
    try:
        return json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return None

def build_checks(base_ref: str, files: list[str], preview_manifest: dict | None) -> list[ReviewCheck]:
    checks: list[ReviewCheck] = []

    if files:
        checks.append(
            ReviewCheck(
                name="changed_files_detected",
                status="PASS",
                detail=f"Detected {len(files)} changed file(s) against {base_ref}.",
            )
        )
    else:
        checks.append(
            ReviewCheck(
                name="changed_files_detected",
                status="WARN",
                detail=f"No changed files detected against {base_ref}.",
            )
        )

    preview_status = "MISSING"
    if preview_manifest:
        preview_status = preview_manifest.get("status", "UNKNOWN")

    if preview_manifest and preview_status == "READY":
        checks.append(
            ReviewCheck(
                name="preview_manifest_ready",
                status="PASS",
                detail="Preview manifest exists and status is READY.",
            )
        )
    elif preview_manifest:
        checks.append(
            ReviewCheck(
                name="preview_manifest_ready",
                status="WARN",
                detail=f"Preview manifest exists but status is {preview_status}.",
            )
        )
    else:
        checks.append(
            ReviewCheck(
                name="preview_manifest_ready",
                status="WARN",
                detail="Preview manifest not found in artifacts/delivery/PreviewManifest.json.",
            )
        )

    risky = [f for f in files if f.startswith(".github/workflows/")]
    if risky:
        checks.append(
            ReviewCheck(
                name="workflow_change_scope",
                status="WARN",
                detail="Workflow files changed; verify CI behavior and permissions explicitly.",
            )
        )
    else:
        checks.append(
            ReviewCheck(
                name="workflow_change_scope",
                status="PASS",
                detail="No workflow file changes detected.",
            )
        )

    return checks

def derive_status(checks: list[ReviewCheck]) -> Status:
    statuses = {c.status for c in checks}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"

def recommendations(files: list[str], preview_manifest: dict | None) -> list[str]:
    recs: list[str] = []
    if any(f.startswith(".github/workflows/") for f in files):
        recs.append("Re-check branch protection and required checks after workflow changes.")
    if preview_manifest is None:
        recs.append("Persist PreviewManifest.json as CI artifact input for downstream review consumers.")
    if not recs:
        recs.append("No blocking review findings in local-rule-review mode.")
    return recs

def write_summary(path: Path, report: dict) -> None:
    lines = [
        "# Review Summary",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- task_id: {report['task_id']}",
        f"- run_id: {report['run_id']}",
        f"- trace_id: {report['trace_id']}",
        f"- audit_id: {report['audit_id']}",
        f"- provider: {report['provider']}",
        f"- review_mode: {report['review_mode']}",
        f"- overall_status: {report['overall_status']}",
        "",
        "## Checks",
    ]
    for item in report["checks"]:
        lines.append(f"- {item['name']}: {item['status']} — {item['detail']}")
    lines.append("")
    lines.append("## Recommendations")
    for item in report["recommendations"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task_id", default="review_grok")
    parser.add_argument("--run_id", default=f"run_{uuid.uuid4().hex[:12]}")
    parser.add_argument("--trace_id", default=uuid.uuid4().hex)
    parser.add_argument("--audit_id", default=f"aud_{uuid.uuid4().hex[:12]}")
    parser.add_argument("--base_ref", default="origin/main")
    parser.add_argument("--provider", default="local-rule-review")
    parser.add_argument("--review_mode", default="offline")
    args = parser.parse_args()

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    files = changed_files(args.base_ref)
    preview_manifest = load_preview_manifest()
    checks = build_checks(args.base_ref, files, preview_manifest)
    overall_status = derive_status(checks)

    report = {
        "generated_at": utc_now(),
        "task_id": args.task_id,
        "run_id": args.run_id,
        "trace_id": args.trace_id,
        "audit_id": args.audit_id,
        "provider": args.provider,
        "review_mode": args.review_mode,
        "base_ref": args.base_ref,
        "overall_status": overall_status,
        "changed_files": files,
        "checks": [asdict(c) for c in checks],
        "recommendations": recommendations(files, preview_manifest),
    }

    report_path = REVIEW_DIR / "ReviewReport.json"
    summary_path = REVIEW_DIR / "ReviewSummary.md"

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(summary_path, report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
