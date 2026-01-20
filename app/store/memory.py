from __future__ import annotations

import hashlib
import uuid
from typing import Optional, List, Dict

from app.store.base import Document, Evidence


def _hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class InMemoryDocStore:
    def __init__(self) -> None:
        self._docs: Dict[str, Document] = {}

    def upsert(self, doc: Document) -> str:
        # If doc_id provided, keep; else generate stable-ish id from content
        doc_id = doc.doc_id or f"doc_{uuid.uuid4().hex[:8]}"
        self._docs[doc_id] = Document(
            doc_id=doc_id,
            tenant_id=doc.tenant_id,
            source_id=doc.source_id,
            received_at=doc.received_at,
            mime_type=doc.mime_type,
            text=doc.text,
            url=doc.url,
            content_hash=doc.content_hash,
        )
        return doc_id

    def get(self, doc_id: str) -> Optional[Document]:
        return self._docs.get(doc_id)

    def search(self, tenant_id: str, query: str, top_k: int) -> List[Evidence]:
        # Day 1 placeholder: returns empty. Day 3 will implement real scoring.
        return []
