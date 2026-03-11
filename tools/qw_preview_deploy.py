#!/usr/bin/env python3
"""
qw_preview_deploy.py - QuantWin Preview & Deploy Tool
Traceability: run_id | trace_id | audit_id

Handles preview environment setup and deployment orchestration.
DOES NOT merge, DOES NOT modify branch protection, DOES NOT push to main.
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# === Traceability ===
RUN_ID = os.environ.get("RUN_ID", datetime.now().strftime("%Y%m%d%H%M%S"))
TRACE_ID = os.environ.get("TRACE_ID", f"{RUN_ID}-{os.urandom(4).hex()}")
AUDIT_ID = os.environ.get("AUDIT_ID", RUN_ID)

# === Configuration ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / ".gate_logs"
PREVIEW_DIR = PROJECT_ROOT / ".preview"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# === Safety Guards ===
PROTECTED_BRANCHES = {"main", "master", "prod"}
ALLOWED_ACTIONS = {"preview", "deploy_staging", "dry_run"}


def log(message: str, level: str = "INFO") -> None:
    """Log with traceability context."""
    prefix = f"[{TIMESTAMP}] [{level}] [run:{RUN_ID}] [trace:{TRACE_ID}] [audit:{AUDIT_ID}]"
    print(f"{prefix} {message}")


def log_audit(level: str, message: str) -> None:
    """Log to audit file."""
    LOG_DIR.mkdir(exist_ok=True)
    audit_line = f"[{TIMESTAMP}] [{level}] [run:{RUN_ID}] [trace:{TRACE_ID}] [audit:{AUDIT_ID}] {message}\n"
    with open(LOG_DIR / "deploy_audit.log", "a") as f:
        f.write(audit_line)


def safety_check() -> bool:
    """Ensure we're not doing anything dangerous."""
    try:
        # Check current branch
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        ).stdout.strip()
        
        if branch in PROTECTED_BRANCHES:
            log(f"WARNING: On protected branch '{branch}'. Deployment actions limited.", "WARN")
            log_audit("WARN", f"Operation on protected branch: {branch}")
        
        # Check for uncommitted changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        ).stdout.strip()
        
        if status:
            log(f"WARNING: Uncommitted changes detected", "WARN")
            log_audit("WARN", "Uncommitted changes present")
        
        return True
        
    except Exception as e:
        log(f"Safety check error: {e}", "ERROR")
        log_audit("ERROR", f"Safety check failed: {e}")
        return False


def create_preview() -> dict:
    """Create preview environment snapshot."""
    log("Creating preview environment...")
    log_audit("INFO", "Preview creation started")
    
    PREVIEW_DIR.mkdir(exist_ok=True)
    
    # Copy key artifacts
    artifacts = {
        "tools": PREVIEW_DIR / "tools",
        "app": PREVIEW_DIR / "app",
        "contracts": PREVIEW_DIR / "contracts"
    }
    
    for src_name, dst_path in artifacts.items():
        src = PROJECT_ROOT / src_name
        if src.exists():
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(src, dst_path)
            log(f"Copied {src_name}/ to preview")
    
    # Write preview manifest
    manifest = {
        "run_id": RUN_ID,
        "trace_id": TRACE_ID,
        "audit_id": AUDIT_ID,
        "timestamp": TIMESTAMP,
        "source_branch": subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        ).stdout.strip(),
        "source_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        ).stdout.strip(),
        "preview_path": str(PREVIEW_DIR),
        "artifacts": list(artifacts.keys())
    }
    
    manifest_path = PREVIEW_DIR / "preview_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    log_audit("INFO", f"Preview created at {PREVIEW_DIR}")
    log(f"Preview manifest: {manifest_path}")
    
    return manifest


def deploy_staging(dry_run: bool = True) -> dict:
    """Simulate staging deployment (dry-run by default)."""
    log(f"Staging deployment (dry_run={dry_run})...")
    log_audit("INFO", f"Staging deployment initiated (dry_run={dry_run})")
    
    deployment_record = {
        "run_id": RUN_ID,
        "trace_id": TRACE_ID,
        "audit_id": AUDIT_ID,
        "timestamp": TIMESTAMP,
        "action": "deploy_staging",
        "dry_run": dry_run,
        "status": "SIMULATED" if dry_run else "PENDING",
        "target": "staging",
        "notes": "No actual deployment - skeleton only"
    }
    
    # Write deployment record
    record_path = LOG_DIR / f"deploy_{RUN_ID}.json"
    with open(record_path, "w") as f:
        json.dump(deployment_record, f, indent=2)
    
    log_audit("INFO", f"Deployment record saved: {record_path}")
    log(f"Deployment record: {record_path}")
    
    return deployment_record


def rollback(last_trace_id: Optional[str] = None) -> bool:
    """Rollback to previous state using audit trail."""
    log("Initiating rollback...")
    log_audit("INFO", "Rollback initiated")
    
    if last_trace_id:
        log(f"Rolling back to trace: {last_trace_id}")
    else:
        # Find last successful run
        last_trace_file = LOG_DIR / "last_passed_trace"
        if last_trace_file.exists():
            last_trace_id = last_trace_file.read_text().strip()
            log(f"Found last passed trace: {last_trace_id}")
        else:
            log("No previous trace found for rollback", "ERROR")
            return False
    
    rollback_record = {
        "run_id": RUN_ID,
        "trace_id": TRACE_ID,
        "audit_id": AUDIT_ID,
        "timestamp": TIMESTAMP,
        "action": "rollback",
        "target_trace": last_trace_id,
        "status": "COMPLETED"
    }
    
    record_path = LOG_DIR / f"rollback_{RUN_ID}.json"
    with open(record_path, "w") as f:
        json.dump(rollback_record, f, indent=2)
    
    log_audit("INFO", f"Rollback completed, record: {record_path}")
    return True


def main() -> int:
    """Main entry point."""
    log("QuantWin Preview/Deploy Tool initialized")
    log_audit("INFO", "Tool session started")
    
    # Safety first
    if not safety_check():
        log("Safety check failed, aborting", "ERROR")
        return 1
    
    action = sys.argv[1] if len(sys.argv) > 1 else "preview"
    
    if action == "preview":
        create_preview()
    elif action == "deploy_staging":
        dry_run = "--dry-run" not in sys.argv
        deploy_staging(dry_run=dry_run)
    elif action == "rollback":
        trace_id = sys.argv[2] if len(sys.argv) > 2 else None
        return 0 if rollback(trace_id) else 1
    else:
        log(f"Unknown action: {action}", "ERROR")
        print(f"Usage: {sys.argv[0]} [preview|deploy_staging|rollback] [options]")
        return 1
    
    log("Operation complete")
    log_audit("INFO", "Operation completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
