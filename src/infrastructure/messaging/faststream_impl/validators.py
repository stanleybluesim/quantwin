from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from .errors import ValidationError

REQUIRED_TRACE_FIELDS = ("trace_id", "run_id", "audit_id")

def load_topic_registry(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _registered_topics(registry: dict[str, Any]) -> set[str]:
    topics = registry.get("topics", [])
    return {
        item["topic"]
        for item in topics
        if item.get("registered") is True and "topic" in item
    }

def validate_message(
    message: dict[str, Any],
    registry: dict[str, Any],
    report_chain: bool = False,
) -> None:
    topic = message.get("topic")
    if not topic or topic not in _registered_topics(registry):
        raise ValidationError("FS-TOPIC-001", "TOPIC_NOT_REGISTERED")

    if not message.get("idempotency_key"):
        raise ValidationError("FS-IDEMP-001", "IDEMPOTENCY_KEY_MISSING")

    for field in REQUIRED_TRACE_FIELDS:
        if not message.get(field):
            raise ValidationError("FS-TRACE-001", "TRACEABILITY_FIELDS_MISSING")

    if message.get("formal_acceptance") != "NOT_ASSERTED":
        raise ValidationError("FS-VAL-001", "CONTRACT_VALIDATION_FAILED")

    if message.get("runtime_publish_state") != "NOT_ASSERTED":
        raise ValidationError("FS-RUNTIME-001", "RUNTIME_PUBLISH_FORBIDDEN_IN_CURRENT_STAGE")

    if message.get("egress_mode") != "offline":
        raise ValidationError("FS-VAL-001", "CONTRACT_VALIDATION_FAILED")

    report_id = message.get("report_id")
    if not report_chain and report_id not in (None, "", "N/A"):
        raise ValidationError("FS-VAL-001", "CONTRACT_VALIDATION_FAILED")
