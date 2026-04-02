from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.messaging.faststream_impl import (
    InMemoryIdempotencyStore,
    ValidationError,
    load_topic_registry,
    validate_message,
)

REGISTRY_PATH = ROOT / "contracts" / "faststream" / "topic_registry.yaml"

def base_message() -> dict:
    return {
        "topic": "dev.quantwin.faststream.idempotency_check",
        "idempotency_key": "idem-001",
        "trace_id": "trace-001",
        "run_id": "run-001",
        "audit_id": "audit-001",
        "report_id": "N/A",
        "formal_acceptance": "NOT_ASSERTED",
        "runtime_publish_state": "NOT_ASSERTED",
        "egress_mode": "offline",
    }

def test_registered_topic_passes() -> None:
    registry = load_topic_registry(REGISTRY_PATH)
    validate_message(base_message(), registry)

def test_missing_topic_fails() -> None:
    registry = load_topic_registry(REGISTRY_PATH)
    msg = base_message()
    msg["topic"] = "dev.quantwin.faststream.unknown"
    try:
        validate_message(msg, registry)
        assert False, "expected ValidationError"
    except ValidationError as e:
        assert e.code == "FS-TOPIC-001"

def test_missing_idempotency_key_fails() -> None:
    registry = load_topic_registry(REGISTRY_PATH)
    msg = base_message()
    msg["idempotency_key"] = ""
    try:
        validate_message(msg, registry)
        assert False, "expected ValidationError"
    except ValidationError as e:
        assert e.code == "FS-IDEMP-001"

def test_missing_traceability_field_fails() -> None:
    registry = load_topic_registry(REGISTRY_PATH)
    msg = base_message()
    msg["trace_id"] = ""
    try:
        validate_message(msg, registry)
        assert False, "expected ValidationError"
    except ValidationError as e:
        assert e.code == "FS-TRACE-001"

def test_duplicate_detection() -> None:
    store = InMemoryIdempotencyStore()
    assert store.mark_seen("dev.quantwin.faststream.idempotency_check", "idem-001") is True
    assert store.mark_seen("dev.quantwin.faststream.idempotency_check", "idem-001") is False

def test_non_report_chain_report_id_forbidden() -> None:
    registry = load_topic_registry(REGISTRY_PATH)
    msg = base_message()
    msg["report_id"] = "report-001"
    try:
        validate_message(msg, registry, report_chain=False)
        assert False, "expected ValidationError"
    except ValidationError as e:
        assert e.code == "FS-VAL-001"
