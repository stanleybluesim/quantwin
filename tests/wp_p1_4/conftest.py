from __future__ import annotations

import pytest
from pathlib import Path

def pytest_collect_file(parent, file_path: Path):
    if file_path.name == "idempotency_test_suite.py":
        return pytest.Module.from_parent(parent, path=file_path)
    return None
