#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ART_DIR = REPO_ROOT / "artifacts" / "automerge"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_summary(path: Path, report: dict) -> None:
    lines = [
        "# Auto Merge Summary",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- mode: {report['mode']}",
        f"- repo: {report['repo']}",
        f"- base_ref: {report['base_ref']}",
        f"- decision: {report['decision']}",
        "",
        "## Required Checks",
    ]
    for item in report["required_checks"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Notes")
    for item in report["notes"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--mode", default="dry-run")
    parser.add_argument("--required-check", action="append", default=[])
    args = parser.parse_args()

    required = args.required_check or ["contract-check", "gate", "preview", "review"]

    report = {
        "generated_at": utc_now(),
        "task_id": "auto_merge_guard",
        "run_id": f"run_{uuid.uuid4().hex[:12]}",
        "trace_id": uuid.uuid4().hex,
        "audit_id": f"aud_{uuid.uuid4().hex[:12]}",
        "mode": args.mode,
        "repo": args.repo,
        "base_ref": args.base_ref,
        "required_checks": required,
        "decision": "SKIPPED",
        "notes": [
            "Local dry-run only.",
            "Future workflow mode MUST require base_ref=main.",
            "Future workflow mode MUST hold on missing/pending/failed checks.",
            "Future workflow mode SHOULD delete branch after successful merge.",
        ],
    }

    ART_DIR.mkdir(parents=True, exist_ok=True)
    (ART_DIR / "AutoMergeReport.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_summary(ART_DIR / "AutoMergeSummary.md", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
