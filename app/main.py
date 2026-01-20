from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

from app.schema_validator import validate_or_raise
from app.auth import is_public, is_protected, valid_bearer
from app.error_envelope import error_response

app = FastAPI(title="QuantWin API", version="0.1.0")


@app.middleware("http")
async def auth_guard(request: Request, call_next):
    if is_public(request):
        return await call_next(request)

    if is_protected(request) and not valid_bearer(request):
        return error_response(
            request,
            status_code=401,
            code="UNAUTHORIZED",
            message="Missing or invalid bearer token",
        )

    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = "HTTP_ERROR"
    if exc.status_code == 400:
        code = "BAD_REQUEST"
    elif exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code >= 500:
        code = "INTERNAL_ERROR"

    return error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=str(exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    # FastAPI 默认是 422。为了与你 OpenAPI 里的 400 ErrorEnvelope 对齐，这里映射成 400。
    return error_response(
        request,
        status_code=400,
        code="BAD_REQUEST",
        message="Request validation failed",
        details={"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return error_response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="Unhandled server error",
        details={"error": str(exc)},
    )


@app.get("/healthz")
def healthz():
    return {"ok": True}


# ---- Pydantic models (mock endpoints) ----
class IngestContent(BaseModel):
    mime_type: str = Field(min_length=1)
    text: Optional[str] = None
    url: Optional[str] = None

class IngestRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    received_at: str = Field(min_length=1)
    content: IngestContent

class IngestAck(BaseModel):
    trace_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    status: Literal["ACCEPTED", "DUPLICATE", "REJECTED"]

class QueryRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    top_k: int = 10
    lang: Literal["zh", "en"] = "zh"

class EvidenceItem(BaseModel):
    evidence_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    snippet: str = Field(min_length=1)
    score: float

class RecommendationCard(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    summary: str = Field(min_length=1)
    actions: List[str] = []
    evidence_refs: List[str] = []

class QueryResponse(BaseModel):
    trace_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    evidence_list: List[EvidenceItem]
    recommendation_card: Optional[RecommendationCard] = None

class FusionEvidence(BaseModel):
    evidence_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    snippet: str = Field(min_length=1)
    score: float

class FusionRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    mode: Literal["STRICT", "BALANCED", "FAST"] = "BALANCED"
    max_evidence: int = 10
    evidence_list: List[FusionEvidence]

class FusionResult(BaseModel):
    trace_id: str = Field(min_length=1)
    fused_summary: str = Field(min_length=1)
    used_evidence_ids: List[str]
    results_by_source: Dict[str, List[str]] = {}


def _validate_response(schema_rel_path: str, payload: dict):
    try:
        validate_or_raise(schema_rel_path, payload)
        return payload
    except Exception as e:
        return error_response(
            None,
            status_code=500,
            code="CONTRACT_VIOLATION",
            message="Response schema validation failed",
            details={"schema": schema_rel_path, "error": str(e)},
        )


@app.post("/v1/ingest", response_model=IngestAck)
def ingest(req: IngestRequest):
    payload = {"trace_id": "tr_ingest_001", "doc_id": "doc_001", "status": "ACCEPTED"}
    return _validate_response("ingest/IngestAck.v1.json", payload)


@app.post("/v1/query", response_model=QueryResponse)
def query(req: QueryRequest):
    payload = {
        "trace_id": "tr_query_001",
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
    return _validate_response("query/QueryResponse.v1.json", payload)


@app.post("/v1/fuse", response_model=FusionResult)
def fuse(req: FusionRequest):
    used = [e.evidence_id for e in req.evidence_list[: req.max_evidence]]
    by_source: Dict[str, List[str]] = {}
    for e in req.evidence_list:
        by_source.setdefault(e.source, []).append(e.evidence_id)

    payload = {
        "trace_id": "tr_fuse_001",
        "fused_summary": "Mock fused summary.",
        "used_evidence_ids": used,
        "results_by_source": by_source,
    }
    return _validate_response("fusion/FusionResult.v1.json", payload)
