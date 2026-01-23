import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
from fastapi.testclient import TestClient

# Robust app import (repo variations)
app = None
try:
    from app.main import app as _app  # type: ignore
    app = _app
except Exception:
    try:
        from app import app as _app  # type: ignore
        app = _app
    except Exception as e:
        raise RuntimeError("Cannot import FastAPI app. Expected app.main:app or app:app") from e


def _auth_headers() -> Dict[str, str]:
    tok = os.getenv("QW_TEST_BEARER_TOKEN", "").strip()
    if not tok:
        return {}
    return {"Authorization": f"Bearer {tok}"}


def _load_json(fp: Path) -> Dict[str, Any]:
    return json.loads(fp.read_text(encoding="utf-8"))


def _find_example(keywords: List[str]) -> Optional[Path]:
    root = Path("contracts")
    if not root.exists():
        return None
    cands = list(root.rglob("*.json"))
    kws = [k.lower() for k in keywords]
    for p in cands:
        name = str(p).lower()
        if all(k in name for k in kws):
            return p
    return None


def _discover_ops() -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    spec = app.openapi()
    paths = spec.get("paths", {}) or {}

    ingest_ops: List[Tuple[str, str]] = []
    query_ops: List[Tuple[str, str]] = []

    def is_json_request(op: Dict[str, Any]) -> bool:
        rb = op.get("requestBody") or {}
        content = rb.get("content") or {}
        return "application/json" in content

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        p_low = str(path).lower()
        for m, op in methods.items():
            if m.lower() not in ("post", "put", "patch", "get"):
                continue
            if not isinstance(op, dict):
                continue

            # skip docs endpoints
            if any(x in p_low for x in ("/docs", "/openapi", "/redoc")):
                continue

            op_low = (op.get("operationId") or "").lower()

            # ingest-ish
            if any(k in p_low for k in ("ingest", "index", "upsert", "document", "docs")) or "ingest" in op_low:
                if m.lower() in ("post", "put", "patch") and is_json_request(op):
                    ingest_ops.append((m.upper(), path))

            # query/search-ish
            if any(k in p_low for k in ("query", "search", "retrieve")) or any(k in op_low for k in ("query", "search")):
                if m.lower() in ("post", "get") and (is_json_request(op) or m.lower() == "get"):
                    query_ops.append((m.upper(), path))

    # stable order to make debugging deterministic
    ingest_ops = list(dict.fromkeys(ingest_ops))
    query_ops = list(dict.fromkeys(query_ops))
    return ingest_ops, query_ops


def _request_with_fallback(
    client: TestClient,
    ops: List[Tuple[str, str]],
    payload: Dict[str, Any],
    phase: str,
) -> Dict[str, Any]:
    tried: List[Tuple[str, str, int]] = []

    for method, path in ops[:20]:
        r = client.request(method, path, headers=_auth_headers(), json=payload)
        tried.append((method, path, r.status_code))

        # discovery mismatch: keep trying
        if r.status_code in (404, 405, 422):
            continue

        # auth required: treat as expected-xfail (CI has no secrets)
        if r.status_code == 401:
            pytest.xfail(
                f"{phase} requires bearer auth. Set env QW_TEST_BEARER_TOKEN to a valid dev token "
                f"(non-secret) for strict local pass, or implement a test-mode auth bypass."
            )

        assert r.status_code < 400, f"{phase} failed: {method} {path} => {r.status_code} {r.text}"

        # best-effort json parse
        try:
            return r.json()
        except Exception:
            return {"_raw": r.text}

    detail = "; ".join([f"{m} {p}={c}" for m, p, c in tried])
    pytest.fail(f"{phase} endpoint not found (all candidates 404/405/422). tried: {detail}")


@pytest.mark.e2e
def test_golden_thread_ingest_then_query_evidence_list_non_empty():
    client = TestClient(app)

    ingest_ops, query_ops = _discover_ops()
    assert ingest_ops, "cannot discover ingest endpoint from app.openapi()"
    assert query_ops, "cannot discover query/search endpoint from app.openapi()"

    ingest_ex = _find_example(["ingest", "request"])
    query_ex = _find_example(["query", "request"]) or _find_example(["search", "request"])

    ingest_payload = _load_json(ingest_ex) if ingest_ex else {"doc_id": "doc-1", "text": "hello quantwin"}
    query_payload = _load_json(query_ex) if query_ex else {"query": "hello"}

    _request_with_fallback(client, ingest_ops, ingest_payload, phase="ingest")
    data = _request_with_fallback(client, query_ops, query_payload, phase="query")

    ev = data.get("evidence_list")
    assert isinstance(ev, list) and len(ev) >= 1, "expected non-empty evidence_list in query response"
