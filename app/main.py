from __future__ import annotations

import hashlib
import json
import os
import secrets
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schema_validator import validate_or_raise


app = FastAPI(title="QuantWin Mock API", version="0.1.0")


def _expected_token() -> str:
    return os.environ.get("QW_API_TOKEN", "dev-token")


def _authorized(request: Request) -> bool:
    h = request.headers.get("authorization") or request.headers.get("Authorization") or ""
    if not h.lower().startswith("bearer "):
        return False
    token = h.split(" ", 1)[1].strip()
    return token == _expected_token()


def _new_trace(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(8)}"


def _error_envelope(status_code: int, code: str, message: str, trace_id: str, details: Optional[Dict[str, Any]] = None):
    payload: Dict[str, Any] = {
        "trace_id": trace_id,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        payload["error"]["details"] = details
    try:
        validate_or_raise("common/ErrorEnvelope.v1.json", payload)
    except Exception:
        pass
    return JSONResponse(status_code=status_code, content=payload)


def _make_valid(schema_path: str, preferred: Dict[str, Any]) -> Dict[str, Any]:
    validate_or_raise(schema_path, preferred)
    return preferred


@app.exception_handler(RequestValidationError)
async def _req_validation_handler(request: Request, exc: RequestValidationError):
    trace_id = _new_trace("tr_400")
    return _error_envelope(400, "BAD_REQUEST", "request validation failed", trace_id, {"reason": str(exc)})


@app.exception_handler(Exception)
async def _unhandled_exc_handler(request: Request, exc: Exception):
    trace_id = _new_trace("tr_500")
    return _error_envelope(500, "INTERNAL_ERROR", str(exc), trace_id)


_seen_ingest: set[str] = set()


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/v1/ingest")
async def ingest(request: Request, payload: Dict[str, Any] = Body(...)):
    trace_id = _new_trace("tr_ingest")

    if not _authorized(request):
        return _error_envelope(401, "UNAUTHORIZED", "missing or invalid bearer token", trace_id)

    try:
        validate_or_raise("ingest/IngestRequest.v1.json", payload)
    except Exception as e:
        return _error_envelope(400, "BAD_REQUEST", "request schema validation failed", trace_id, {"reason": str(e)})

    key = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    status = "DUPLICATE" if key in _seen_ingest else "ACCEPTED"
    _seen_ingest.add(key)

    doc_id = payload.get("doc_id") or payload.get("document_id") or "doc_001"
    resp = _make_valid("ingest/IngestAck.v1.json", {"trace_id": trace_id, "doc_id": doc_id, "status": status})
    return JSONResponse(status_code=200, content=resp)


@app.post("/v1/query")
async def query(request: Request, payload: Dict[str, Any] = Body(...)):
    trace_id = _new_trace("tr_query")

    if not _authorized(request):
        return _error_envelope(401, "UNAUTHORIZED", "missing or invalid bearer token", trace_id)

    try:
        validate_or_raise("query/QueryRequest.v1.json", payload)
    except Exception as e:
        return _error_envelope(400, "BAD_REQUEST", "request schema validation failed", trace_id, {"reason": str(e)})

    preferred = {
        "trace_id": trace_id,
        "answer": "Mock answer.",
        "evidence_list": [
            {"evidence_id": "ev_001", "source": "internal.docs", "snippet": "A", "score": 0.8},
            {"evidence_id": "ev_002", "source": "internal.runbook", "snippet": "B", "score": 0.7},
        ],
        "recommendation_card": {
            "risk_level": "MEDIUM",
            "summary": "Mock recommendation.",
            "actions": ["action_1"],
            "evidence_refs": ["ev_001", "ev_002"],
        },
    }
    resp = _make_valid("query/QueryResponse.v1.json", preferred)
    return JSONResponse(status_code=200, content=resp)


@app.post("/v1/fuse")
async def fuse(request: Request, payload: Dict[str, Any] = Body(...)):
    trace_id = _new_trace("tr_fuse")

    if not _authorized(request):
        return _error_envelope(401, "UNAUTHORIZED", "missing or invalid bearer token", trace_id)

    try:
        validate_or_raise("fusion/FusionRequest.v1.json", payload)
    except Exception as e:
        return _error_envelope(400, "BAD_REQUEST", "request schema validation failed", trace_id, {"reason": str(e)})

    preferred = {
        "trace_id": trace_id,
        "fused_summary": "Mock fused summary.",
        "used_evidence_ids": ["ev_001", "ev_002"],
        "results_by_source": {"internal.docs": ["ev_001"], "internal.runbook": ["ev_002"]},
    }
    resp = _make_valid("fusion/FusionResult.v1.json", preferred)
    return JSONResponse(status_code=200, content=resp)
