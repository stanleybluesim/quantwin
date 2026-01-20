from __future__ import annotations

import uuid
from typing import Any, Optional, Dict

from fastapi import Request
from fastapi.responses import JSONResponse

from app.schema_validator import validate_or_raise


def _trace_id(request: Optional[Request]) -> str:
    if request is not None:
        tid = request.headers.get("x-trace-id") or request.headers.get("x-request-id")
        if tid:
            return tid
    return uuid.uuid4().hex


def build_error_envelope(
    request: Optional[Request],
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    trace_id = _trace_id(request)

    # 默认形状：你如果 ErrorEnvelope schema 字段不同，后面会在校验报错里精确指出
    payload: Dict[str, Any] = {
        "trace_id": trace_id,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details is not None:
        payload["error"]["details"] = details

    # 开发期强约束：确保符合 contracts/schemas/common/ErrorEnvelope.v1.json
    try:
        validate_or_raise("common/ErrorEnvelope.v1.json", payload)
    except Exception as e:
        # 避免错误处理再触发错误导致死循环
        return {"trace_id": trace_id, "detail": f"ErrorEnvelope schema mismatch: {e}"}

    return payload


def error_response(
    request: Optional[Request],
    status_code: int,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=build_error_envelope(request, code=code, message=message, details=details),
    )
