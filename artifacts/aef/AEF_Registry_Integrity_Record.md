# AEF_Registry_Integrity_Record

## 1. Formal Object
- task_id: WP-P1-3
- task_name: 回归护栏与 TTL / registry integrity 固化
- owner: DEV / QA / SRE
- accountable_owner: SRE
- scope_layer: AEF_ENGINEERING_GOV
- formal_output: true

## 2. C-7 Anchor
- trace_id: REQUIRED_AT_EXECUTION
- run_id: REQUIRED_AT_EXECUTION
- audit_id: REQUIRED_AT_EXECUTION
- report_id: N/A
- non_report_chain_real_report_id = FAIL

## 3. Input Binding
- registry_root: tests/regressions
- ttl_policy: config/aef/ttl_policy.yaml
- registry_index_mode: document_contract_only
- source_of_truth: aef-config
- runtime_policy_source: NOT_APPLICABLE

## 4. Integrity Checklist
- README_present: PASS_PENDING_EXECUTION
- ttl_policy_present: PASS_PENDING_EXECUTION
- duplicate_case_id_check: PASS_PENDING_EXECUTION
- required_c7_fields_declared: PASS_PENDING_EXECUTION
- non_report_chain_report_id_rule: PASS_PENDING_EXECUTION
- registry_integrity_rule_declared: PASS_PENDING_EXECUTION

## 5. Boundary
- AEF = 工程治理层
- QuantWin = 业务运行层
- FastStream = 唯一异步通信层
- 所有异步消息 MUST 通过已登记 Topic
- 所有异步消息 MUST 携带 idempotency_key
- 工件变更与运行时发布动作 MUST 分离
- AEF MUST NOT 直接修改线上当前生效状态
- 本记录不表示运行时当前生效状态已切换

## 6. TTL / Registry Rule
- ttl_days default = 90
- ttl source MUST be config/aef/ttl_policy.yaml
- duplicate case_id = FAIL
- missing ttl_days = FAIL
- missing trace_id / run_id / audit_id = FAIL
- non-report chain real report_id = FAIL

## 7. Error Codes
- AEF-RG-001 MissingRegressionReadme
- AEF-RG-002 MissingRequiredCaseField
- AEF-RG-003 DuplicateCaseId
- AEF-RG-004 InvalidTTLValue
- AEF-RG-005 RegistryIntegrityViolation
- AEF-RG-006 MissingC7Fields
- AEF-RG-007 RuntimeBoundaryViolation

## 8. AS Mapping
- Traceability Matrix: WP-P1-3 -> FF-AEF-RG-001/002/003
- Metric Specifications: formal_artifact_presence / c7_anchor_presence
- Test Specifications & Gates: TC-BL-P1-003 / BL-GATE-009
- Coverage Matrix: README / TTL policy / Integrity record
- Merge Ledger: pending after git landing

## 9. Non-Extrapolation
- NOT formal acceptance complete
- NOT runtime publish complete
- NOT runtime live-state switch asserted
- NOT auto-release complete
- NOT auto-go-live complete
