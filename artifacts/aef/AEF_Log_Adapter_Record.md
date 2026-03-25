# AEF_Log_Adapter_Record

## Metadata
- artifact_id: FF-AEF-FB-001
- task_id: WP-P1-1
- owner: AR / DEV / QA
- accountable_owner: QA
- scope_layer: AEF_ENGINEERING_GOV
- trace_id: TBD-BY-RUN
- audit_id: TBD-BY-RUN
- run_id: TBD-BY-RUN
- report_id: N/A

## Boundary
- AEF = 工程治理层
- QuantWin = 业务运行层
- FastStream = 唯一异步通信层
- Topic = required
- idempotency_key = required
- 工件变更与运行时发布动作 MUST 分离
- egress_mode = offline
- egress_mode = allowlist
- offline-first = true

## Gate 4 Mapping
- Layer 1: Adapter Registry
- Layer 3: LLM Summarizer
- Layer 4: Raw Context

## Contract
- output_format = structured_json | sanitized_text | raw_context
- raw_context_tail_lines = 500
- monitoring.adapter_health_threshold = 50%
- llm_summarizer_async = true
- raw_context_async = false

## Error Codes
- AEF-QW-002 MissingC7Fields
- AEF-QW-004 BoundaryViolation
- AEF-QW-006 EgressPolicyViolation
- AEF-QW-007 DuplicateRuntimeFieldOwner
