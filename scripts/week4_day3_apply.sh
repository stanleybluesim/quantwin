#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if [ "${CONFIRM_OVERWRITE:-}" != "YES" ]; then
  echo "ABORT: this script overwrites app/*.py"
  echo "To proceed: CONFIRM_OVERWRITE=YES bash scripts/week4_day3_apply.sh"
  exit 1
fi


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
        if not terms:
            return []

        scored: List[tuple[float, Evidence]] = []

        for doc in self._docs.values():
            if doc.tenant_id != tenant_id:
                continue
            text = (doc.text or "").lower()
            if not text:
                continue

            hit = 0
            for t in terms:
                if t in text:
                    hit += 1
            if hit == 0:
                continue

            score = min(1.0, hit / max(1.0, len(terms)))
            raw = doc.text or ""
            snippet = raw[:160].strip() if raw else ""
            evidence_id = f"ev_{doc.doc_id}"

            scored.append(
                (
                    score,
                    Evidence(
                        evidence_id=evidence_id,
                        source=doc.source_id or "internal",
                        snippet=snippet or "N/A",
                        score=score,
                        doc_id=doc.doc_id,
                    ),
                )
            )

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[: max(1, int(top_k or 5))]]
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
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
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


def _get_store() -> DocStore:
    kind = (os.getenv("QW_STORE") or "memory").strip().lower()
    if kind == "memory":
        persist = os.getenv("QW_STORE_PATH")  # 可选：比如 ./var/store.json
        return InMemoryDocStore(persist_path=persist)
    return InMemoryDocStore()


STORE: DocStore = _get_store()


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
    payload: Dict[str, Any] = {"trace_id": trace_id, "error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def _request_validation_handler(request: Request, exc: RequestValidationError):
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

    tenant_id = payload.get("tenant_id") or "t_default"
    source_id = payload.get("source_id") or "s_default"
    text = payload.get("text") or payload.get("content") or ""
    url = payload.get("url")
    mime_type = payload.get("mime_type") or "text/plain"
    received_at = payload.get("received_at") or _now_iso()

    raw_for_hash = text or (url or json.dumps(payload, ensure_ascii=False, sort_keys=True))
    content_hash = hashlib.sha256(raw_for_hash.encode("utf-8")).hexdigest()

    existing = STORE.find_by_idempotency(tenant_id, source_id, content_hash)
    if existing:
        status = "DUPLICATE"
        doc_id = existing
    else:
        status = "ACCEPTED"
        doc_id = payload.get("doc_id") or payload.get("document_id") or f"doc_{os.urandom(4).hex()}"
        doc = Document(
            doc_id=doc_id,
            tenant_id=tenant_id,
            source_id=source_id,
            received_at=received_at,
            mime_type=mime_type,
            text=text or None,
            url=url,
            content_hash=content_hash,
        )
        STORE.upsert(doc)

    key = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if key in _seen_ingest:
        status = "DUPLICATE"
    _seen_ingest.add(key)

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

    tenant_id = payload.get("tenant_id") or "t_default"
    q = payload.get("query") or payload.get("q") or ""
    top_k = int(payload.get("top_k") or 5)

    hits = STORE.search(tenant_id=tenant_id, query=q, top_k=top_k)
    evidence_list = [
        {"evidence_id": e.evidence_id, "source": e.source, "snippet": e.snippet, "score": float(e.score)}
        for e in hits
    ]
    evidence_refs = [e["evidence_id"] for e in evidence_list]

    preferred = {
        "trace_id": trace_id,
        "answer": "Mock answer.",
        "evidence_list": evidence_list,
        "recommendation_card": {
            "risk_level": "MEDIUM",
            "summary": "Mock recommendation.",
            "actions": ["action_1"],
            "evidence_refs": evidence_refs,
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
        "used_evidence_ids": ["ev_001"],
        "results_by_source": {"internal.docs": ["ev_001"]},
    }
    resp = _make_valid("fusion/FusionResult.v1.json", preferred)
    return JSONResponse(status_code=200, content=resp)
""",
    encoding="utf-8",
)

print("OK: wrote app/store/memory.py and app/main.py")
PY

./scripts/preflight.sh

echo "NEXT:"
echo "git add app/main.py app/store/memory.py scripts/week4_day3.sh"
echo "git commit -m \"feat(store): wire ingest/query to in-memory retrieval\""
echo "git push"
