from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Protocol, Dict


@dataclass(frozen=True)
class Document:
    doc_id: str
    tenant_id: str
    source_id: str
    received_at: str
    mime_type: str
    text: Optional[str] = None
    url: Optional[str] = None
    content_hash: Optional[str] = None


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source: str
    snippet: str
    score: float
    doc_id: str


class DocStore(Protocol):
    def find_by_idempotency(self, tenant_id: str, source_id: str, content_hash: str) -> Optional[str]:
        ...

    def upsert(self, doc: Document) -> str:
        ...

    def get(self, doc_id: str) -> Optional[Document]:
        ...

    def search(self, tenant_id: str, query: str, top_k: int) -> List[Evidence]:
        ...
