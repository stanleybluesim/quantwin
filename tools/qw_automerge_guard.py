#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
ART_DIR = REPO_ROOT / "artifacts" / "automerge"

Decision = Literal["MERGED", "BLOCKED", "SKIPPED", "ERROR"]

@dataclass
class CheckEvaluation:
    name: str
    status: str
    detail: str

class GitHubApiError(RuntimeError):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"GitHub API {status_code}: {body}")

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
        f"- pr_number: {report['pr_number']}",
        f"- decision: {report['decision']}",
        f"- merge_method: {report['merge_method']}",
        f"- merge_sha: {report['merge_sha']}",
        f"- deleted_branch: {report['deleted_branch']}",
        "",
        "## Required Checks",
    ]
    for item in report["required_checks"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Check Evaluation")
    for item in report["check_evaluation"]:
        lines.append(f"- {item['name']}: {item['status']} — {item['detail']}")
    lines.append("")
    lines.append("## Notes")
    for item in report["notes"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def persist(report: dict) -> None:
    ART_DIR.mkdir(parents=True, exist_ok=True)
    (ART_DIR / "AutoMergeReport.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_summary(ART_DIR / "AutoMergeSummary.md", report)

def api_request(
    method: str,
    url: str,
    token: str,
    payload: dict | None = None,
) -> dict | list | None:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if payload is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            if not body:
                return None
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise GitHubApiError(e.code, body) from e

def parse_event(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def get_pr(repo: str, pr_number: int, token: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    return api_request("GET", url, token)  # type: ignore[return-value]

def get_check_runs(repo: str, sha: str, token: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/commits/{sha}/check-runs?per_page=100"
    data = api_request("GET", url, token)  # type: ignore[assignment]
    assert isinstance(data, dict)
    return data.get("check_runs", [])

def merge_pr(repo: str, pr_number: int, head_sha: str, merge_method: str, token: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/merge"
    payload = {
        "sha": head_sha,
        "merge_method": merge_method,
    }
    data = api_request("PUT", url, token, payload)  # type: ignore[assignment]
    assert isinstance(data, dict)
    return data

def delete_branch_ref(repo: str, branch_name: str, token: str) -> None:
    encoded = urllib.parse.quote(f"heads/{branch_name}", safe="")
    url = f"https://api.github.com/repos/{repo}/git/refs/{encoded}"
    api_request("DELETE", url, token)

def evaluate_checks(required: list[str], runs: list[dict]) -> tuple[list[CheckEvaluation], list[str]]:
    grouped: dict[str, list[dict]] = {}
    for run in runs:
        name = str(run.get("name", ""))
        if name in required:
            grouped.setdefault(name, []).append(run)

    evaluations: list[CheckEvaluation] = []
    failed_checks: list[str] = []

    for name in required:
        items = grouped.get(name, [])
        if not items:
            evaluations.append(CheckEvaluation(name=name, status="MISSING", detail="Required check not found on head SHA."))
            failed_checks.append(name)
            continue

        statuses = [str(x.get("status")) for x in items]
        conclusions = [str(x.get("conclusion")) for x in items]

        if any(s != "completed" for s in statuses):
            evaluations.append(CheckEvaluation(name=name, status="PENDING", detail=f"statuses={statuses}, conclusions={conclusions}"))
            failed_checks.append(name)
            continue

        bad = [c for c in conclusions if c != "success"]
        if bad:
            evaluations.append(CheckEvaluation(name=name, status="FAILED", detail=f"statuses={statuses}, conclusions={conclusions}"))
            failed_checks.append(name)
            continue

        evaluations.append(CheckEvaluation(name=name, status="PASS", detail=f"all matched runs succeeded; count={len(items)}"))

    return evaluations, failed_checks

def build_report(args, repo: str) -> dict:
    return {
        "generated_at": utc_now(),
        "task_id": "auto_merge_guard",
        "run_id": f"run_{uuid.uuid4().hex[:12]}",
        "trace_id": uuid.uuid4().hex,
        "audit_id": f"aud_{uuid.uuid4().hex[:12]}",
        "mode": args.mode,
        "repo": repo,
        "base_ref": args.base_ref,
        "required_checks": args.required_check,
        "decision": "SKIPPED",
        "pr_number": None,
        "head_sha": None,
        "merge_sha": None,
        "deleted_branch": False,
        "merge_method": args.merge_method,
        "failed_checks": [],
        "check_evaluation": [],
        "notes": [],
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry-run", "workflow-run"], default="dry-run")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--event-path", default="")
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--merge-method", choices=["merge", "squash", "rebase"], default="merge")
    parser.add_argument("--delete-branch", action="store_true")
    parser.add_argument("--required-check", action="append", default=[])
    parser.add_argument("--poll-attempts", type=int, default=4)
    parser.add_argument("--poll-interval-sec", type=int, default=3)
    args = parser.parse_args()

    if not args.required_check:
        args.required_check = ["contract-check", "gate", "preview", "review"]

    report = build_report(args, args.repo)

    if args.mode == "dry-run":
        report["decision"] = "SKIPPED"
        report["notes"] = [
            "Local dry-run only.",
            "workflow-run MUST require base_ref=main.",
            "workflow-run MUST block on missing/pending/failed required checks.",
            "workflow-run SHOULD delete branch after successful merge when configured.",
        ]
        persist(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    token = (
        Path("/proc/self/environ").exists() and None
    )
    token = token  # keep linter quiet
    import os
    gh_token = os.environ.get("GITHUB_TOKEN", "")
    if not gh_token:
        report["decision"] = "ERROR"
        report["notes"] = ["Missing GITHUB_TOKEN in environment."]
        persist(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    if not args.event_path:
        report["decision"] = "ERROR"
        report["notes"] = ["workflow-run mode requires --event-path."]
        persist(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    try:
        event = parse_event(args.event_path)
        wr = event.get("workflow_run", {})
        pulls = wr.get("pull_requests") or []

        if wr.get("event") != "pull_request":
            report["decision"] = "SKIPPED"
            report["notes"] = [f"workflow_run.event={wr.get('event')} is not pull_request."]
            persist(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        if not pulls:
            report["decision"] = "SKIPPED"
            report["notes"] = ["No pull_requests attached to workflow_run."]
            persist(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        pr_number = int(pulls[0]["number"])
        report["pr_number"] = pr_number

        pr = None
        for _ in range(args.poll_attempts):
            pr = get_pr(args.repo, pr_number, gh_token)
            if pr.get("mergeable") is not None:
                break
            time.sleep(args.poll_interval_sec)

        assert pr is not None

        state = pr.get("state")
        draft = bool(pr.get("draft"))
        base_ref = (pr.get("base") or {}).get("ref")
        head_sha = (pr.get("head") or {}).get("sha")
        head_ref = (pr.get("head") or {}).get("ref")
        head_repo = ((pr.get("head") or {}).get("repo") or {}).get("full_name")
        base_repo = ((pr.get("base") or {}).get("repo") or {}).get("full_name")

        report["head_sha"] = head_sha

        notes: list[str] = []

        if state != "open":
            report["decision"] = "SKIPPED"
            notes.append(f"PR state={state}, not open.")
            report["notes"] = notes
            persist(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        if draft:
            report["decision"] = "BLOCKED"
            notes.append("PR is draft.")
            report["notes"] = notes
            persist(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        if base_ref != args.base_ref:
            report["decision"] = "SKIPPED"
            notes.append(f"PR base_ref={base_ref}, expected {args.base_ref}.")
            report["notes"] = notes
            persist(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        if head_repo != base_repo:
            report["decision"] = "SKIPPED"
            notes.append(f"head repo {head_repo} != base repo {base_repo}; same-repo only.")
            report["notes"] = notes
            persist(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        runs = get_check_runs(args.repo, head_sha, gh_token)
        evaluations, failed_checks = evaluate_checks(args.required_check, runs)
        report["check_evaluation"] = [asdict(x) for x in evaluations]
        report["failed_checks"] = failed_checks

        if failed_checks:
            report["decision"] = "BLOCKED"
            notes.append("At least one required check is not PASS.")
            report["notes"] = notes
            persist(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        merge_result = merge_pr(args.repo, pr_number, head_sha, args.merge_method, gh_token)
        report["decision"] = "MERGED"
        report["merge_sha"] = merge_result.get("sha")
        notes.append("PR merged successfully.")

        if args.delete_branch and head_ref:
            try:
                delete_branch_ref(args.repo, head_ref, gh_token)
                report["deleted_branch"] = True
                notes.append(f"Deleted branch: {head_ref}")
            except GitHubApiError as e:
                notes.append(f"Branch delete failed after merge: {e}")
        report["notes"] = notes
        persist(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    except GitHubApiError as e:
        report["decision"] = "ERROR"
        report["notes"] = [str(e)]
        persist(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    except Exception as e:
        report["decision"] = "ERROR"
        report["notes"] = [repr(e)]
        persist(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
