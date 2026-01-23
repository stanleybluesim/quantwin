#!/usr/bin/env bash
set -euo pipefail

echo "==> validate docs"

test -f docs/specs/RS_v3.1.pdf
test -f docs/specs/AS_v5.0-7.1.pdf
test -f docs/specs/manifest.md
test -f docs/specs/SpecIndex.md

python3 - <<'PY'
from pathlib import Path
import hashlib, os, re, sys

manifest = Path("docs/specs/manifest.md").read_text(encoding="utf-8").splitlines()

rows = []
for ln in manifest:
  if not ln.startswith("|"):
    continue
  # skip header separators
  if re.match(r"^\|\s*---", ln):
    continue
  cols = [c.strip() for c in ln.strip().strip("|").split("|")]
  if len(cols) != 4:
    continue
  spec, path, size, sha = cols
  if spec.lower() == "spec" or spec.startswith("#"):
    continue
  # strip backticks
  path = path.strip("`")
  sha = sha.strip("`")
  try:
    size_i = int(size)
  except:
    continue
  rows.append((spec, path, size_i, sha))

if len(rows) < 2:
  raise SystemExit("FAIL: manifest.md has no parsable rows")

def sha256(p: Path) -> str:
  h = hashlib.sha256()
  h.update(p.read_bytes())
  return h.hexdigest()

for _, fp, size, sha in rows:
  p = Path(fp)
  if not p.exists():
    raise SystemExit(f"FAIL: manifest references missing file: {fp}")
  real_size = os.path.getsize(fp)
  real_sha = sha256(p)
  if real_size != size:
    raise SystemExit(f"FAIL: size mismatch: {fp} manifest={size} real={real_size}")
  if real_sha != sha:
    raise SystemExit(f"FAIL: sha mismatch: {fp} manifest={sha} real={real_sha}")

print("OK: manifest files exist + sha256/size match")
PY

# SpecIndex references
grep -qF "docs/specs/RS_v3.1.pdf" docs/specs/SpecIndex.md
grep -qF "docs/specs/AS_v5.0-7.1.pdf" docs/specs/SpecIndex.md
grep -qF "docs/specs/manifest.md" docs/specs/SpecIndex.md
echo "OK: SpecIndex references baseline specs"

echo "OK: docs validate"
