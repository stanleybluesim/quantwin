#!/usr/bin/env bash
set -euo pipefail

F1="artifacts/aef/AEF_Log_Adapter_Record.md"
F2="artifacts/aef/AEF_EFR_Record.md"
F3="artifacts/aef/AEF_Semantic_Fingerprint_Index.md"
FILES=("$F1" "$F2" "$F3")

say() { printf "\n==> %s\n" "$*"; }
die() { printf "\nFAIL: %s\n" "$*" >&2; exit 1; }
need_file() { [[ -f "$1" ]] || die "missing file: $1"; }
must_grep_file() {
  local pattern="$1"
  local file="$2"
  local label="$3"
  grep -nE "$pattern" "$file" >/dev/null || die "$label missing in $file"
}
must_grep_any() {
  local pattern="$1"
  local label="$2"
  grep -nE "$pattern" "${FILES[@]}" >/dev/null || die "$label missing in target artifacts"
}
must_not_grep_any() {
  local pattern="$1"
  local label="$2"
  if grep -nE "$pattern" "${FILES[@]}" >/dev/null; then
    die "$label detected"
  fi
}

say "1. 文件存在"
for f in "${FILES[@]}"; do
  need_file "$f"
  ls "$f"
done

say "2. Gate 4 / EFR / 指纹规则"
must_grep_file 'Layer 1|Adapter Registry' "$F1" 'Layer 1 marker'
must_grep_file 'Layer 3|LLM Summarizer' "$F1" 'Layer 3 marker'
must_grep_file 'Layer 4|Raw Context' "$F1" 'Layer 4 marker'

must_grep_file 'Layer 2|Error Fingerprint Registry|EFR' "$F2" 'Layer 2/EFR marker'
must_grep_file 'Few-Shot|few_shot|injection_mode' "$F2" 'EFR injection marker'
must_grep_file '0\.80|80%' "$F2" 'Contextual Delta threshold marker'

must_grep_file 'Semantic Signature Hash' "$F3" 'semantic signature marker'
must_grep_file 'tree-sitter' "$F3" 'tree-sitter marker'
must_grep_file 'Docker|CLI' "$F3" 'single runtime marker'
must_grep_file 'normalization|normalize' "$F3" 'normalization marker'

say "3. C-7 最小追溯字段"
for f in "${FILES[@]}"; do
  must_grep_file 'trace_id' "$f" 'trace_id'
  must_grep_file 'audit_id' "$f" 'audit_id'
  must_grep_file 'run_id' "$f" 'run_id'
done

say "4. 边界约束"
must_grep_any 'AEF = 工程治理层|AEF.*工程治理层' 'AEF engineering-governance boundary'
must_grep_any 'QuantWin = 业务运行层|QuantWin.*业务运行层' 'QuantWin runtime boundary'
must_grep_any 'FastStream' 'FastStream boundary'
must_grep_any 'Topic' 'Topic boundary'
must_grep_any 'idempotency_key' 'idempotency_key boundary'
must_grep_any 'offline-first|egress_mode=offline|egress_mode = offline' 'offline boundary'
must_grep_any 'egress_mode=allowlist|egress_mode = allowlist|allowlist' 'allowlist boundary'

say "5. 禁止外推 / 禁止运行时发布越界"
must_not_grep_any '已上线|已生效|运行时已切换|自治闭环已达成' 'overclaim wording'
must_not_grep_any 'POST /v1/policy/publish|POST /v1/policy/rollback' 'runtime publish endpoint reference'

say "PASS: WP-P1-1 acceptance checks passed"
