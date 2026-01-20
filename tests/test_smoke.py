import subprocess
import time
import httpx

BASE = "http://127.0.0.1:8000"

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

def test_smoke_contract_endpoints():
    p = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_ready()

        ingest_body = open("contracts/examples/ingest/IngestRequest.example.json", "r", encoding="utf-8").read()
        query_body = open("contracts/examples/query/QueryRequest.example.json", "r", encoding="utf-8").read()
        fuse_body = open("contracts/examples/fusion/FusionRequest.example.json", "r", encoding="utf-8").read()

        headers = {"Content-Type": "application/json"}

        r1 = httpx.post(f"{BASE}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
        assert r1.status_code == 200
        j1 = r1.json()
        assert "trace_id" in j1 and "doc_id" in j1 and "status" in j1

        r2 = httpx.post(f"{BASE}/v1/query", content=query_body, headers=headers, timeout=5.0)
        assert r2.status_code == 200
        j2 = r2.json()
        assert "trace_id" in j2 and "answer" in j2 and "evidence_list" in j2

        r3 = httpx.post(f"{BASE}/v1/fuse", content=fuse_body, headers=headers, timeout=5.0)
        assert r3.status_code == 200
        j3 = r3.json()
        assert "trace_id" in j3 and "fused_summary" in j3 and "used_evidence_ids" in j3

    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()
