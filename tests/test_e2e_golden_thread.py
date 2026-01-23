import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INGEST_EX = ROOT / "contracts" / "examples" / "ingest" / "IngestRequest.example.json"
QUERY_EX  = ROOT / "contracts" / "examples" / "query"  / "QueryRequest.example.json"

# Base candidate keys (keep)
TOKEN_ENV_KEYS: List[str] = [
    "QW_TEST_BEARER_TOKEN",
    "BEARER_TOKEN",
    "API_BEARER_TOKEN",
    "AUTH_BEARER_TOKEN",
    "QW_BEARER_TOKEN",
]

def _read_base_token() -> str:
    p = ROOT / "tests" / "test_smoke.py"
    if p.exists():
        m = re.search(r'(?m)^\s*BASE_TOKEN\s*=\s*[\'"]([^\'"]+)[\'"]\s*$', p.read_text(encoding="utf-8"))
        if m:
            return m.group(1).strip()
    for k in TOKEN_ENV_KEYS:
        v = os.getenv(k, "").strip()
        if v:
            return v
    return ""

def _extract_token_like_env_keys_from_smoke() -> List[str]:
    """
    从 tests/test_smoke.py 中抓取所有 env key（os.environ[...] / env[...] / environ.get(...) / getenv(...)）
    然后仅保留“像 token 的 key”：包含 TOKEN/BEARER/AUTH/KEY/API（不区分大小写）
    """
    p = ROOT / "tests" / "test_smoke.py"
    if not p.exists():
        return []
    s = p.read_text(encoding="utf-8")

    keys = set()

    # os.environ["X"] / os.environ.get("X") / os.getenv("X")
    keys.update(re.findall(r'os\.environ\[\s*[\'"]([^\'"]+)[\'"]\s*\]', s))
    keys.update(re.findall(r'os\.environ\.get\(\s*[\'"]([^\'"]+)[\'"]', s))
    keys.update(re.findall(r'os\.getenv\(\s*[\'"]([^\'"]+)[\'"]', s))

    # env["X"] / env.get("X")  (常见于 subprocess env dict)
    keys.update(re.findall(r'\benv\[\s*[\'"]([^\'"]+)[\'"]\s*\]', s))
    keys.update(re.findall(r'\benv\.get\(\s*[\'"]([^\'"]+)[\'"]', s))

    keep = []
    for k in sorted(keys):
        u = k.upper()
        if ("TOKEN" in u) or ("BEARER" in u) or ("AUTH" in u) or ("API" in u) or (u.endswith("KEY")) or ("_KEY" in u):
            keep.append(k)
    return keep

BASE_TOKEN = _read_base_token()
if not BASE_TOKEN:
    raise RuntimeError("No bearer token available. Expected tests/test_smoke.py BASE_TOKEN or token env vars.")

# Critical: align ALL discovered token-like env keys BEFORE importing app
extra_keys = _extract_token_like_env_keys_from_smoke()
ALL_KEYS = list(dict.fromkeys(TOKEN_ENV_KEYS + extra_keys))  # stable dedupe

for k in ALL_KEYS:
    os.environ[k] = BASE_TOKEN

from fastapi.testclient import TestClient
from app.main import app  # type: ignore


def _load(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _auth_headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {BASE_TOKEN}", "Content-Type": "application/json"}


@pytest.mark.e2e
def test_golden_thread_ingest_then_query_evidence_list_non_empty():
    if not INGEST_EX.exists():
        pytest.fail(f"missing example: {INGEST_EX}")
    if not QUERY_EX.exists():
        pytest.fail(f"missing example: {QUERY_EX}")

    client = TestClient(app)

    ingest_payload = _load(INGEST_EX)
    query_payload = _load(QUERY_EX)

    r1 = client.post("/v1/ingest", headers=_auth_headers(), json=ingest_payload)
    assert r1.status_code < 400, f"ingest failed: {r1.status_code} {r1.text}"

    r2 = client.post("/v1/query", headers=_auth_headers(), json=query_payload)
    assert r2.status_code < 400, f"query failed: {r2.status_code} {r2.text}"

    data = r2.json()
    ev = data.get("evidence_list")
    assert isinstance(ev, list), f"expected evidence_list list, got: {type(ev)} {data}"
    assert len(ev) >= 1, f"expected non-empty evidence_list, got: {data}"
