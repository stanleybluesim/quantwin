from __future__ import annotations

from app.settings import QW_STORE
from app.store.base import DocStore
from app.store.memory import InMemoryDocStore

_store: DocStore | None = None


def get_store() -> DocStore:
    global _store
    if _store is not None:
        return _store

    if QW_STORE == "memory":
        _store = InMemoryDocStore()
        return _store

    raise ValueError(f"Unsupported QW_STORE={QW_STORE}")
