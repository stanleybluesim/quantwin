#!/usr/bin/env python3
"""
qw_review_grok.py - QuantWin Code Review Grok Tool
Traceability: run_id | trace_id | audit_id

Performs automated code review analysis with audit trail.
"""

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# === Traceability ===
RUN_ID = os.environ.get("RUN_ID", datetime.now().strftime("%Y%m%d%H%M%S"))
TRACE_ID = os.environ.get("TRACE_ID", f"{RUN_ID}-{os.urandom(4).hex()}")
AUDIT_ID = os.environ.get("AUDIT_ID", RUN_ID)

# === Configuration ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / ".gate_logs"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message: str, level: str = "INFO") -> None:
    """Log with traceability context."""
    prefix = f"[{TIMESTAMP}] [{level}] [run:{RUN_ID}] [trace:{TRACE_ID}] [audit:{AUDIT_ID}]"
    print(f"{prefix} {message}")


def log_audit(level: str, message: str) -> None:
    """Log to audit file."""
    LOG_DIR.mkdir(exist_ok=True)
    audit_line = f"[{TIMESTAMP}] [{level}] [run:{RUN_ID}] [trace:{TRACE_ID}] [audit:{AUDIT_ID}] {message}\n"
    with open(LOG_DIR / "review_audit.log", "a") as f:
        f.write(audit_line)


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file for audit trail."""
    if not filepath.exists():
        return "MISSING"
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def get_git_status() -> dict:
    """Get current git status for context."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "changed_files": result.stdout.strip().split("\n") if result.stdout.strip() else [],
            "branch": subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=10
            ).stdout.strip()
        }
    except Exception as e:
        log(f"Git status error: {e}", "WARN")
        return {"changed_files": [], "branch": "unknown"}


def review_python_files() -> list:
    """Review Python files for common issues."""
    issues = []
    py_files = list(PROJECT_ROOT.glob("**/*.py"))
    
    for py_file in py_files:
        if "venv" in str(py_file) or ".git" in str(py_file):
            continue
        
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
                
                # Check for TODO/FIXME without trace_id
                for i, line in enumerate(lines, 1):
                    if "TODO" in line or "FIXME" in line:
                        if "trace_id" not in line.lower() and "run_id" not in line.lower():
                            issues.append({
                                "file": str(py_file.relative_to(PROJECT_ROOT)),
                                "line": i,
                                "type": "traceability",
                                "message": "TODO/FIXME without traceability reference"
                            })
        except Exception as e:
            log(f"Error reviewing {py_file}: {e}", "WARN")
    
    return issues


def generate_review_report(issues: list) -> dict:
    """Generate structured review report."""
    return {
        "run_id": RUN_ID,
        "trace_id": TRACE_ID,
        "audit_id": AUDIT_ID,
        "timestamp": TIMESTAMP,
        "project_root": str(PROJECT_ROOT),
        "git_context": get_git_status(),
        "issues": issues,
        "issue_count": len(issues),
        "status": "PASS" if len(issues) == 0 else "REVIEW_NEEDED"
    }


def main() -> int:
    """Main review entry point."""
    log("Starting code review grok...")
    log_audit("INFO", "Review session initialized")
    
    try:
        issues = review_python_files()
        report = generate_review_report(issues)
        
        # Save report
        report_path = LOG_DIR / f"review_{RUN_ID}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        log(f"Review complete: {len(issues)} issues found")
        log_audit("INFO", f"Review complete: {len(issues)} issues, report saved to {report_path}")
        
        # Output summary
        print("\n=== Review Summary ===")
        print(f"Run ID: {RUN_ID}")
        print(f"Trace ID: {TRACE_ID}")
        print(f"Audit ID: {AUDIT_ID}")
        print(f"Issues: {len(issues)}")
        print(f"Report: {report_path}")
        
        if issues:
            print("\n=== Issues ===")
            for issue in issues[:10]:  # Show first 10
                print(f"  [{issue['type']}] {issue['file']}:{issue['line']} - {issue['message']}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")
        
        return 0 if len(issues) == 0 else 1
        
    except Exception as e:
        log(f"Review failed: {e}", "ERROR")
        log_audit("ERROR", f"Review failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
