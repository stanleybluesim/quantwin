from __future__ import annotations

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
        terms = [t for t in q.replace("\n", " ").split(" ") if t]
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
