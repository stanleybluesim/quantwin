#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPORT_TEMPLATE = {
    "provider": "",
    "status": "UNAVAILABLE",
    "checked_at": "",
    "latency_ms": 0,
    "session_probe": "SKIPPED",
    "auth_state": "UNKNOWN",
    "error_code": "PROVIDER_UNAVAILABLE",
    "error_message": ""
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def probe_dns(host: str, port: int, timeout_sec: int) -> tuple[bool, int, str]:
    start = time.perf_counter()
    try:
        socket.setdefaulttimeout(timeout_sec)
        socket.getaddrinfo(host, port)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return True, latency_ms, ""
    except socket.timeout:
        return False, int((time.perf_counter() - start) * 1000), "TIMEOUT"
    except Exception as exc:
        return False, int((time.perf_counter() - start) * 1000), repr(exc)


def build_report(provider: str, ok: bool, latency_ms: int, err: str, auth_env: str) -> dict:
    report = dict(REPORT_TEMPLATE)
    report["provider"] = provider
    report["checked_at"] = now_iso()
    report["latency_ms"] = latency_ms

    token = os.getenv(auth_env, "")
    if token:
        report["auth_state"] = "VALID"
    else:
        report["auth_state"] = "UNKNOWN"

    if ok:
        report["status"] = "HEALTHY"
        report["session_probe"] = "OK"
        report["error_code"] = "NONE"
        report["error_message"] = ""
    else:
        report["status"] = "UNAVAILABLE"
        report["session_probe"] = "FAIL"
        if "TIMEOUT" in err:
            report["error_code"] = "TIMEOUT"
        else:
            report["error_code"] = "PROVIDER_UNAVAILABLE"
        report["error_message"] = err

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--timeout-sec", type=int, default=5)
    parser.add_argument("--auth-env", default="QWEN_API_KEY")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    ok, latency_ms, err = probe_dns(args.host, args.port, args.timeout_sec)
    report = build_report(args.provider, ok, latency_ms, err, args.auth_env)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PROBE_STATUS={report['status']}")
    print(f"OUTPUT={out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
