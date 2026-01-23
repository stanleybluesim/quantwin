#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

MANIFEST="docs/specs/manifest.md"
SPEC_INDEX="docs/specs/SpecIndex.md"

echo "==> validate docs"

test -f "$MANIFEST" || { echo "FAIL: missing $MANIFEST"; exit 2; }
test -f "$SPEC_INDEX" || { echo "FAIL: missing $SPEC_INDEX"; exit 2; }

python3 - <<'PY'
from pathlib import Path
import hashlib, os, re, sys

manifest = Path("docs/specs/manifest.md").read_text(encoding="utf-8")

# parse markdown table rows: | Spec | `path` | size | `sha` |
rows = []
for line in manifest.splitlines():
    if not line.strip().startswith("|"):
        continue
    if "Spec | Path" in line or re.match(r"^\|\s*---", line):
        continue
    m = re.match(r'^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*([0-9]+)\s*\|\s*`([0-9a-f]{64})`\s*\|', line.strip())
    if m:
        label, path, size_s, sha = m.group(1).strip(), m.group(2).strip(), int(m.group(3)), m.group(4)
        rows.append((label, path, size_s, sha))

if not rows:
    print("FAIL: manifest.md has no parsable rows")
    sys.exit(2)

fail = False
for label, path, size_expected, sha_expected in rows:
    p = Path(path)
    if not p.exists():
        print(f"FAIL: missing file: {path} ({label})")
        fail = True
        continue
    size = os.path.getsize(p)
    if size != size_expected:
        print(f"FAIL: size mismatch for {path}: expected={size_expected} got={size}")
        fail = True
    b = p.read_bytes()
    sha = hashlib.sha256(b).hexdigest()
    if sha != sha_expected:
        print(f"FAIL: sha256 mismatch for {path}: expected={sha_expected} got={sha}")
        fail = True

if fail:
    sys.exit(2)
print("OK: manifest files exist + sha256/size match")
PY

# ensure SpecIndex references the manifest + the pdf files (light guard)
grep -qF "docs/specs/manifest.md" "$SPEC_INDEX" || { echo "FAIL: SpecIndex does not reference manifest.md"; exit 2; }

echo "OK: docs validate"
