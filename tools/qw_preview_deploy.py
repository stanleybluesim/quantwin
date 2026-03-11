#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tarfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DELIVERY_DIR = REPO_ROOT / "artifacts" / "delivery"

DEFAULT_INCLUDE = [
    ".github/workflows/dev-gate.yml",
    "tools/qw_gate.sh",
    "tools/qw_review_grok.py",
    "tools/qw_preview_deploy.py",
    "requirements-dev.txt",
    ".ruff.toml",
    "contracts/openapi/openapi.yaml",
    "README.md",
]

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def existing_files() -> list[Path]:
    files: list[Path] = []
    for rel in DEFAULT_INCLUDE:
        p = REPO_ROOT / rel
        if p.exists() and p.is_file():
            files.append(p)
    return files

def build_bundle(bundle_path: Path, files: list[Path]) -> None:
    with tarfile.open(bundle_path, "w:gz") as tar:
        for p in files:
            tar.add(p, arcname=str(p.relative_to(REPO_ROOT)))

def write_summary(summary_path: Path, manifest: dict) -> None:
    lines = [
        "# Preview Summary",
        "",
        f"- generated_at: {manifest['generated_at']}",
        f"- task_id: {manifest['task_id']}",
        f"- run_id: {manifest['run_id']}",
        f"- trace_id: {manifest['trace_id']}",
        f"- audit_id: {manifest['audit_id']}",
        f"- preview_type: {manifest['preview_type']}",
        f"- status: {manifest['status']}",
        f"- bundle_path: {manifest['bundle_path']}",
        "",
        "## Included Files",
    ]
    for item in manifest["included_files"]:
        lines.append(f"- {item}")
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task_id", default="preview_deploy")
    parser.add_argument("--run_id", default=f"run_{uuid.uuid4().hex[:12]}")
    parser.add_argument("--trace_id", default=uuid.uuid4().hex)
    parser.add_argument("--audit_id", default=f"aud_{uuid.uuid4().hex[:12]}")
    parser.add_argument("--preview_type", default="artifact_download")
    args = parser.parse_args()

    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)

    files = existing_files()
    bundle_name = f"preview_bundle_{args.run_id}.tgz"
    bundle_path = DELIVERY_DIR / bundle_name

    status = "READY" if files else "DEGRADED"
    if files:
        build_bundle(bundle_path, files)

    manifest = {
        "generated_at": utc_now(),
        "task_id": args.task_id,
        "run_id": args.run_id,
        "trace_id": args.trace_id,
        "audit_id": args.audit_id,
        "preview_type": args.preview_type,
        "status": status,
        "bundle_path": str(bundle_path.relative_to(REPO_ROOT)) if bundle_path.exists() else None,
        "included_files": [str(p.relative_to(REPO_ROOT)) for p in files],
        "notes": [
            "Preview is delivered as downloadable artifact bundle.",
            "Status READY means at least one preview file was packaged.",
            "Status DEGRADED means no eligible preview files were found.",
        ],
    }

    manifest_path = DELIVERY_DIR / "PreviewManifest.json"
    summary_path = DELIVERY_DIR / "PreviewSummary.md"

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(summary_path, manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
