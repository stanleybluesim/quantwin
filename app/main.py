from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator, RefResolver

from app.store.base import Document, DocStore
from app.store.memory import InMemoryDocStore


app = FastAPI(title="QuantWin Mock API", version="0.1.0")

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "schemas"


def _load_schema(rel: str) -> Dict[str, Any]:
    path = (SCHEMAS / rel).resolve()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_or_raise(rel: str, instance: Any) -> None:
    schema = _load_schema(rel)
    base = (SCHEMAS / rel).resolve()
    resolver = RefResolver(base_uri=f"file://{base}", referrer=schema)
    Draft202012Validator(schema, resolver=resolver).validate(instance)


def _new_trace(prefix: str) -> str:
    rnd = os.urandom(8).hex()
    return f"{prefix}_{rnd}"


def _authorized(request: Request) -> bool:
    token = os.getenv("QW_API_TOKEN", "")
    if not token:
        return True
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {token}"


def _make_valid(schema_rel: str, preferred: Dict[str, Any]) -> Dict[str, Any]:
    candidates = [preferred]

    if schema_rel.endswith("ingest/IngestAck.v1.json"):
        candidates.append(
            {
                "trace_id": preferred.get("trace_id", _new_trace("tr_ingest")),
                "doc_id": preferred.get("doc_id", "doc_001"),
                "status": preferred.get("status", "ACCEPTED"),
            }
        )

    if schema_rel.endswith("query/QueryResponse.v1.json"):
        candidates.append(
            {
                "trace_id": preferred.get("trace_id", _new_trace("tr_query")),
                "answer": preferred.get("answer", "Mock answer."),
                "evidence_list": preferred.get(
                    "evidence_list",
                    [{"evidence_id": "ev_001", "source": "internal.docs", "snippet": "A", "score": 0.8}],
                ),
                "recommendation_card": preferred.get(
                    "recommendation_card",
                    {"risk_level": "MEDIUM", "summary": "Mock recommendation.", "actions": ["action_1"], "evidence_refs": ["ev_001"]},
                ),
            }
        )

    if schema_rel.endswith("fusion/FusionResult.v1.json"):
        candidates.append(
            {
                "trace_id": preferred.get("trace_id", _new_trace("tr_fuse")),
                "fused_summary": preferred.get("fused_summary", "Mock fused summary."),
                "used_evidence_ids": preferred.get("used_evidence_ids", ["ev_001"]),
                "results_by_source": preferred.get("results_by_source", {"internal.docs": ["ev_001"]}),
            }
        )

    for c in candidates:
        try:
            validate_or_raise(schema_rel, c)
            return c
        except Exception:
            continue
    return preferred


def _error_envelope(status_code: int, code: str, message: str, trace_id: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    payload = {"trace_id": trace_id, "error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details

    # 可选：如果你有 ErrorEnvelope schema，可以在这里校验；没有也不影响测试
    return JSONResponse(status_code=status_code, content=payload)


def _build_store() -> DocStore:
    kind = os.getenv("QW_STORE", "memory").lower()
    if kind in ("memory", "mem", "inmemory"):
        return InMemoryDocStore(persist_path=os.getenv("QW_STORE_PATH"))
    return InMemoryDocStore(persist_path=os.getenv("QW_STORE_PATH"))


STORE: DocStore = _build_store()


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

    tenant_id = str(payload.get("tenant_id") or "tenant_001")
    source_id = str(payload.get("source_id") or "source_001")
    content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    existing = STORE.find_by_idempotency(tenant_id, source_id, content_hash)
    if existing:
        doc_id = existing
        status = "DUPLICATE"
    else:
        doc_id = str(payload.get("doc_id") or payload.get("document_id") or "doc_001")
        received_at = str(payload.get("received_at") or datetime.now(timezone.utc).isoformat())
        mime_type = str(payload.get("mime_type") or "application/json")

        doc = Document(
            doc_id=doc_id,
            tenant_id=tenant_id,
            source_id=source_id,
            received_at=received_at,
            mime_type=mime_type,
            text=payload.get("text"),
            url=payload.get("url"),
            content_hash=content_hash,
        )
        STORE.upsert(doc)
        status = "ACCEPTED"

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
