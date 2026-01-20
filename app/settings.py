from __future__ import annotations

import os

QW_STORE = os.getenv("QW_STORE", "memory").strip().lower()
