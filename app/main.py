from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

app = FastAPI(title="QuantWin API", version="0.1.0")

@app.get("/healthz")
def healthz():
    return {"ok": True}

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

@app.post("/v1/ingest", response_model=IngestAck)
def ingest(req: IngestRequest):
    return IngestAck(trace_id="tr_ingest_001", doc_id="doc_001", status="ACCEPTED")

@app.post("/v1/query", response_model=QueryResponse)
def query(req: QueryRequest):
    ev = [
        EvidenceItem(evidence_id="ev_001", source="internal.docs", snippet="A", score=0.8),
        EvidenceItem(evidence_id="ev_002", source="internal.runbook", snippet="B", score=0.7),
    ]
    card = RecommendationCard(
        risk_level="MEDIUM",
        summary="Mock recommendation.",
        actions=["action_1"],
        evidence_refs=["ev_001", "ev_002"],
    )
    return QueryResponse(trace_id="tr_query_001", answer="Mock answer.", evidence_list=ev, recommendation_card=card)

@app.post("/v1/fuse", response_model=FusionResult)
def fuse(req: FusionRequest):
    used = [e.evidence_id for e in req.evidence_list[: req.max_evidence]]
    by_source: Dict[str, List[str]] = {}
    for e in req.evidence_list:
        by_source.setdefault(e.source, []).append(e.evidence_id)
    return FusionResult(
        trace_id="tr_fuse_001",
        fused_summary="Mock fused summary.",
        used_evidence_ids=used,
        results_by_source=by_source,
    )
