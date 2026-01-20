import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "schemas"
BASE_TOKEN = "devtoken"


def _pick_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    _, port = s.getsockname()
    s.close()
    return int(port)


_SCHEMA_STORE = None

def _build_schema_store():
    store = {}
    for fp in SCHEMAS.rglob("*.json"):
        try:
            doc = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        sid = doc.get("$id")
        if sid:
            store[sid] = doc
    return store


def _validate_schema(rel: str, instance) -> None:
    global _SCHEMA_STORE
    if _SCHEMA_STORE is None:
        _SCHEMA_STORE = _build_schema_store()

    schema_path = (SCHEMAS / rel).resolve()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    resolver = RefResolver(base_uri=f"file://{schema_path}", referrer=schema, store=_SCHEMA_STORE)
    Draft202012Validator(schema, resolver=resolver).validate(instance)

def _start_server(store_path: str | None = None):
    port = _pick_free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["QW_API_TOKEN"] = BASE_TOKEN
    env.setdefault("QW_STORE", "memory")
    if store_path:
        env["QW_STORE_PATH"] = store_path

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
            r = httpx.get(f"{base}/healthz", timeout=0.2)
            if r.status_code == 200:
                return p, base
        except Exception:
            pass
        time.sleep(0.1)

    p.terminate()
    raise RuntimeError("server failed to start")


def _stop_server(p: subprocess.Popen):
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def test_smoke_contract_endpoints_authorized():
    p, base = _start_server()
    try:
        ingest_body = (ROOT / "contracts/examples/ingest/IngestRequest.example.json").read_text(encoding="utf-8")
        query_body = (ROOT / "contracts/examples/query/QueryRequest.example.json").read_text(encoding="utf-8")
        fuse_body = (ROOT / "contracts/examples/fusion/FusionRequest.example.json").read_text(encoding="utf-8")

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BASE_TOKEN}"}

        r1 = httpx.post(f"{base}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
        assert r1.status_code == 200
        _validate_schema("ingest/IngestAck.v1.json", r1.json())

        r2 = httpx.post(f"{base}/v1/query", content=query_body, headers=headers, timeout=5.0)
        assert r2.status_code == 200
        _validate_schema("query/QueryResponse.v1.json", r2.json())

        r3 = httpx.post(f"{base}/v1/fuse", content=fuse_body, headers=headers, timeout=5.0)
        assert r3.status_code == 200
        _validate_schema("fusion/FusionResult.v1.json", r3.json())
    finally:
        _stop_server(p)


def test_unauthorized_returns_error_envelope():
    p, base = _start_server()
    try:
        ingest_body = (ROOT / "contracts/examples/ingest/IngestRequest.example.json").read_text(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        r = httpx.post(f"{base}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
        assert r.status_code == 401
        j = r.json()
        assert "trace_id" in j and "error" in j
        assert "code" in j["error"] and "message" in j["error"]
    finally:
        _stop_server(p)


def test_bad_request_returns_error_envelope():
    p, base = _start_server()
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BASE_TOKEN}"}
        r = httpx.post(f"{base}/v1/query", json={}, headers=headers, timeout=5.0)
        assert r.status_code == 400
        j = r.json()
        assert "trace_id" in j and "error" in j
        assert "code" in j["error"] and "message" in j["error"]
    finally:
        _stop_server(p)


def test_ingest_idempotency_duplicate_persists_across_restart():
    with tempfile.TemporaryDirectory() as td:
        store_path = str(Path(td) / "store.json")

        p1, base1 = _start_server(store_path=store_path)
        try:
            ingest_body = (ROOT / "contracts/examples/ingest/IngestRequest.example.json").read_text(encoding="utf-8")
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BASE_TOKEN}"}

            r1 = httpx.post(f"{base1}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
            assert r1.status_code == 200
            j1 = r1.json()
            _validate_schema("ingest/IngestAck.v1.json", j1)
            assert j1["status"] == "ACCEPTED"
        finally:
            _stop_server(p1)

        p2, base2 = _start_server(store_path=store_path)
        try:
            ingest_body = (ROOT / "contracts/examples/ingest/IngestRequest.example.json").read_text(encoding="utf-8")
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BASE_TOKEN}"}

            r2 = httpx.post(f"{base2}/v1/ingest", content=ingest_body, headers=headers, timeout=5.0)
            assert r2.status_code == 200
            j2 = r2.json()
            _validate_schema("ingest/IngestAck.v1.json", j2)
            assert j2["status"] == "DUPLICATE"
        finally:
            _stop_server(p2)
