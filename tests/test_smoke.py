import subprocess
import time
import httpx

from app.schema_validator import validate_or_raise

BASE = "http://127.0.0.1:8000"
TOKEN = "devtoken"

def _wait_ready(timeout_sec: float = 8.0) -> None:
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            r = httpx.get(f"{BASE}/healthz", timeout=1.0)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError("server not ready")

def _start_server():
    p = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    _wait_ready()
    return p

def test_smoke_contract_endpoints_authorized():
    p = _start_server()
    try:
        ingest_body = open("contracts/examples/ingest/IngestRequest.example.json", "r", encoding="utf-8").read()
        query_body = open("contracts/examples/query/QueryRequest.example.json", "r", encoding="utf-8").read()
        fuse_body = open("contracts/examples/fusion/FusionRequest.example.json", "r", encoding="utf-8").read()

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

        r1 = httpx.post(f"{BASE}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
        assert r1.status_code == 200

        r2 = httpx.post(f"{BASE}/v1/query", content=query_body, headers=headers, timeout=5.0)
        assert r2.status_code == 200

        r3 = httpx.post(f"{BASE}/v1/fuse", content=fuse_body, headers=headers, timeout=5.0)
        assert r3.status_code == 200
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()

def test_unauthorized_returns_error_envelope():
    p = _start_server()
    try:
        ingest_body = open("contracts/examples/ingest/IngestRequest.example.json", "r", encoding="utf-8").read()
        headers = {"Content-Type": "application/json"}  # no Authorization

        r = httpx.post(f"{BASE}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
        assert r.status_code == 401
        payload = r.json()
        validate_or_raise("common/ErrorEnvelope.v1.json", payload)
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()

def test_bad_request_returns_error_envelope():
    p = _start_server()
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}
        # 缺少必填字段，触发 RequestValidationError -> 400
        r = httpx.post(f"{BASE}/v1/query", json={}, headers=headers, timeout=5.0)
        assert r.status_code == 400
        payload = r.json()
        validate_or_raise("common/ErrorEnvelope.v1.json", payload)
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()
