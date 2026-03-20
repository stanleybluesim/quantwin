# OpenClaw Auditor / complex_reasoning Routing Formalization — Traceability

Status: READY_FOR_COMMIT
Topic: OpenClaw Auditor / complex_reasoning routing formalization
Scope: topic-level traceability artifact only

## 1. Baseline Status
- 本专题已完成工程收口。
- 当前不能上推为“正式验收完成”。
- 本文件为专题级 Traceability 落库工件，不代表运行时已生效。

## 2. Proposed Traceability Labels
以下标签为本轮拟采用命名，仅作为待落库对象，不视为“项目内已正式注册事实”。

### 2.1 Proposed Requirement Labels
- PROPOSED-REQ-OCLAW-AUDITOR-001
  - Auditor / complex_reasoning formalization 只允许作用于工程治理层工件。
- PROPOSED-REQ-OCLAW-AUDITOR-002
  - 当前默认主基线保持不变；qwen-portal 继续承担 bootstrap 基线。
- PROPOSED-REQ-OCLAW-AUDITOR-003
  - 不切 primary model。
- PROPOSED-REQ-OCLAW-AUDITOR-004
  - 不把 DeepSeek 直接接入 QuantWin 真实开发任务。
- PROPOSED-REQ-OCLAW-AUDITOR-005
  - 相关工件必须挂接 C-7 字段：trace_id / run_id / audit_id / report_id。
- PROPOSED-REQ-OCLAW-AUDITOR-006
  - 异步边界必须对齐 FastStream / Topic / idempotency_key。
- PROPOSED-REQ-OCLAW-AUDITOR-007
  - 出站边界必须对齐 egress_mode=offline|allowlist。
- PROPOSED-REQ-OCLAW-AUDITOR-008
  - 工件变更与运行时当前生效状态变更必须分离。

### 2.2 Proposed Test Labels
- PROPOSED-TC-OCLAW-AUDITOR-001
  - 工程收口证据复核：PR #28 已 merged；checks 全部通过；main 已对齐；分支已清理。
- PROPOSED-TC-OCLAW-AUDITOR-002
  - schema/sample 覆盖复核：两份 policy 文件与两份 artifacts 文件均已具备正式章节结构。
- PROPOSED-TC-OCLAW-AUDITOR-003
  - C-7 字段覆盖复核：trace_id / run_id / audit_id / report_id 已在 policy 与本专题工件中明示。
- PROPOSED-TC-OCLAW-AUDITOR-004
  - FastStream / Topic / idempotency_key 覆盖复核。
- PROPOSED-TC-OCLAW-AUDITOR-005
  - egress_mode=offline|allowlist 覆盖复核。
- PROPOSED-TC-OCLAW-AUDITOR-006
  - runtime-boundary 复核：未修改线上当前生效状态；未执行 publish / rollback。

## 3. File Mapping
- docs/process/OpenClawAuditorRoutingPolicy.md
  - 对应：
    - PROPOSED-REQ-OCLAW-AUDITOR-001
    - PROPOSED-REQ-OCLAW-AUDITOR-002
    - PROPOSED-REQ-OCLAW-AUDITOR-003
    - PROPOSED-REQ-OCLAW-AUDITOR-004
    - PROPOSED-REQ-OCLAW-AUDITOR-005
- docs/process/ModelRoutingPolicy.md
  - 对应：
    - 默认路由基线
    - timeout / retry
    - fallback / circuit breaker 基线
- artifacts/openclaw/OpenClaw_Auditor_Routing_Acceptance.md
  - 对应：
    - PROPOSED-TC-OCLAW-AUDITOR-001..006
- artifacts/openclaw/OpenClaw_Auditor_Routing_Traceability.md
  - 对应：
    - REQ / TC / 文件 / 边界映射落库

## 4. Mapping to AS Structures

### 4.1 Traceability Matrix
本文件承担以下映射：
- Proposed Requirement Label -> 文件
- Proposed Test Label -> 证据对象
- PR / Branch Closure Evidence -> topic-level validation artifact

### 4.2 Test Specifications & Gates
本文件将以下验证对象映射到专题级门禁语义：
- 工程收口证据
- schema/sample 覆盖
- C-7 覆盖
- FastStream / Topic / idempotency_key 覆盖
- egress_mode=offline|allowlist 覆盖
- runtime-boundary 覆盖

### 4.3 Metric Specifications
- 本专题为 docs/sample formalization 子专题。
- 本专题未生成运行时数值指标。
- 因此 Metric Specifications 的映射方式为：
  - 记录“本专题无新增 runtime metric”
  - 记录“不得把无数值指标误写成已完成运行时指标验收”

## 5. Boundary Mapping
- C-7
  - trace_id / run_id / audit_id / report_id
- Async Boundary
  - FastStream
  - Topic
  - idempotency_key
- Egress Boundary
  - egress_mode=offline
  - egress_mode=allowlist
- Runtime Boundary
  - 工件变更与运行时生效分离
  - 不直接修改线上当前生效策略状态

## 6. Merge Gate Statement
- 本文件与 Acceptance 工件均合并入 main 前：
  - 不得写“专题正式验收完成”
  - 不得写“Traceability 已正式注册”
- 仅当本文件与 Acceptance 工件完成落库，且相关 PR checks 全部通过并完成合并后，方可关闭：
  - GAP-OCLAW-AUDITOR-ACCEPTANCE-001
  - GAP-OCLAW-AUDITOR-TRACEABILITY-ARTIFACT-001
