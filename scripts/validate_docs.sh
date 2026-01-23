#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

MAN="docs/specs/manifest.md"
RS="docs/specs/RS_v3.1.pdf"
AS="docs/specs/AS_v5.0-7.1.pdf"

echo "==> validate docs"
test -f "$MAN"
test -f "$RS"
test -f "$AS"

python3 - <<'PY'
from pathlib import Path
import hashlib, os, re, sys

man = Path("docs/specs/manifest.md")
rs = Path("docs/specs/RS_v3.1.pdf")
as_ = Path("docs/specs/AS_v5.0-7.1.pdf")

text = man.read_text(encoding="utf-8")

rows = []
for ln in text.splitlines():
  if not ln.startswith("|"):
    continue
  if re.match(r"^\|\s*-+\s*\|", ln):
    continue
  cols = [c.strip() for c in ln.strip().strip("|").split("|")]
  if len(cols) != 4:
    continue
  if cols[0].lower() == "spec":
    continue
  rows.append(cols)

if not rows:
  print("FAIL: manifest.md has no parsable rows")
  sys.exit(2)

def sha256(p: Path) -> str:
  h = hashlib.sha256()
  h.update(p.read_bytes())
  return h.hexdigest()

expected = {
  str(rs): (os.path.getsize(rs), sha256(rs)),
  str(as_): (os.path.getsize(as_), sha256(as_)),
}

seen = {}
for spec, path, size_s, sha_s in rows:
  path = path.strip("`")
  sha_s = sha_s.strip("`")
  try:
    size_i = int(size_s)
  except:
    continue
  seen[path] = (size_i, sha_s)

missing = [p for p in expected.keys() if p not in seen]
if missing:
  print("FAIL: manifest missing rows for:", missing)
  sys.exit(2)

for p, (size_e, sha_e) in expected.items():
  size_g, sha_g = seen[p]
  if size_g != size_e or sha_g != sha_e:
    print("FAIL: manifest mismatch:", p)
    print("  expected:", size_e, sha_e)
    print("  got     :", size_g, sha_g)
    sys.exit(2)

print("OK: manifest files exist + sha256/size match")
PY

echo "OK: docs validate"
