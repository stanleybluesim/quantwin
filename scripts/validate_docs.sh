#!/usr/bin/env bash
set -euo pipefail

echo "==> validate docs"
test -f docs/specs/RS_v3.1.pdf
test -f docs/specs/AS_v5.0-7.1.pdf
test -f docs/specs/manifest.md
test -f docs/specs/SpecIndex.md

python3 - <<'PY'
from pathlib import Path
import hashlib, os, re

manifest = Path("docs/specs/manifest.md").read_text(encoding="utf-8").splitlines()

# parse markdown table rows
rows = []
for ln in manifest:
    if ln.startswith("|") and "`docs/specs/" in ln:
        cols = [c.strip() for c in ln.strip("|").split("|")]
        if len(cols) >= 4:
            spec, path, size, sha = cols[0], cols[1], cols[2], cols[3]
            path = path.strip("`")
            sha = sha.strip("`")
            try:
                size = int(size)
            except Exception:
                continue
            rows.append((spec, path, size, sha))

if len(rows) < 2:
    raise SystemExit("FAIL: manifest.md has no parsable rows")

def sha256(p: str) -> str:
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest()

for spec, path, size, sha in rows:
    if not Path(path).exists():
        raise SystemExit(f"FAIL: missing file referenced in manifest: {path}")
    real_size = os.path.getsize(path)
    real_sha = sha256(path)
    if real_size != size:
        raise SystemExit(f"FAIL: size mismatch for {path}: manifest={size} real={real_size}")
    if real_sha != sha:
        raise SystemExit(f"FAIL: sha mismatch for {path}: manifest={sha} real={real_sha}")

idx = Path("docs/specs/SpecIndex.md").read_text(encoding="utf-8")
need = ["docs/specs/RS_v3.1.pdf", "docs/specs/AS_v5.0-7.1.pdf", "docs/specs/manifest.md"]
missing = [x for x in need if x not in idx]
if missing:
    raise SystemExit("FAIL: SpecIndex missing references: " + ", ".join(missing))

print("OK: manifest files exist + sha256/size match")
print("OK: SpecIndex references baseline specs")
print("OK: docs validate")
PY
