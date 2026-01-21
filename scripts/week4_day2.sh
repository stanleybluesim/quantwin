#!/usr/bin/env bash
set -euo pipefail

# WEEK4_DAY2_IDEMPOTENT_GUARD
# This script overwrites files. Use only on a clean branch.

cd "$(git rev-parse --show-toplevel)"

python - <<'PY'
from pathlib import Path
from datetime import datetime

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(path: str):
    p = Path(path)
    if p.exists():
        bak = p.with_suffix(p.suffix + f".bak.{ts}")
        bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        print("BACKUP:", bak)

backup("app/store/memory.py")
backup("app/main.py")

Path("app/store/memory.py").write_text(
"""from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from app.store.base import Document, Evidence


class InMemoryDocStore:
    def __init__(self, persist_path: Optional[str] = None) -> None:
        self._docs: Dict[str, Document] = {}
        self._idem: Dict[Tuple[str, str, str], str] = {}  # (tenant_id, source_id, content_hash) -> doc_id
        self._persist_path = Path(persist_path).expanduser() if persist_path else None
        if self._persist_path:
            self._load()

    def _load(self) -> None:
        try:
            if not self._persist_path or not self._persist_path.exists():
                return
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            docs = data.get("docs", {})
            self._docs.clear()
            for doc_id, d in docs.items():
                self._docs[doc_id] = Document(**d)
            self._idem.clear()
            for doc_id, doc in self._docs.items():
                if doc.content_hash:
                    self._idem[(doc.tenant_id, doc.source_id, doc.content_hash)] = doc_id
        except Exception:
            self._docs = {}
            self._idem = {}

    def _save(self) -> None:
        if not self._persist_path:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._persist_path.with_suffix(self._persist_path.suffix + ".tmp")
        payload = {"docs": {doc_id: asdict(doc) for doc_id, doc in self._docs.items()}}
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
        os.replace(tmp, self._persist_path)

    def find_by_idempotency(self, tenant_id: str, source_id: str, content_hash: str) -> Optional[str]:
        return self._idem.get((tenant_id, source_id, content_hash))

    def upsert(self, doc: Document) -> str:
        doc_id = doc.doc_id
        self._docs[doc_id] = doc
        if doc.content_hash:
            self._idem[(doc.tenant_id, doc.source_id, doc.content_hash)] = doc_id
        self._save()
        return doc_id

    def get(self, doc_id: str) -> Optional[Document]:
        return self._docs.get(doc_id)

    def search(self, tenant_id: str, query: str, top_k: int) -> List[Evidence]:
        q = (query or "").strip().lower()
        if not q:
            return []
        terms = [t for t in q.replace("\\n", " ").split(" ") if t]
        scored: List[tuple[float, Evidence]] = []

        for doc in self._docs.values():
            if doc.tenant_id != tenant_id:
                continue
            text = (doc.text or "").lower()
            if not text:
                continue
            hits = 0
            for t in terms:
                if t and t in text:
                    hits += text.count(t)
            if hits <= 0:
                continue
            score = min(1.0, hits / 10.0)
            snippet = (doc.text or "")[:200]
            ev = Evidence(
                evidence_id=f"ev_{doc.doc_id}",
                source=doc.source_id,
                snippet=snippet,
                score=score,
                doc_id=doc.doc_id,
            )
            scored.append((score, ev))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ev for _, ev in scored[: max(1, int(top_k))]]
""",
    encoding="utf-8",
)

