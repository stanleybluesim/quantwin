from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_BASE = REPO_ROOT / "contracts" / "schemas"

_validator_cache: Dict[str, Draft202012Validator] = {}

def _load_schema(schema_rel_path: str) -> Dict[str, Any]:
    p = SCHEMA_BASE / schema_rel_path
    if not p.exists():
        raise FileNotFoundError(f"Schema not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))

def get_validator(schema_rel_path: str) -> Draft202012Validator:
    if schema_rel_path in _validator_cache:
        return _validator_cache[schema_rel_path]
    schema = _load_schema(schema_rel_path)
    v = Draft202012Validator(schema)
    _validator_cache[schema_rel_path] = v
    return v

def validate_or_raise(schema_rel_path: str, instance: Any) -> None:
    v = get_validator(schema_rel_path)
    errors = sorted(v.iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(x) for x in first.path) if first.path else "(root)"
        raise ValueError(f"{schema_rel_path} invalid at {path}: {first.message}")
