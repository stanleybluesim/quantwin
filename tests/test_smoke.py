from __future__ import annotations

import os
import sys
import time
import socket
import subprocess
from pathlib import Path

import httpx

from app.schema_validator import validate_or_raise

ROOT = Path(__file__).resolve().parents[1]
TOKEN = os.getenv("QW_API_TOKEN", "devtoken")


def _pick_free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _start_server():
    port = _pick_free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["QW_API_TOKEN"] = TOKEN
    env.setdefault("QW_STORE", "memory")

    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"

    for _ in range(80):
        if p.poll() is not None:
            err = (p.stderr.read() or "")[-4000:]
            out = (p.stdout.read() or "")[-2000:]
            raise RuntimeError("uvicorn exited early.\nSTDERR:\n" + err + "\nSTDOUT:\n" + out)
        try:
            # any HTTP response means server is up
            httpx.get(f"{base}/healthz", timeout=0.2)
            return p, base
        except Exception:
            time.sleep(0.1)

    p.terminate()
    err = (p.stderr.read() or "")[-4000:]
    raise RuntimeError("server did not respond.\nSTDERR:\n" + err)


def test_smoke_contract_endpoints_authorized():
    p, base = _start_server()
    try:
        ingest_body = (ROOT / "contracts/examples/ingest/IngestRequest.example.json").read_text(encoding="utf-8")
        query_body = (ROOT / "contracts/examples/query/QueryRequest.example.json").read_text(encoding="utf-8")
        fuse_body = (ROOT / "contracts/examples/fusion/FusionRequest.example.json").read_text(encoding="utf-8")

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

        r1 = httpx.post(f"{base}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
        assert r1.status_code == 200
        validate_or_raise("ingest/IngestAck.v1.json", r1.json())

        r2 = httpx.post(f"{base}/v1/query", content=query_body, headers=headers, timeout=5.0)
        assert r2.status_code == 200
        validate_or_raise("query/QueryResponse.v1.json", r2.json())

        r3 = httpx.post(f"{base}/v1/fuse", content=fuse_body, headers=headers, timeout=5.0)
        assert r3.status_code == 200
        validate_or_raise("fusion/FusionResult.v1.json", r3.json())
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()


def test_unauthorized_returns_error_envelope():
    p, base = _start_server()
    try:
        query_body = (ROOT / "contracts/examples/query/QueryRequest.example.json").read_text(encoding="utf-8")
        headers = {"Content-Type": "application/json"}  # no Authorization
        r = httpx.post(f"{base}/v1/query", content=query_body, headers=headers, timeout=5.0)
        assert r.status_code == 401
        validate_or_raise("common/ErrorEnvelope.v1.json", r.json())
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()


def test_bad_request_returns_error_envelope():
    p, base = _start_server()
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}
        r = httpx.post(f"{base}/v1/query", json={}, headers=headers, timeout=5.0)
        assert r.status_code == 400
        validate_or_raise("common/ErrorEnvelope.v1.json", r.json())
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()


def test_ingest_idempotency_duplicate():
    p, base = _start_server()
    try:
        ingest_body = (ROOT / "contracts/examples/ingest/IngestRequest.example.json").read_text(encoding="utf-8")
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

        r1 = httpx.post(f"{base}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
        assert r1.status_code == 200
        j1 = r1.json()
        validate_or_raise("ingest/IngestAck.v1.json", j1)
        assert j1["status"] == "ACCEPTED"

        r2 = httpx.post(f"{base}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
        assert r2.status_code == 200
        j2 = r2.json()
        validate_or_raise("ingest/IngestAck.v1.json", j2)
        assert j2["status"] == "DUPLICATE"
        assert j2["doc_id"] == j1["doc_id"]
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()
