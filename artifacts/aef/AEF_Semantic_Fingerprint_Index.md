# AEF_Semantic_Fingerprint_Index

## Metadata
- artifact_id: FF-AEF-FB-003
- task_id: WP-P1-1
- owner: AR / DEV / QA
- accountable_owner: QA
- scope_layer: AEF_ENGINEERING_GOV
- trace_id: TBD-BY-RUN
- audit_id: TBD-BY-RUN
- run_id: TBD-BY-RUN
- report_id: N/A

## Fingerprint Definition
- hash_name: Semantic Signature Hash
- normalization = required
- normalization_runtime = Docker_or_CLI_single_source
- tree-sitter = enabled
- tool_ref = quantwin-fingerprint-cli

## Rules
- remove_comments = true
- normalize_indent = true
- normalize_literals = placeholder
- normalize_identifiers = placeholder
- function_signature = required
- Local / CI / Agent MUST share the same Docker or CLI implementation
- MUST NOT maintain divergent hash logic

## Archive
- archive_path = artifacts/aef/
- index_key = fingerprint_hash
- collision_policy = manual-review-required
