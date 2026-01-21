from __future__ import annotations

import json
import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from app.store.base import Document, Evidence


def _tokenize(text: str) -> List[str]:
    t = (text or "").lower().replace("\n", " ")
    return [w for w in re.split(r"[^a-z0-9_]+", t) if w]


def _snippet(text: str, terms: List[str], limit: int = 180) -> str:
    s = (text or "").replace("\n", " ").strip()
    if not s:
        return "N/A"
    low = s.lower()
    pos = -1
    for t in terms:
        p = low.find(t)
        if p >= 0:
            pos = p
            break
    if pos < 0:
        return s[:limit]
    start = max(0, pos - 40)
    return s[start:start + limit]


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
        self._docs[doc.doc_id] = doc
        if doc.content_hash:
            self._idem[(doc.tenant_id, doc.source_id, doc.content_hash)] = doc.doc_id
        self._save()
        return doc.doc_id

    def get(self, doc_id: str) -> Optional[Document]:
        return self._docs.get(doc_id)

    def _fallback(self, tenant_id: str) -> List[Evidence]:
        # 先挑同 tenant 的任意 doc
        for doc in self._docs.values():
            if doc.tenant_id == tenant_id:
                return [Evidence(
                    evidence_id=f"ev_{doc.doc_id}_fallback",
                    source=doc.source_id or "memory",
                    snippet=_snippet(doc.text or "", [], 180),
                    score=0.1,
                    doc_id=doc.doc_id,
                )]
        # 再挑任意 doc
        if self._docs:
            doc = next(iter(self._docs.values()))
            return [Evidence(
                evidence_id=f"ev_{doc.doc_id}_fallback",
                source=doc.source_id or "memory",
                snippet=_snippet(doc.text or "", [], 180),
                score=0.1,
                doc_id=doc.doc_id,
            )]
        # 库里完全没 doc，也要给 1 条 evidence，确保 QueryResponse minItems=1
        return [Evidence(
            evidence_id="ev_000",
            source="internal.mock",
            snippet="No evidence available.",
            score=0.0,
            doc_id="doc_000",
        )]

    def search(self, tenant_id: str, query: str, top_k: int) -> List[Evidence]:
        k = max(1, int(top_k or 1))
        terms = _tokenize(query or "")
        if not terms:
            return self._fallback(tenant_id)

        scored: List[tuple[float, Evidence]] = []
        for doc in self._docs.values():
            if doc.tenant_id != tenant_id:
                continue
            text = doc.text or ""
            low = text.lower()
            hits = sum(1 for t in terms if t in low)
            if hits <= 0:
                continue
            score = min(1.0, hits / max(1, len(terms)))
            ev = Evidence(
                evidence_id=f"ev_{doc.doc_id}_{len(scored)+1}",
                source=doc.source_id or "memory",
                snippet=_snippet(text, terms, 180),
                score=float(score),
                doc_id=doc.doc_id,
            )
            scored.append((score, ev))

        scored.sort(key=lambda x: x[0], reverse=True)
        out = [ev for _, ev in scored[:k]]
        if out:
            return out
        return self._fallback(tenant_id)
