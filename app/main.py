import os
import json
import hashlib
import uuid
from pathlib import Path
from typing import Any, Dict, Tuple

from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse

from app.schema_validator import validate_or_raise

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts" / "schemas"

app = FastAPI(title="QuantWin Mock API", version="0.1.0")

# ----------------------------
# Schema helpers (minimal generator + merge)
# ----------------------------
_schema_cache: Dict[str, Any] = {}

def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def _load_schema(rel: str) -> Any:
    if rel not in _schema_cache:
        _schema_cache[rel] = _load_json(SCHEMA_DIR / rel)
    return _schema_cache[rel]

def _json_pointer(doc: Any, ptr: str) -> Any:
    # ptr like "#/properties/error"
    if not ptr.startswith("#/"):
        return doc
    cur = doc
    for part in ptr[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        cur = cur[part]
    return cur

def _resolve_ref(base_rel: str, ref: str) -> Tuple[Any, str]:
    # returns (schema_node, relpath_of_schema_file)
    if ref.startswith("#/"):
        base = _load_schema(base_rel)
        return _json_pointer(base, ref), base_rel
    if "#" in ref:
        file_part, ptr = ref.split("#", 1)
        ptr = "#" + ptr
    else:
        file_part, ptr = ref, ""
    base_path = (SCHEMA_DIR / base_rel).parent
    target_rel = str((base_path / file_part).resolve().relative_to(SCHEMA_DIR.resolve()))
    target_schema = _load_schema(target_rel)
    if ptr:
        return _json_pointer(target_schema, ptr), target_rel
    return target_schema, target_rel

def _merge(a: Any, b: Any) -> Any:
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = _merge(out.get(k), v) if k in out else v
        return out
    return b if b is not None else a

def _minimal_instance(schema: Any, base_rel: str) -> Any:
    if not isinstance(schema, dict):
        return None

    if "$ref" in schema:
        node, rel = _resolve_ref(base_rel, schema["$ref"])
        return _minimal_instance(node, rel)

    # choose first option
    for key in ("oneOf", "anyOf"):
        if key in schema and isinstance(schema[key], list) and schema[key]:
            return _minimal_instance(schema[key][0], base_rel)

    if "allOf" in schema and isinstance(schema["allOf"], list) and schema["allOf"]:
        inst = {}
        for sub in schema["allOf"]:
            inst = _merge(inst, _minimal_instance(sub, base_rel))
        return inst

    if "const" in schema:
        return schema["const"]

    if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
        return schema["enum"][0]

    t = schema.get("type")
    if isinstance(t, list):
        t = t[0] if t else None

    if t == "object" or ("properties" in schema):
        props = schema.get("properties", {}) or {}
        req = schema.get("required", []) or []
        obj = {}
        for k in req:
            if k in props:
                obj[k] = _minimal_instance(props[k], base_rel)
            else:
                obj[k] = "x"
        return obj

    if t == "array":
        item_schema = schema.get("items", {}) or {}
        return [_minimal_instance(item_schema, base_rel)]

    if t == "string":
        return "x"
    if t == "integer":
        return 0
    if t == "number":
        return 0
    if t == "boolean":
        return True

    return None

def _make_valid(rel_schema: str, preferred: Dict[str, Any]) -> Dict[str, Any]:
    # Try preferred first; if fails, generate minimal instance then overlay preferred.
    try:
        validate_or_raise(rel_schema, preferred)
        return preferred
    except Exception:
        base = _minimal_instance(_load_schema(rel_schema), rel_schema)
        if not isinstance(base, dict):
            base = {}
        merged = _merge(base, preferred)
        validate_or_raise(rel_schema, merged)
        return merged

def _new_trace(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"

# ----------------------------
# Auth + error envelope
# ----------------------------
def _get_token() -> str:
    return os.getenv("QW_API_TOKEN", "dev-token")

def _authorized(request: Request) -> bool:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    return auth.split(" ", 1)[1].strip() == _get_token()

def _error_envelope(status_code: int, code: str, message: str, trace_id: str, details: Dict[str, Any] | None = None):
    details = details or {}
    # try common shapes until one validates
    candidates = [
        {"trace_id": trace_id, "error": {"code": code, "message": message, "details": details}},
        {"trace_id": trace_id, "error": {"error_code": code, "message": message, "details": details}},
        {"trace_id": trace_id, "code": code, "message": message, "details": details},
        {"trace_id": trace_id, "error_code": code, "message": message, "details": details},
    ]
    for c in candidates:
        try:
            payload = _make_valid("common/ErrorEnvelope.v1.json", c)
            return JSONResponse(status_code=status_code, content=payload)
        except Exception:
            continue
    # last resort (tests will likely fail if schema is very different)
    return JSONResponse(status_code=status_code, content={"trace_id": trace_id, "error": {"code": code, "message": message}})

@app.exception_handler(Exception)
async def _unhandled_exc_handler(request: Request, exc: Exception):
    trace_id = _new_trace("tr_err")
    return _error_envelope(500, "INTERNAL_ERROR", str(exc), trace_id)

# ----------------------------
# Endpoints
# ----------------------------
_seen_ingest: set[str] = set()

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/v1/ingest")
async def ingest(request: Request, payload: Dict[str, Any] = Body(...)):
    trace_id = _new_trace("tr_ingest")
    if not _authorized(request):
        return _error_envelope(401, "UNAUTHORIZED", "missing or invalid bearer token", trace_id)

    try:
        validate_or_raise("ingest/IngestRequest.v1.json", payload)
    except Exception as e:
        return _error_envelope(400, "BAD_REQUEST", "request schema validation failed", trace_id, {"reason": str(e)})

    key = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    status = "DUPLICATE" if key in _seen_ingest else "ACCEPTED"
    _seen_ingest.add(key)

    doc_id = payload.get("doc_id") or payload.get("document_id") or "doc_001"
    resp = _make_valid("ingest/IngestAck.v1.json", {"trace_id": trace_id, "doc_id": doc_id, "status": status})
    return JSONResponse(status_code=200, content=resp)

@app.post("/v1/query")
async def query(request: Request, payload: Dict[str, Any] = Body(...)):
    trace_id = _new_trace("tr_query")
    if not _authorized(request):
        return _error_envelope(401, "UNAUTHORIZED", "missing or invalid bearer token", trace_id)

    try:
        validate_or_raise("query/QueryRequest.v1.json", payload)
    except Exception as e:
        return _error_envelope(400, "BAD_REQUEST", "request schema validation failed", trace_id, {"reason": str(e)})

    preferred = {
        "trace_id": trace_id,
        "answer": "Mock answer.",
        "evidence_list": [
            {"evidence_id": "ev_001", "source": "internal.docs", "snippet": "A", "score": 0.8},
            {"evidence_id": "ev_002", "source": "internal.runbook", "snippet": "B", "score": 0.7},
        ],
        "recommendation_card": {
            "risk_level": "MEDIUM",
            "summary": "Mock recommendation.",
            "actions": ["action_1"],
            "evidence_refs": ["ev_001", "ev_002"],
        },
    }
    resp = _make_valid("query/QueryResponse.v1.json", preferred)
    return JSONResponse(status_code=200, content=resp)

@app.post("/v1/fuse")
async def fuse(request: Request, payload: Dict[str, Any] = Body(...)):
    trace_id = _new_trace("tr_fuse")
    if not _authorized(request):
        return _error_envelope(401, "UNAUTHORIZED", "missing or invalid bearer token", trace_id)

    try:
        validate_or_raise("fusion/FusionRequest.v1.json", payload)
    except Exception as e:
        return _error_envelope(400, "BAD_REQUEST", "request schema validation failed", trace_id, {"reason": str(e)})

    preferred = {
        "trace_id": trace_id,
        "fused_summary": "Mock fused summary.",
        "used_evidence_ids": ["ev_001", "ev_002"],
        "results_by_source": {"internal.docs": ["ev_001"], "internal.runbook": ["ev_002"]},
    }
    resp = _make_valid("fusion/FusionResult.v1.json", preferred)
    return JSONResponse(status_code=200, content=resp)
