from __future__ import annotations

from typing import Optional, List, Dict, Tuple

from app.store.base import Document, Evidence


class InMemoryDocStore:
    def __init__(self) -> None:
        self._docs: Dict[str, Document] = {}
        self._idem: Dict[Tuple[str, str, str], str] = {}  # (tenant_id, source_id, content_hash) -> doc_id

    def find_by_idempotency(self, tenant_id: str, source_id: str, content_hash: str) -> Optional[str]:
        return self._idem.get((tenant_id, source_id, content_hash))

    def upsert(self, doc: Document) -> str:
        doc_id = doc.doc_id
        self._docs[doc_id] = doc
        if doc.content_hash:
            self._idem[(doc.tenant_id, doc.source_id, doc.content_hash)] = doc_id
        return doc_id

    def get(self, doc_id: str) -> Optional[Document]:
        return self._docs.get(doc_id)

    def search(self, tenant_id: str, query: str, top_k: int) -> List[Evidence]:
        # Day 3 实现检索打分。Day 1-2 先占位。
        return []
