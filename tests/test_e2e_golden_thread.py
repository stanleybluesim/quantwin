import os
import json
from pathlib import Path

import yaml
from fastapi.testclient import TestClient
from jsonschema import validate as js_validate


# Try to keep auth stable across envs
os.environ.setdefault("API_TOKEN", "dev-token")
os.environ.setdefault("QW_API_TOKEN", "dev-token")


def _load_openapi() -> dict:
    p = Path("contracts/openapi/openapi.yaml")
    assert p.exists(), "missing contracts/openapi/openapi.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _find_op_by_request_ref(spec: dict, needle: str):
    needle = needle.lower()
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            rb = (op or {}).get("requestBody") or {}
            content = (rb.get("content") or {}).get("application/json") or {}
            schema = content.get("schema") or {}
            blob = json.dumps(schema, ensure_ascii=False).lower()
            if needle in blob:
                return path, method.lower()
    return None, None


def _load_json(path: str) -> dict:
    p = Path(path)
    assert p.exists(), f"missing {path}"
    return json.loads(p.read_text(encoding="utf-8"))


def _auth_headers():
    tok = os.environ.get("QW_API_TOKEN") or os.environ.get("API_TOKEN") or ""
    if tok:
        return {"Authorization": f"Bearer {tok}"}
    return {}


def test_p0_golden_thread_ingest_then_query():
    # Import app after env defaults
    from app.main import app  # noqa

    spec = _load_openapi()

    ingest_path, ingest_method = _find_op_by_request_ref(spec, "IngestRequest")
    query_path, query_method = _find_op_by_request_ref(spec, "QueryRequest")

    assert ingest_path and ingest_method, "cannot find ingest operation by IngestRequest ref"
    assert query_path and query_method, "cannot find query operation by QueryRequest ref"

    client = TestClient(app)
    headers = _auth_headers()

    ingest_body = _load_json("contracts/examples/ingest/IngestRequest.example.json")
    query_body = _load_json("contracts/examples/query/QueryRequest.example.json")

    # 1) ingest
    r1 = client.request(ingest_method.upper(), ingest_path, json=ingest_body, headers=headers)
    if r1.status_code in (401, 403) and headers:
        # If runner uses different auth config, retry once without auth
        r1 = client.request(ingest_method.upper(), ingest_path, json=ingest_body)
    assert r1.status_code == 200, f"ingest failed: {r1.status_code} {r1.text}"

    # 2) query
    r2 = client.request(query_method.upper(), query_path, json=query_body, headers=headers)
    if r2.status_code in (401, 403) and headers:
        r2 = client.request(query_method.upper(), query_path, json=query_body)
    assert r2.status_code == 200, f"query failed: {r2.status_code} {r2.text}"

    data = r2.json()

    # Validate response against schema if available
    schema_path = Path("contracts/schemas/query/QueryResponse.v1.json")
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        js_validate(instance=data, schema=schema)

    # Basic sanity: evidence_list expected non-empty in this project
    ev = data.get("evidence_list")
    assert isinstance(ev, list) and len(ev) >= 1, "expected non-empty evidence_list in query response"
