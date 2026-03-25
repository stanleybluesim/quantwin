# AEF_EFR_Record

## Metadata
- artifact_id: FF-AEF-FB-002
- task_id: WP-P1-1
- owner: AR / DEV / QA
- accountable_owner: QA
- scope_layer: AEF_ENGINEERING_GOV
- trace_id: TBD-BY-RUN
- audit_id: TBD-BY-RUN
- run_id: TBD-BY-RUN
- report_id: N/A

## Gate 4 Mapping
- Layer 2: Error Fingerprint Registry (EFR)

## EFR Record Model
- fingerprint_hash: Semantic Signature Hash
- normalization_tool_ref: single-source-runtime
- function_signature: required
- injection_mode: Few-Shot
- contextual_delta_check_threshold = 0.80
- contextual_delta_check_threshold_percent = 80%
- history_records:
  - outcome: success
    resolution_path: required
  - outcome: failure
    resolution_path: required

## Rules
- MUST query EFR before Worker initialization
- MUST retrieve historical success/failure repair paths
- SHOULD fall back to Layer 3 on hash miss
- SHOULD fall back to Layer 4 on sanitizer miss

## Error Codes
- AEF-QW-002 MissingC7Fields
- AEF-QW-004 BoundaryViolation
