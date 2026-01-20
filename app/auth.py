from __future__ import annotations

import os
from fastapi import Request

DEFAULT_TOKEN = "devtoken"
ENV_TOKEN_KEY = "QW_API_TOKEN"

PUBLIC_PATH_PREFIXES = (
    "/healthz",
    "/docs",
    "/openapi.json",
    "/redoc",
)

PROTECTED_PREFIXES = ("/v1/",)


def expected_token() -> str:
    return os.getenv(ENV_TOKEN_KEY, DEFAULT_TOKEN)


def is_public(request: Request) -> bool:
    p = request.url.path
    return any(p.startswith(x) for x in PUBLIC_PATH_PREFIXES)


def is_protected(request: Request) -> bool:
    p = request.url.path
    return any(p.startswith(x) for x in PROTECTED_PREFIXES)


def valid_bearer(request: Request) -> bool:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth.removeprefix("Bearer ").strip()
    return token == expected_token()