Path("app/main.py").write_text(
"""from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator, RefResolver

from app.store.base import Document, DocStore
from app.store.memory import InMemoryDocStore


app = FastAPI(title="QuantWin Mock API", version="0.1.0")

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "schemas"

_SCHEMA_STORE: Optional[Dict[str, Any]] = None


def _build_schema_store() -> Dict[str, Any]:
    store: Dict[str, Any] = {}
    for fp in SCHEMAS.rglob("*.json"):
        try:
            doc = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        sid = doc.get("$id")
        if sid:
            store[sid] = doc
    return store


def _load_schema(rel: str) -> Dict[str, Any]:
    path = (SCHEMAS / rel).resolve()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_or_raise(rel: str, instance: Any) -> None:
    global _SCHEMA_STORE
    if _SCHEMA_STORE is None:
        _SCHEMA_STORE = _build_schema_store()
    schema = _load_schema(rel)
    base = (SCHEMAS / rel).resolve()
    resolver = RefResolver(base_uri=f"file://{base}", referrer=schema, store=_SCHEMA_STORE)
    Draft202012Validator(schema, resolver=resolver).validate(instance)


def _new_trace(prefix: str) -> str:
    return f"{prefix}_{os.urandom(8).hex()}"


def _authorized(request: Request) -> bool:
    token = os.getenv("QW_API_TOKEN", "")
    if not token:
        return True
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {token}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
                    [{"evidence_id": "ev_001", "source": "internal.docs", "snippet": "A", "score": 0.8, "doc_id": "doc_001"}],
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
    payload: Dict[str, Any] = {"trace_id": trace_id, "error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(Exception)
async def _unhandled_exc_handler(request: Request, exc: Exception):
    trace_id = _new_trace("tr_err")
    return _error_envelope(500, "INTERNAL_ERROR", str(exc), trace_id)


def _canonical_hash(payload: Dict[str, Any]) -> str:
    b = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _get_tenant_id(payload: Dict[str, Any], request: Request) -> str:
    return str(payload.get("tenant_id") or request.headers.get("X-Tenant-Id") or "tenant_default")


def _get_source_id(payload: Dict[str, Any], request: Request) -> str:
    return str(payload.get("source_id") or request.headers.get("X-Source-Id") or "source_default")


def _get_store() -> DocStore:
    store_kind = os.getenv("QW_STORE", "memory").strip().lower()
    if store_kind == "memory":
        persist_path = os.getenv("QW_STORE_PATH") or None
        return InMemoryDocStore(persist_path=persist_path)
    return InMemoryDocStore(persist_path=None)


STORE: DocStore = _get_store()


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

    tenant_id = _get_tenant_id(payload, request)
    source_id = _get_source_id(payload, request)

    content_hash = payload.get("content_hash")
    if not isinstance(content_hash, str) or not content_hash:
        content_hash = _canonical_hash(payload)

    existing = STORE.find_by_idempotency(tenant_id, source_id, content_hash)
    if existing:
        resp = _make_valid("ingest/IngestAck.v1.json", {"trace_id": trace_id, "doc_id": existing, "status": "DUPLICATE"})
        return JSONResponse(status_code=200, content=resp)

    doc_id = payload.get("doc_id") or payload.get("document_id") or f"doc_{content_hash[:12]}"
    text = payload.get("text") or payload.get("content") or payload.get("raw_text") or ""
    mime_type = payload.get("mime_type") or "text/plain"
    url = payload.get("url")

    doc = Document(
        doc_id=str(doc_id),
        tenant_id=str(tenant_id),
        source_id=str(source_id),
        received_at=_now_iso(),
        mime_type=str(mime_type),
        text=str(text) if text is not None else None,
        url=str(url) if url is not None else None,
        content_hash=str(content_hash),
    )
    STORE.upsert(doc)

    resp = _make_valid("ingest/IngestAck.v1.json", {"trace_id": trace_id, "doc_id": doc.doc_id, "status": "ACCEPTED"})
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

    tenant_id = _get_tenant_id(payload, request)
    q = payload.get("query") or payload.get("question") or payload.get("q") or ""
    top_k = payload.get("top_k") or payload.get("k") or 5
    try:
        top_k_int = int(top_k)
    except Exception:
        top_k_int = 5

    evs = STORE.search(str(tenant_id), str(q), max(1, top_k_int))
    evidence_list: List[Dict[str, Any]] = [
        {"evidence_id": e.evidence_id, "source": e.source, "snippet": e.snippet, "score": e.score, "doc_id": e.doc_id}
        for e in evs
    ]
    ev_refs = [e["evidence_id"] for e in evidence_list]

    preferred = {
        "trace_id": trace_id,
        "answer": "Mock answer.",
        "evidence_list": evidence_list if evidence_list else [{"evidence_id": "ev_001", "source": "internal.docs", "snippet": "A", "score": 0.8, "doc_id": "doc_001"}],
        "recommendation_card": {
            "risk_level": "MEDIUM",
            "summary": "Mock recommendation.",
            "actions": ["action_1"],
            "evidence_refs": ev_refs if ev_refs else ["ev_001"],
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
        "used_evidence_ids": payload.get("used_evidence_ids") or ["ev_001"],
        "results_by_source": payload.get("results_by_source") or {"internal.docs": ["ev_001"]},
    }
    resp = _make_valid("fusion/FusionResult.v1.json", preferred)
    return JSONResponse(status_code=200, content=resp)
""",
    encoding="utf-8",
)

print("OK: wrote app/store/memory.py and app/main.py")
PY

python -m py_compile app/main.py app/store/memory.py

if [ -x scripts/preflight.sh ]; then
  ./scripts/preflight.sh
else
  bash scripts/validate_openapi.sh
  bash scripts/validate_schemas.sh
  python -m pytest -q
fi

echo "OK: week4_day2 complete"
