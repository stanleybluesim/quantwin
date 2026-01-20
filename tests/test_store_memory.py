from app.store import get_store
from app.store.base import Document


def test_store_insert_get():
    store = get_store()
    doc_id = store.upsert(
        Document(
            doc_id="doc_test_001",
            tenant_id="t1",
            source_id="s1",
            received_at="2026-01-20T00:00:00Z",
            mime_type="text/plain",
            text="hello",
            url=None,
        )
    )
    assert doc_id == "doc_test_001"
    doc = store.get(doc_id)
    assert doc is not None
    assert doc.doc_id == "doc_test_001"
    assert doc.tenant_id == "t1"
    assert doc.text == "hello"
