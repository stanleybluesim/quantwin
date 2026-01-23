import os
import re
from typing import Any, Dict, List, Optional, Tuple

import pytest
from fastapi.testclient import TestClient

# -------- import app (keep fallback to avoid brittle import paths) --------
try:
    from app.main import app  # type: ignore
except Exception:
    try:
        from app.app import app  # type: ignore
    except Exception as e:
        raise RuntimeError("cannot import FastAPI app (tried app.main/app.app)") from e


def _auth_headers() -> Dict[str, str]:
    tok = (os.getenv("QW_TEST_BEARER_TOKEN") or "").strip()
    if not tok:
        tok = (os.getenv("QW_BEARER_TOKEN") or "").strip()
    return {"Authorization": f"Bearer {tok}"} if tok else {}


def _openapi() -> Dict[str, Any]:
    spec = app.openapi()
    assert isinstance(spec, dict) and "paths" in spec, "app.openapi() did not return a valid OpenAPI dict"
    return spec


def _is_http_method(k: str) -> bool:
    return k.lower() in {"get", "post", "put", "patch", "delete"}


def _discover_ops() -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    spec = _openapi()
    paths = spec.get("paths", {}) or {}
    ingest_ops: List[Tuple[str, str]] = []
    query_ops: List[Tuple[str, str]] = []

    ingest_pats = [r"\bingest\b", r"\bindex\b", r"\bupsert\b"]
    query_pats = [r"\bquery\b", r"\bsearch\b", r"\bretrieve\b"]

    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if not _is_http_method(method) or not isinstance(op, dict):
                continue
            blob = (path + " " + str(op.get("operationId", "")) + " " + " ".join(op.get("tags", []) or [])).lower()
            if any(re.search(p, blob) for p in ingest_pats):
                ingest_ops.append((method.upper(), path))
            if any(re.search(p, blob) for p in query_pats):
                query_ops.append((method.upper(), path))

    # de-dup, stable
    def uniq(xs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        seen = set()
        out = []
        for x in xs:
            if x not in seen:
                out.append(x)
                seen.add(x)
        return out

    return uniq(ingest_ops), uniq(query_ops)


def _resolve_ref(spec: Dict[str, Any], ref: str) -> Dict[str, Any]:
    assert ref.startswith("#/"), f"unexpected ref: {ref}"
    node: Any = spec
    for part in ref[2:].split("/"):
        node = node[part]
    assert isinstance(node, dict)
    return node


def _schema_example(spec: Dict[str, Any], schema: Optional[Dict[str, Any]], depth: int = 0) -> Any:
    if schema is None:
        return {}
    if depth > 8:
        return {}
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "$ref" in schema:
        return _schema_example(spec, _resolve_ref(spec, schema["$ref"]), depth + 1)

    t = schema.get("type")
    if t == "object" or "properties" in schema:
        props = schema.get("properties", {}) or {}
        req = schema.get("required", []) or []
        obj: Dict[str, Any] = {}
        for k in req:
            if k in props:
                obj[k] = _schema_example(spec, props[k], depth + 1)
        # if no required fields, include 1st property to avoid empty payload 422
        if not obj and props:
            k = next(iter(props.keys()))
            obj[k] = _schema_example(spec, props[k], depth + 1)
        return obj

    if t == "array":
        items = schema.get("items", {}) or {}
        ex = _schema_example(spec, items, depth + 1)
        return [ex] if ex != {} else []

    if t == "string":
        enum = schema.get("enum")
        if enum:
            return enum[0]
        fmt = schema.get("format", "")
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        return "string"

    if t == "integer":
        return 0
    if t == "number":
        return 0
    if t == "boolean":
        return False

    return {}


def _request_schema(spec: Dict[str, Any], method: str, path: str) -> Optional[Dict[str, Any]]:
    op = spec["paths"][path][method.lower()]
    rb = op.get("requestBody", {}) or {}
    content = rb.get("content", {}) or {}
    # prefer JSON
    for ct in ("application/json", "application/*+json"):
        if ct in content and isinstance(content[ct], dict) and "schema" in content[ct]:
            return content[ct]["schema"]
    # any json-like
    for ct, v in content.items():
        if "json" in ct and isinstance(v, dict) and "schema" in v:
            return v["schema"]
    return None


def _request_with_fallback(
    client: TestClient,
    ops: List[Tuple[str, str]],
    phase: str,
) -> Tuple[str, str, Any]:
    spec = _openapi()
    tried: List[Tuple[str, str, int]] = []

    for method, path in ops[:20]:
        schema = _request_schema(spec, method, path)
        payload = _schema_example(spec, schema)
        r = client.request(method, path, headers=_auth_headers(), json=payload)
        tried.append((method, path, r.status_code))

        if r.status_code == 404:
            continue

        if r.status_code == 401:
            pytest.xfail(
                f"{phase} requires bearer auth and current token is not accepted. "
                f"Set env QW_TEST_BEARER_TOKEN to a valid dev token for strict local pass."
            )

        assert r.status_code < 400, f"{phase} failed: {method} {path} => {r.status_code} {r.text}"
        return method, path, r.json() if "application/json" in (r.headers.get("content-type") or "") else None

    detail = "; ".join([f"{m} {p}={c}" for m, p, c in tried])
    pytest.fail(f"{phase} endpoint not found (all candidates returned 404). tried: {detail}")


@pytest.mark.e2e
def test_golden_thread_ingest_then_query_evidence_list_non_empty():
    client = TestClient(app)

    ingest_ops, query_ops = _discover_ops()
    assert ingest_ops, "cannot discover ingest endpoint from app.openapi()"
    assert query_ops, "cannot discover query/search endpoint from app.openapi()"

    _request_with_fallback(client, ingest_ops, phase="ingest")
    _, _, data = _request_with_fallback(client, query_ops, phase="query")

    assert isinstance(data, dict), "query did not return JSON object"
    ev = data.get("evidence_list")
    assert isinstance(ev, list) and len(ev) >= 1, "expected non-empty evidence_list in query response"
